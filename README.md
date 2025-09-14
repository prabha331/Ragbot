RAG-Based Chatbot 

Overview

This project is a Retrieval-Augmented Generation (RAG) chatbot developed for the LLM Challenge as part of the internship process at Ragworks. The application integrates a Streamlit frontend, FastAPI backend, and a RAG pipeline using Chroma vector store and OpenRouter’s GPT-3.5-turbo. It supports user authentication, document uploads (PDF, DOCX, TXT), RAG-powered chat responses, and conversation history, with a focus on security and usability.

Features
User Authentication: Secure login/register with JWT tokens and bcrypt password hashing.
Document Upload: Supports PDF, DOCX, and TXT files, with robust text extraction and error handling.
RAG Integration: User-specific document retrieval using Chroma vector store, ensuring privacy and relevant responses.
Chat Interface: Streamlit-based UI for real-time chats, with conversation history stored in SQLite.
Error Handling: Comprehensive try-except blocks for API, document processing, and database operations.


Unique Enhancements:
User-specific RAG isolation to prevent data leakage.
Custom LLM prompting to reduce hallucinations.
Utility scripts (migrate_database.py, reset_database.py) for schema updates and development resets.
Backend logging for debugging.

Tech Stack
Frontend: Streamlit
Backend: FastAPI, Uvicorn
Database: SQLite (SQLModel)
Authentication: python-jose (JWT), passlib[bcrypt]
LLM/RAG: langchain-openai (GPT-3.5-turbo via OpenRouter), langchain-huggingface (Sentence Transformers), Chroma (chromadb)
Document Processing: PyMuPDF (PDFs), docx2txt (DOCX)
Other: python-multipart (file uploads), dotenv (environment variables)

Installation

Clone the Repository:

git clone [Insert Your GitHub Repo Link Here]
cd [Repo Name]


Install Dependencies:

pip install fastapi uvicorn sqlmodel passlib[bcrypt] python-jose[cryptography] python-multipart langchain-huggingface langchain-openai langchain-community chromadb streamlit PyMuPDF docx2txt

Configure Environment: Create a .env file in the project root with:

OPENROUTER_API_KEY=sk-or-v1-[your-api-key]
SECRET_KEY=[your-secret-key]
REDIS_URL=redis://localhost:6379/0
Obtain an OpenRouter API key from openrouter.ai.
Generate a secret key: python -c "import secrets; print(secrets.token_urlsafe(32))"


Run the Backend:
uvicorn main:app --reload

Run the Frontend:
streamlit run app.py

Usage
Open http://localhost:8501 in your browser.
Register a new account or log in.
Upload documents (PDF, DOCX, or TXT) via the "Upload Document" tab.
Start chatting in the "Chat" tab; the system retrieves relevant document chunks for RAG-powered responses.
Use the "New Conversation" button to start a fresh chat or "Logout" to end the session.

Project Structure
app.py: Streamlit frontend for login, registration, document upload, and chat.
main.py: FastAPI backend with endpoints for authentication, document ingestion, and chat.
auth.py: JWT authentication logic and user management.
rag.py: RAG pipeline for document ingestion and retrieval.
models.py: SQLModel definitions for User, Conversation, and Message tables.
migrate_database.py: Utility to update database schema (e.g., add conversation titles).
reset_database.py: Utility to reset SQLite and Chroma databases for development.
.env: Environment variables (not tracked in Git).
