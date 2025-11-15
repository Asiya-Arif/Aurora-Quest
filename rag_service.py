from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Initialize ChromaDB
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

def store_in_vector_db(text, filename):
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    
    # Store in ChromaDB
    vector_store.add_texts(
        texts=chunks,
        metadatas=[{"source": filename} for _ in chunks]
    )

def retrieve_from_vector_db(subject, query=None, k=3):
    if query:
        docs = vector_store.similarity_search(query, k=k)
    else:
        docs = vector_store.similarity_search(subject, k=k)
    
    return "\n".join([doc.page_content for doc in docs])
