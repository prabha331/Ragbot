from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from models import User, Conversation, Message, engine
from auth import create_access_token, get_current_user, authenticate_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, Token
from rag import ingest_document, get_rag_response
from pydantic import BaseModel
from typing import List
import os
import asyncio
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class RegisterForm(BaseModel):
    username: str
    email: str
    password: str

class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str

@app.post("/register")
def register(form: RegisterForm):
    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.username == form.username)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        hashed_password = get_password_hash(form.password)
        user = User(username=form.username, email=form.email, hashed_password=hashed_password)
        session.add(user)
        session.commit()
        session.refresh(user)
    return {"msg": "User registered"}

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"Login attempt for username: {form_data.username}")  # Debug print
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        print(f"Authentication failed for: {form_data.username}")  # Debug print
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    print(f"Authentication successful for: {form_data.username}")  # Debug print
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    file_path = f"./uploads/{file.filename}"
    os.makedirs("./uploads", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    try:
        ingest_document(file_path, current_user.id)
        return {"msg": "Document ingested"}
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    logger.info(f"Chat request received: {request}")
    with Session(engine) as session:
        # If conversation_id is provided, get existing conversation
        if request.conversation_id:
            conv = session.exec(select(Conversation).where(Conversation.id == request.conversation_id)).first()
            if not conv or conv.user_id != current_user.id:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            conv = Conversation(user_id=current_user.id)
            session.add(conv)
            session.commit()
            session.refresh(conv)
        
        # Add user message
        user_msg = Message(conversation_id=conv.id, content=request.message, is_user=True)
        session.add(user_msg)
        session.commit()
        
        try:
            # Get RAG response
            response = get_rag_response(request.message, current_user.id)
            
            # Add bot message
            bot_msg = Message(conversation_id=conv.id, content=response, is_user=False)
            session.add(bot_msg)
            session.commit()
            
            return {"response": response, "conversation_id": conv.id}
            
        except Exception as e:
            logger.error(f"Error getting RAG response: {str(e)}")
            # Still save the user message but return error
            error_response = "I'm sorry, I encountered an error while processing your request. Please try again."
            bot_msg = Message(conversation_id=conv.id, content=error_response, is_user=False)
            session.add(bot_msg)
            session.commit()
            return {"response": error_response, "conversation_id": conv.id}

@app.get("/history/{conversation_id}", response_model=List[dict])
def get_history(conversation_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        # Verify conversation belongs to current user
        conv = session.exec(select(Conversation).where(Conversation.id == conversation_id)).first()
        if not conv or conv.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        msgs = session.exec(select(Message).where(Message.conversation_id == conversation_id)).all()
        return [{"content": m.content, "is_user": m.is_user} for m in msgs]