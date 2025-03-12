import os
import absl.logging  # Added import
absl.logging.set_verbosity(absl.logging.ERROR)  # Suppress verbose logs
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted  # Added import
from backend.test1.utils import prepare_document  # Imported upload function from utils.py

genai.configure(api_key='AIzaSyD4lR1WQ1yaZumSFtMVTG_0Y8d0oRy1XhA')

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  # Removed unsupported "response_mime_type" key.
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash",
  generation_config=generation_config,
)

conversation_history = []  # Dynamic conversation history

# Optionally add system message for context if needed:
# add_message("system", "hey you are teaching assistant")

def add_message(role, text):
    conversation_history.append({
        "role": role,
        "parts": [text.rstrip("\n") + "\n"]
    })

# Start chat session with current dynamic history
chat_session = model.start_chat(history=conversation_history)

while True:
    user_input = input("Enter your message (or type 'exit' to quit): ")  # Updated to fetch user input dynamically
    if user_input.strip().lower() == "exit":
        break

    # Check if user intends to upload a document.
    if user_input.strip().startswith("upload"):
        # Hardcoded file path.
        file_path = "images.png"
        full_response = ""
        for chunk in prepare_document(file_path, "Describe this document."):
            full_response += chunk
        # Use "user" role instead of "system" to avoid unsupported system message.
        add_message("user", f"Document upload response:\n{full_response}")
        # Reinitialize chat_session to include the new message.
        chat_session = model.start_chat(history=conversation_history)
        print(full_response)
        continue

    add_message("user", user_input)
    try:
        response = chat_session.send_message(user_input)
    except ResourceExhausted as e:
        print("Error: Resource has been exhausted. Please check your quota.")
        continue
    add_message("model", response.text)
    print(response.text)