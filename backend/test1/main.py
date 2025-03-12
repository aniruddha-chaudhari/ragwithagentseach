from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.genai import types  # new import
import shutil
import os
import json
from datetime import datetime
from backend.test1.document import process_document
from backend.test1.utils import prepare_document
from google.api_core.exceptions import ResourceExhausted
import absl.logging

# Suppress verbose logs
absl.logging.set_verbosity(absl.logging.ERROR)

# Configure Gemini
genai.configure(api_key='AIzaSyD4lR1WQ1yaZumSFtMVTG_0Y8d0oRy1XhA')

# Create the model with configuration
generation_config = {
	"temperature": 1,
	"top_p": 0.95,
	"top_k": 40,
	"max_output_tokens": 8192,
}

model = genai.GenerativeModel(
	model_name="gemini-2.0-flash",
	generation_config=generation_config,
)

# Data Models
class ChatMessage(BaseModel):
	role: str
	content: str
	chat_id: Optional[str] = None  # Added optional chat_id

class ChatRequest(BaseModel):
	message: str
	chat_id: Optional[str] = None

class ChatResponse(BaseModel):
	message: str
	chat_id: str

class GoogleSearchRequest(BaseModel):
	query: str

app = FastAPI()

# Add CORS middleware
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Store chat sessions and document context
chat_sessions = {}
document_context = {}
conversation_history = []

def save_chat_history(chat_id: str, history: List[Dict[str, Any]]):
	if not os.path.exists('data'):
		os.makedirs('data')
	with open(f'data/{chat_id}-st_messages', 'w') as f:
		json.dump(history, f)

def load_chat_history(chat_id: str) -> List[Dict[str, Any]]:
	try:
		with open(f'data/{chat_id}-st_messages', 'r') as f:
			return json.load(f)
	except FileNotFoundError:
		return []

def add_message(role: str, text: str) -> None:
	conversation_history.append({
		"role": role,
		"parts": [text.rstrip("\n") + "\n"]
	})

# ------------------ Chat API Routes ------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
	try:
		chat_id = request.chat_id or str(datetime.now().timestamp())
		
		if chat_id not in chat_sessions:
			history = load_chat_history(chat_id)
			chat_sessions[chat_id] = model.start_chat(history=history)

		chat_session = chat_sessions[chat_id]
		
		# Add document context if available
		context_prompt = ""
		if chat_id in document_context:
			context = document_context[chat_id]
			context_prompt = (
				f"Remember this context about the document/image the user uploaded:\n"
				f"{context}\n\n"
				f"Now answer this question considering the above context:\n"
			)
		
		full_prompt = context_prompt + request.message
		response = chat_session.send_message(full_prompt)
		
		current_history = [
			{"role": "user", "parts": [request.message]},
			{"role": "model", "parts": [response.text]}
		]
		save_chat_history(chat_id, current_history)
		
		return ChatResponse(message=response.text, chat_id=chat_id)
		
	except ResourceExhausted:
		raise HTTPException(status_code=429, detail="API quota exceeded")
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/send-message")
async def send_message(chat_message: ChatMessage):
	user_msg = chat_message.content
	# Prepend document context if available for the provided chat_id
	if chat_message.chat_id and chat_message.chat_id in document_context:
		lower_msg = user_msg.lower().strip()
		# Immediately return stored document context if message asks about the image
		if lower_msg in ["whats the image about", "what's the image about", "whats the image about?", "what's the image about?"]:
			response_text = document_context[chat_message.chat_id]
			add_message("user", user_msg)
			add_message("model", response_text)
			return {"response": response_text}
		# Otherwise, prepend the context to the user's message
		context = document_context[chat_message.chat_id]
		user_msg = (f"Remember this context about the document/image the user uploaded:\n"
					f"{context}\n\n"
					f"Now answer this question considering the above context:\n"
					f"{user_msg}")
	add_message("user", user_msg)
	try:
		chat_session = model.start_chat(history=conversation_history)
		response = chat_session.send_message(user_msg)
		add_message("model", response.text)
		return {"response": response.text}
	except ResourceExhausted:
		return {"success": False, "error": "Resource exhausted. Please check your quota."}
	except Exception as e:
		return {"success": False, "error": str(e)}

@app.post("/chat/upload-document")
async def upload_document(
	file: UploadFile = File(...),
	chat_id: Optional[str] = None,
):
	try:
		temp_file_path = f"temp_{file.filename}"
		with open(temp_file_path, "wb") as buffer:
			shutil.copyfileobj(file.file, buffer)
		
		full_response = ""
		for chunk in prepare_document(temp_file_path, "Describe this document."):
			full_response += chunk
		
		os.remove(temp_file_path)
		
		# Store the context for this chat session
		auto_bot_response = ""
		if chat_id:
			document_context[chat_id] = full_response
			# Reinitialize chat session to include updated context
			chat_sessions[chat_id] = model.start_chat(history=load_chat_history(chat_id))
			# Auto-send a message to the chat bot using the document context
			auto_prompt = "what is the image about?"
			auto_bot_response_obj = chat_sessions[chat_id].send_message(auto_prompt)
			auto_bot_response = auto_bot_response_obj.text
			# Append messages to conversation history
			add_message("user", auto_prompt)
			add_message("model", auto_bot_response)
		
		# Also add the document response as a message for front-end display
		add_message("user", f"Document upload response:\n{full_response}")
		
		return {"success": True, "document_response": full_response, "auto_bot_response": auto_bot_response}
	except Exception as e:
		return {"success": False, "error": str(e)}

# ------------------ Paper Analysis Routes ------------------

@app.post("/analyze-paper")
async def analyze_paper(file: UploadFile = File(...)):
	try:
		temp_file_path = f"temp_{file.filename}"
		with open(temp_file_path, "wb") as buffer:
			shutil.copyfileobj(file.file, buffer)
		
		result = process_document(temp_file_path)
		os.remove(temp_file_path)
		return result
	except Exception as e:
		return {"success": False, "error": str(e)}

@app.get("/")
async def root():
	return {"message": "Teacher Assistant API is running"}

# ------------------ New Google Search Route ------------------

@app.post("/chat/google-search")
async def google_search(request: GoogleSearchRequest):
	try:
		absl.logging.info("Received google search request: %s", request.dict())
		if not request.query.strip():
			absl.logging.error("Empty query received")
			raise HTTPException(status_code=422, detail="Query cannot be empty")
		response = genai.generate_content(
			model='gemini-2.0-flash',
			prompt=request.query,
			config=types.GenerateContentConfig(
				tools=[types.Tool(google_search=types.GoogleSearchRetrieval)]
			)
		)
		absl.logging.info("Generated google search response: %s", response)
		return {"response": response}
	except Exception as e:
		absl.logging.error("Error in google_search: %s", str(e))
		raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(
		"main:app",
		host="0.0.0.0",
		port=8000,
		reload=True,  # Enable hot reloading
		reload_excludes=["*.pyc", "*.log"],  # Exclude unnecessary files from reload
		reload_includes=["*.py", "*.json"],  # Watch Python and JSON files
	)