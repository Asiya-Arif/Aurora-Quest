from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from config import settings
import os

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-3.5-turbo",
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        self.chat_prompt = PromptTemplate(
            template="""You are Aurora, a friendly and enthusiastic AI study companion! 🌈✨
            
You help students learn by answering questions based on their study materials.
Be encouraging, warm, and use emojis to make learning fun!

Context from study materials:
{context}

Student's question: {question}

Your helpful answer (be clear, friendly, and add relevant emojis):""",
            input_variables=["context", "question"]
        )
    
    async def get_response(self, query: str, session_id: int) -> str:
        try:
            vectorstore_path = f"{settings.CHROMA_PERSIST_DIR}/session_{session_id}"
            
            if not os.path.exists(vectorstore_path):
                return "Hi! 👋 Please upload some study materials first so I can help you learn! 📚✨"
            
            vectorstore = Chroma(
                persist_directory=vectorstore_path,
                embedding_function=self.embeddings
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(
                    search_kwargs={"k": 3}
                ),
                chain_type_kwargs={"prompt": self.chat_prompt}
            )
            
            response = await qa_chain.ainvoke({"query": query})
            return response["result"]
        
        except Exception as e:
            return f"Oops! I encountered an error: {str(e)}. Let's try that again! 💫"
    
    async def generate_quiz(self, session_id: int, num_questions: int = 5) -> list:
        try:
            vectorstore_path = f"{settings.CHROMA_PERSIST_DIR}/session_{session_id}"
            
            if not os.path.exists(vectorstore_path):
                return []
            
            vectorstore = Chroma(
                persist_directory=vectorstore_path,
                embedding_function=self.embeddings
            )
            
            docs = vectorstore.similarity_search("", k=10)
            context = "\n\n".join([doc.page_content for doc in docs[:5]])
            
            quiz_prompt = f"""Based on this study material, create {num_questions} multiple choice questions.
            
Material:
{context}

Format each question as:
Q: [question]
A) [option]
B) [option]
C) [option]
D) [option]
CORRECT: [A/B/C/D]

Generate questions now:"""
            
            response = await self.llm.ainvoke(quiz_prompt)
            questions = self._parse_quiz_response(response.content)
            return questions[:num_questions]
        
        except Exception as e:
            print(f"Quiz generation error: {e}")
            return []
    
    def _parse_quiz_response(self, response: str) -> list:
        questions = []
        current_q = {}
        
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('Q:'):
                if current_q:
                    questions.append(current_q)
                current_q = {'question': line[2:].strip()}
            elif line.startswith('A)'):
                current_q['option_a'] = line[2:].strip()
            elif line.startswith('B)'):
                current_q['option_b'] = line[2:].strip()
            elif line.startswith('C)'):
                current_q['option_c'] = line[2:].strip()
            elif line.startswith('D)'):
                current_q['option_d'] = line[2:].strip()
            elif line.startswith('CORRECT:'):
                current_q['correct'] = line.split(':')[1].strip()
        
        if current_q:
            questions.append(current_q)
        
        return questions
