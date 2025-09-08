# models.py

import torch
import requests
from transformers import Pipeline, pipeline
from typing import Union, Dict, List, Any, Optional

prompt = "How to set up a FastAPI project?"
system_prompt = """
Your name is FastAPI bot and you are a helpful
chatbot responsible for teaching FastAPI to your users.
Always respond in markdown.
"""

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_text_model(model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
    """
    Load a text generation model either from HuggingFace or Ollama.
    
    Args:
        model_name: Name of the model to load. For Ollama models, use "ollama:model_name"
                   (e.g., "ollama:qwen3:0.6b")
    
    Returns:
        Either a HuggingFace pipeline or an OllamaModel wrapper
    """
    if model_name.startswith("ollama:"):
        # Extract the actual model name after "ollama:"
        ollama_model_name = model_name.split("ollama:")[1]
        return OllamaModel(model_name=ollama_model_name)
    else:
        # Use the original HuggingFace pipeline
        pipe = pipeline(
            "text-generation",
            model=model_name,
            torch_dtype=torch.bfloat16,
            device=device,
        )
        return pipe


class OllamaModel:
    """Wrapper class for Ollama models to provide a similar interface to HuggingFace pipelines"""
    
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.tokenizer = DummyTokenizer()  # Placeholder for compatibility
        
    def __call__(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_new_tokens: Optional[int] = None,
        do_sample: bool = True,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
    ) -> List[Dict[str, str]]:
        """
        Generate text using Ollama API via the /api/chat endpoint
        
        Returns:
            List containing a dict with generated_text
        """
        # Parse the prompt to extract messages
        # The prompt is expected to be formatted by DummyTokenizer.apply_chat_template
        messages = []
        
        # Simple parsing of the formatted prompt to extract system and user messages
        # This assumes the prompt was formatted by our DummyTokenizer
        if "<|system|>" in prompt:
            system_content = prompt.split("<|system|>\n")[1].split("\n<|user|>")[0].strip()
            messages.append({"role": "system", "content": system_content})
            
        if "<|user|>" in prompt:
            user_content = prompt.split("<|user|>\n")[1].split("\n<|assistant|>")[0].strip()
            messages.append({"role": "user", "content": user_content})
        
        # If no messages were extracted, use the entire prompt as a user message
        if not messages:
            messages.append({"role": "user", "content": prompt})
            
        # Prepare the payload for the /api/chat endpoint
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        
        # Add optional parameters if provided
        if max_new_tokens is not None:
            payload["max_tokens"] = max_new_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if top_k is not None:
            payload["top_k"] = top_k
            
        # Use the /api/chat endpoint instead of /api/generate
        response = requests.post(f"{self.base_url}/api/chat", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            # Extract the generated text from the message content
            generated_text = result.get("message", {}).get("content", "")
            
            # Remove the <think> tags and content if present
            if "<think>" in generated_text and "</think>" in generated_text:
                think_start = generated_text.find("<think>")
                think_end = generated_text.find("</think>") + len("</think>")
                generated_text = generated_text[:think_start] + generated_text[think_end:].strip()
            
            return [{"generated_text": generated_text}]
        else:
            raise Exception(f"Ollama API error: {response.text}")


class DummyTokenizer:
    """Placeholder tokenizer for Ollama models to maintain compatibility with HF pipeline interface"""
    
    def apply_chat_template(
        self, messages: List[Dict[str, str]], tokenize: bool = False, add_generation_prompt: bool = False
    ) -> str:
        """
        Format chat messages for Ollama models
        """
        formatted_prompt = ""
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                formatted_prompt += f"<|system|>\n{content}\n"
            elif role == "user":
                formatted_prompt += f"<|user|>\n{content}\n"
            elif role == "assistant":
                formatted_prompt += f"<|assistant|>\n{content}\n"
        
        if add_generation_prompt:
            formatted_prompt += "<|assistant|>\n"
            
        return formatted_prompt


def generate_text(
    pipe: Union[Pipeline, OllamaModel], 
    prompt: str, 
    temperature: float = 0.7
) -> str:
    """
    Generate text using either a HuggingFace pipeline or Ollama model
    
    Args:
        pipe: Either a HuggingFace pipeline or OllamaModel instance
        prompt: The prompt to generate text from
        temperature: Controls randomness in generation
        
    Returns:
        Generated text as a string
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    
    formatted_prompt = pipe.tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    
    predictions = pipe(
        formatted_prompt,
        temperature=temperature,
        max_new_tokens=256,
        do_sample=True,
        top_k=50,
        top_p=0.95,
    )
    
    # Handle different return formats
    if isinstance(pipe, OllamaModel):
        output = predictions[0]["generated_text"]
    else:
        output = predictions[0]["generated_text"].split("</s>\n<|assistant|>\n")[-1]
        
    return output