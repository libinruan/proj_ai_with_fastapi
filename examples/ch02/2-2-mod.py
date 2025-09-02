"""
(1) command 1.
http://localhost:8000
(2) command 2.
http://localhost:8000/chat?prompt=tell me a joke
(3) command 3.
http://localhost:8000/users - POST endpoint for user creation

curl -X POST "http://localhost:8000/users" -H "Content-Type: application/json" -d '{"username":"john","password":"Password123"}'
"""

from fastapi import FastAPI
from openai import OpenAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator
import uvicorn
from fastapi.responses import RedirectResponse

# Load environment variables from .env file
load_dotenv()
# Get API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

app = FastAPI()
openai_client = OpenAI(api_key=openai_api_key)

class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        return value

# Case 1.
@app.get("/")
def root_controller():
    return {"status": "healthy"}

# # Case 2.
# # include_in_schema=False means it won't appear in the auto-generated API documentation
# @app.get("/", include_in_schema=False)
# def docs_redirect_controller():
#     return RedirectResponse(url="/docs", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/users")
async def create_user_controller(user: UserCreate):
    return {"name": user.username, "message": "Account successfully created"}

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
    uvicorn.run("2-2-mod:app", host="0.0.0.0", port=8000, reload=True) 
