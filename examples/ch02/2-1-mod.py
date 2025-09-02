"""
(1) command 1.
http://localhost:8000
(2) command 2.
http://localhost:8000/chat?prompt=tell me a joke
"""

from fastapi import FastAPI
from openai import OpenAI
import os
from dotenv import load_dotenv
import uvicorn

# Load environment variables from .env file
load_dotenv()
# Get API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

app = FastAPI()
openai_client = OpenAI(api_key=openai_api_key)


@app.get("/")
def root_controller():
    return {"status": "healthy"}


@app.get("/chat")
def chat_controller(prompt: str = "Inspire me"):
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    statement = response.choices[0].message.content.strip()
    return {"statement": statement}


if __name__ == "__main__":
    # Uvicorn looks for a file named "2-1-mod.py" with an app object inside it.
    # If change it to host="127.0.0.1", then restrict access to only your local machine.
    uvicorn.run("2-1-mod:app", host="0.0.0.0", port=8000, reload=True) 
