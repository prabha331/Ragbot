from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
import fitz  # PyMuPDF
import docx2txt
import os
from dotenv import load_dotenv
import redis
import hashlib
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize embeddings and LLM
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
llm = ChatOpenAI(
    model="openai/gpt-3.5-turbo",  # Use a more reliable model
    openai_api_key=os.getenv("OPENROUTER_API_KEY"), 
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.1
)

# Vector store
vector_store = Chroma(
    collection_name="documents", 
    embedding_function=embeddings, 
    persist_directory="./chroma_db"
)

def ingest_document(file_path: str, user_id: int):
    try:
        logger.info(f"Starting document ingestion for file: {file_path}")
        
        # Handle multiple types (PDF, TXT, DOCX)
        if file_path.endswith(".pdf"):
            doc = fitz.open(file_path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
        elif file_path.endswith(".docx"):
            text = docx2txt.process(file_path)
        elif file_path.endswith(".txt"):
            with open(file_path, "r", encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError("Unsupported file type")

        if not text.strip():
            raise ValueError("Document appears to be empty or text could not be extracted")

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(text)
        
        if not chunks:
            raise ValueError("No chunks were created from the document")

        # Create metadata with user_id for each chunk
        metadata = [{"user_id": str(user_id), "source": file_path} for _ in chunks]
        
        # Add texts to vector store
        vector_store.add_texts(chunks, metadatas=metadata)
        vector_store.persist()
        
        logger.info(f"Successfully ingested {len(chunks)} chunks for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}")
        raise e
    finally:
        # Clean up the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

def get_rag_response(query: str, user_id: int):
    try:
        logger.info(f"Getting RAG response for user {user_id}, query: {query}")
        
        # First, try without user filtering to see if we have any documents at all
        try:
            retriever_all = vector_store.as_retriever(search_kwargs={"k": 5})
            all_docs = retriever_all.get_relevant_documents(query)
            logger.info(f"Total documents in database: {len(all_docs)}")
            
            if not all_docs:
                return "I don't have any documents uploaded yet. Please upload some documents first, then ask your questions."
            
            # Now try to filter by user_id
            user_docs = []
            for doc in all_docs:
                if doc.metadata.get("user_id") == str(user_id):
                    user_docs.append(doc)
            
            logger.info(f"Found {len(user_docs)} documents for user {user_id}")
            
            if not user_docs:
                return f"I don't have any documents uploaded by you. Please upload some documents first. (Found {len(all_docs)} documents from other users)"
            
            # Use the user's documents
            context = "\n\n".join([doc.page_content[:500] for doc in user_docs[:3]])  # Limit context length
            
        except Exception as e:
            logger.error(f"Error with document retrieval: {e}")
            return f"I'm having trouble accessing the documents. Error: {str(e)}"
        
        # Generate response with LLM
        try:
            prompt = f"""Based on the following context from uploaded documents, please answer the question. If the answer is not clearly in the context, say "I don't have enough information in the uploaded documents to answer that question."

Context: {context}

Question: {query}

Answer:"""
            
            response = llm.invoke(prompt)
            
            if hasattr(response, 'content'):
                result = response.content
            else:
                result = str(response)
            
            logger.info(f"RAG response generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return f"I found your documents but had trouble generating a response. Error: {str(e)}"
        
    except Exception as e:
        logger.error(f"Error in get_rag_response: {str(e)}")
        return f"I'm sorry, I encountered an error: {str(e)}"