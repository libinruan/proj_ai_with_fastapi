# 3-2-main.py

from fastapi import FastAPI
from models import load_text_model, generate_text

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Welcome to the text generation API. Use /generate/text?prompt=your_prompt to generate text."}

@app.get("/generate/text")
def serve_language_model_controller(prompt: str) -> str:
    pipe = load_text_model(model_name="ollama:qwen3:0.6b")
    output = generate_text(pipe, prompt)
    return output

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
