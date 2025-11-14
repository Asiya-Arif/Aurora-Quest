from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from config import settings
import os

class DocumentProcessor:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
    
    async def process_document(self, file_path: str, session_id: int) -> bool:
        try:
            # Load document based on file type
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith('.docx'):
                loader = Docx2txtLoader(file_path)
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path)
            else:
                return False
            
            documents = loader.load()
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Create or update vector store
            vectorstore_path = f"{settings.CHROMA_PERSIST_DIR}/session_{session_id}"
            
            if os.path.exists(vectorstore_path):
                vectorstore = Chroma(
                    persist_directory=vectorstore_path,
                    embedding_function=self.embeddings
                )
                vectorstore.add_documents(chunks)
            else:
                vectorstore = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    persist_directory=vectorstore_path
                )
            
            vectorstore.persist()
            return True
        
        except Exception as e:
            print(f"Document processing error: {e}")
            return False
