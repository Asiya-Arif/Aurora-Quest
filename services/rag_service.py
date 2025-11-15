"""
Enhanced RAG Service with Document Q&A, Quiz, and Flashcard Generation
"""
from typing import List, Dict, Optional
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from config import settings
import os


class RAGService:
    """
    Retrieval-Augmented Generation service using ChromaDB
    """
    
    def __init__(self):
        self.embeddings = None
        self.llm = None
        
        # Initialize OpenAI if API key is available
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            try:
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=settings.OPENAI_API_KEY
                )
                self.llm = ChatOpenAI(
                    openai_api_key=settings.OPENAI_API_KEY,
                    model_name=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                    temperature=0.7
                )
            except Exception as e:
                print(f"OpenAI initialization error: {e}")
    
    async def get_response(
        self,
        query: str,
        session_id: int,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Generate AI response using RAG from uploaded documents"""
        try:
            # Get vectorstore for this session
            vectorstore_path = f"{settings.CHROMA_PERSIST_DIR}/session_{session_id}"
            
            if not os.path.exists(vectorstore_path):
                return "📚 Please upload your study materials first! I'll be able to answer questions once you upload PDF, TXT, or DOCX files. ✨"
            
            if not self.embeddings or not self.llm:
                return "🤖 I'm here to help! Unfortunately, OpenAI API is not configured. Please check your settings to enable AI-powered responses. In the meantime, upload materials and I'll do my best! 💖"
            
            # Load vectorstore
            vectorstore = Chroma(
                persist_directory=vectorstore_path,
                embedding_function=self.embeddings
            )
            
            # Create custom prompt
            prompt_template = """You are Aurora, a friendly and enthusiastic study companion AI! 🌟
            
You help students learn by answering their questions using the context from their study materials.
Be encouraging, use emojis appropriately, and explain concepts clearly.

Context from study materials:
{context}

Student's question: {question}

Your helpful answer:"""
            
            PROMPT = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )
            
            # Create QA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
                chain_type_kwargs={"prompt": PROMPT},
                return_source_documents=False
            )
            
            # Get response
            result = qa_chain.invoke({"query": query})
            return result.get("result", "I'm not sure how to answer that. Could you rephrase? 🤔")
        
        except Exception as e:
            print(f"RAG response error: {e}")
            return f"I encountered an error while processing your question. Please try again! 🥺 (Error: {str(e)})"
    
    async def generate_quiz(
        self,
        session_id: int,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """Generate quiz questions from uploaded documents"""
        try:
            vectorstore_path = f"{settings.CHROMA_PERSIST_DIR}/session_{session_id}"
            
            if not os.path.exists(vectorstore_path) or not self.embeddings or not self.llm:
                return self._get_sample_questions(num_questions)
            
            # Load vectorstore
            vectorstore = Chroma(
                persist_directory=vectorstore_path,
                embedding_function=self.embeddings
            )
            
            # Get diverse chunks from materials
            retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
            docs = retriever.get_relevant_documents("Generate diverse questions covering main concepts")
            
            if not docs:
                return self._get_sample_questions(num_questions)
            
            # Combine content
            context = "\n\n".join([doc.page_content for doc in docs[:5]])
            
            # Generate questions using LLM
            prompt = f"""Based on the following study materials, create {num_questions} multiple-choice questions at {difficulty} difficulty level.

Study Materials:
{context[:3000]}

Generate EXACTLY {num_questions} questions. For each question, provide:
1. A clear question
2. Four distinct options (A, B, C, D)
3. The correct answer (must be one of: "Option A", "Option B", "Option C", or "Option D")
4. A brief explanation

Format each question EXACTLY like this:
QUESTION: [question text]
OPTION_A: [first option]
OPTION_B: [second option]
OPTION_C: [third option]
OPTION_D: [fourth option]
CORRECT: [Option A, Option B, Option C, or Option D]
---END---

Make sure to end each question with ---END--- marker."""
            
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse response
            questions = self._parse_quiz_response(content, num_questions)
            
            return questions if questions else self._get_sample_questions(num_questions)
        
        except Exception as e:
            print(f"Quiz generation error: {e}")
            return self._get_sample_questions(num_questions)
    
    def _parse_quiz_response(self, content: str, num_questions: int) -> List[Dict]:
        """Parse LLM response into quiz questions"""
        questions = []
        
        try:
            # Split by question markers
            question_blocks = content.split('---END---')
            
            for block in question_blocks[:num_questions]:
                if not block.strip():
                    continue
                
                lines = block.strip().split('\n')
                question_data = {}
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('QUESTION:'):
                        question_data['question'] = line.replace('QUESTION:', '').strip()
                    elif line.startswith('OPTION_A:'):
                        question_data['option_a'] = line.replace('OPTION_A:', '').strip()
                    elif line.startswith('OPTION_B:'):
                        question_data['option_b'] = line.replace('OPTION_B:', '').strip()
                    elif line.startswith('OPTION_C:'):
                        question_data['option_c'] = line.replace('OPTION_C:', '').strip()
                    elif line.startswith('OPTION_D:'):
                        question_data['option_d'] = line.replace('OPTION_D:', '').strip()
                    elif line.startswith('CORRECT:'):
                        question_data['correct'] = line.replace('CORRECT:', '').strip()
                
                # Validate question has all required fields
                if all(key in question_data for key in ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct']):
                    questions.append(question_data)
            
            return questions
        
        except Exception as e:
            print(f"Parse error: {e}")
            return []
    
    def _get_sample_questions(self, num: int) -> List[Dict]:
        """Fallback sample questions"""
        return [
            {
                "question": f"Sample question {i+1} - Upload materials for personalized quizzes!",
                "option_a": "Option A",
                "option_b": "Option B",
                "option_c": "Option C",
                "option_d": "Option D",
                "correct": "Option A"
            }
            for i in range(num)
        ]
    
    async def generate_flashcards(
        self,
        session_id: int,
        num_cards: int = 10
    ) -> List[Dict]:
        """Generate flashcards from uploaded documents"""
        try:
            vectorstore_path = f"{settings.CHROMA_PERSIST_DIR}/session_{session_id}"
            
            if not os.path.exists(vectorstore_path) or not self.embeddings or not self.llm:
                return self._get_sample_flashcards(num_cards)
            
            # Load vectorstore
            vectorstore = Chroma(
                persist_directory=vectorstore_path,
                embedding_function=self.embeddings
            )
            
            # Get diverse chunks
            retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
            docs = retriever.get_relevant_documents("Key concepts, definitions, important terms")
            
            if not docs:
                return self._get_sample_flashcards(num_cards)
            
            # Combine content
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Generate flashcards
            prompt = f"""Based on the following study materials, create {num_cards} flashcards for studying.

Study Materials:
{context[:3000]}

For each flashcard, provide:
- FRONT: A key concept, term, or question
- BACK: The answer, definition, or explanation

Format EXACTLY like this:
FRONT: [concept/question]
BACK: [answer/explanation]
---END---

Create {num_cards} flashcards covering the most important concepts."""
            
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse response
            flashcards = self._parse_flashcards(content, num_cards)
            
            return flashcards if flashcards else self._get_sample_flashcards(num_cards)
        
        except Exception as e:
            print(f"Flashcard generation error: {e}")
            return self._get_sample_flashcards(num_cards)
    
    def _parse_flashcards(self, content: str, num_cards: int) -> List[Dict]:
        """Parse LLM response into flashcards"""
        flashcards = []
        
        try:
            card_blocks = content.split('---END---')
            
            for block in card_blocks[:num_cards]:
                if not block.strip():
                    continue
                
                lines = block.strip().split('\n')
                card_data = {}
                
                current_section = None
                for line in lines:
                    line = line.strip()
                    if line.startswith('FRONT:'):
                        current_section = 'front'
                        card_data['front'] = line.replace('FRONT:', '').strip()
                    elif line.startswith('BACK:'):
                        current_section = 'back'
                        card_data['back'] = line.replace('BACK:', '').strip()
                    elif current_section and line:
                        # Continuation of previous section
                        card_data[current_section] += ' ' + line
                
                if 'front' in card_data and 'back' in card_data:
                    flashcards.append(card_data)
            
            return flashcards
        
        except Exception as e:
            print(f"Flashcard parse error: {e}")
            return []
    
    def _get_sample_flashcards(self, num: int) -> List[Dict]:
        """Fallback sample flashcards"""
        return [
            {
                "front": f"Sample Concept {i+1}",
                "back": "Upload your study materials to generate personalized flashcards! ✨"
            }
            for i in range(num)
        ]
    
    async def get_language_tutor_response(
        self,
        query: str,
        language: str,
        session_id: int,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Generate language tutor response with RAG support"""
        try:
            # Check if there are uploaded materials for this session
            vectorstore_path = f"{settings.CHROMA_PERSIST_DIR}/session_{session_id}"
            has_materials = os.path.exists(vectorstore_path)
            
            if not self.llm:
                return f"Hello! I'm your {language} tutor! 🌍 Ask me anything about {language} - grammar, vocabulary, pronunciation, or culture! ✨"
            
            # Build context from materials if available
            context = ""
            if has_materials and self.embeddings:
                try:
                    vectorstore = Chroma(
                        persist_directory=vectorstore_path,
                        embedding_function=self.embeddings
                    )
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
                    docs = retriever.get_relevant_documents(query)
                    if docs:
                        context = "\n".join([doc.page_content[:500] for doc in docs[:2]])
                except:
                    pass
            
            # Create tutor prompt
            base_prompt = f"""You are a friendly and encouraging {language} language tutor! 🌟

Your role:
- Help students learn {language} through conversation
- Correct pronunciation and grammar gently
- Explain cultural context when relevant
- Provide examples and practice exercises
- Be encouraging and supportive! Use emojis appropriately

"""
            
            if context:
                base_prompt += f"""Reference materials (student's uploaded documents):
{context}

"""
            
            # Add conversation history
            messages = [{"role": "system", "content": base_prompt}]
            
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Last 3 exchanges
            
            messages.append({"role": "user", "content": query})
            
            # Get response
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        
        except Exception as e:
            print(f"Language tutor error: {e}")
            return f"I'm here to help you learn {language}! 🌍 Ask me anything - vocabulary, grammar, or practice conversation! ✨"


__all__ = ["RAGService"]
