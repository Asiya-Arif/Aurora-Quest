"""
RAG Service using Pinecone Vector Database
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
import openai
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
from config import settings


class RAGService:
    """
    Retrieval-Augmented Generation service using Pinecone
    """
    
    def __init__(self):
        # Initialize OpenAI
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        
        # Initialize Pinecone
        self.pc = None
        self.index = None
        if settings.PINECONE_API_KEY:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self._initialize_index()
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
    
    def _initialize_index(self):
        """Initialize or get existing Pinecone index"""
        try:
            index_name = settings.PINECONE_INDEX_NAME
            
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            
            if index_name not in [idx.name for idx in existing_indexes]:
                # Create new index
                self.pc.create_index(
                    name=index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
            
            self.index = self.pc.Index(index_name)
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            response = openai.Embedding.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    def index_document(
        self,
        user_id: int,
        session_id: int,
        file_path: str,
        filename: str
    ) -> int:
        """
        Process and index a document into Pinecone
        
        Returns:
            Number of chunks indexed
        """
        try:
            # Load document
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path)
            else:
                return 0
            
            documents = loader.load()
            chunks = self.text_splitter.split_documents(documents)
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, chunk in enumerate(chunks):
                embedding = self.get_embedding(chunk.page_content)
                if not embedding:
                    continue
                
                vector_id = f"user_{user_id}_session_{session_id}_doc_{filename}_chunk_{i}"
                
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "filename": filename,
                        "chunk_id": i,
                        "text": chunk.page_content[:1000],  # Store preview
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
            
            # Upsert to Pinecone
            if self.index and vectors:
                self.index.upsert(vectors=vectors)
                return len(vectors)
            
            return 0
        
        except Exception as e:
            print(f"Error indexing document: {e}")
            return 0
    
    def retrieve_context(
        self,
        user_id: int,
        session_id: int,
        query: str,
        top_k: int = 3
    ) -> str:
        """Retrieve relevant context for a query"""
        try:
            if not self.index:
                return ""
            
            # Generate query embedding
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                return ""
            
            # Query Pinecone with filters
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter={
                    "user_id": user_id,
                    "session_id": session_id
                },
                include_metadata=True
            )
            
            # Combine retrieved texts
            contexts = []
            for match in results.matches:
                if match.score > 0.7:  # Similarity threshold
                    contexts.append(match.metadata.get("text", ""))
            
            return "\n\n".join(contexts)
        
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return ""
    
    def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Generate AI response using retrieved context"""
        try:
            if not settings.OPENAI_API_KEY:
                if context:
                    return f"Based on your materials: {context[:300]}..."
                return "I'm ready to help! Upload your study materials first."
            
            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": """You are Aurora, a friendly and knowledgeable AI study companion. 
                    Help students understand concepts, answer questions, and provide explanations.
                    Use the provided context from their study materials to give accurate answers.
                    If the context doesn't contain relevant information, say so politely and offer general help."""
                }
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Last 3 exchanges
            
            # Add current query with context
            user_message = query
            if context:
                user_message = f"Context from study materials:\n{context}\n\nStudent's question: {query}"
            
            messages.append({"role": "user", "content": user_message})
            
            # Call OpenAI
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm having trouble generating a response. Please try again!"
    
    def generate_quiz(
        self,
        user_id: int,
        session_id: int,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """Generate quiz questions from indexed materials"""
        try:
            if not self.index or not settings.OPENAI_API_KEY:
                return self._get_sample_questions(num_questions)
            
            # Get random chunks from user's materials
            results = self.index.query(
                vector=[0.1] * 1536,  # Dummy vector to get random results
                top_k=10,
                filter={
                    "user_id": user_id,
                    "session_id": session_id
                },
                include_metadata=True
            )
            
            if not results.matches:
                return self._get_sample_questions(num_questions)
            
            # Combine context
            context = "\n".join([m.metadata.get("text", "") for m in results.matches])
            
            # Generate questions using GPT
            prompt = f"""Based on the following study materials, generate {num_questions} multiple choice questions at {difficulty} difficulty level.

Study Materials:
{context[:3000]}

Format each question as JSON:
{{
    "question": "question text",
    "options": ["A", "B", "C", "D"],
    "correct": 0,
    "explanation": "why this answer is correct"
}}

Return a JSON array of {num_questions} questions."""
            
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=2000
            )
            
            import json
            questions = json.loads(response.choices[0].message.content)
            return questions if isinstance(questions, list) else [questions]
        
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return self._get_sample_questions(num_questions)
    
    def _get_sample_questions(self, num: int) -> List[Dict]:
        """Fallback sample questions"""
        return [
            {
                "question": f"Sample question {i+1}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct": i % 4,
                "explanation": "Upload study materials for personalized questions!"
            }
            for i in range(num)
        ]
