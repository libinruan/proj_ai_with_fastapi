# Debugging Ollama Model Integration

## Step 1: Understanding the Current Setup

Let's first understand what we're working with:

1. We have a FastAPI application defined in `main.py` that uses functions from `models.py`
2. In `models.py`, we have:
   - A `load_text_model()` function that can load either HuggingFace models or Ollama models
   - An `OllamaModel` class that wraps the Ollama API
   - A `DummyTokenizer` class to maintain compatibility with HuggingFace's interface
   - A `generate_text()` function that works with either type of model

3. The issue is that we're unable to successfully invoke the locally installed Qwen3:0.6b model through Ollama.

Let's examine the current implementation and identify potential issues:

### Current Implementation Analysis

Looking at the code in `models.py`:

- The `load_text_model` function correctly identifies Ollama models by the "ollama:" prefix
- The `OllamaModel` class is using the `/api/generate` endpoint from Ollama
- The `DummyTokenizer` is formatting messages with `<|system|>`, `<|user|>`, and `<|assistant|>` tags

Potential issues:
1. The Ollama API endpoint might not be correct or might require different parameters
2. The message formatting in `DummyTokenizer` might not match what Qwen3 expects
3. The response handling in `OllamaModel.__call__` might not correctly extract the generated text

Let's check if Ollama is running and if we can access the Qwen3:0.6b model directly using curl before making changes to the code.

## Step 2: Analyzing the Ollama API Usage

Based on the `TESTING_OLLAMA_W_cURL.md` file, we have valuable insights about how to interact with the Ollama API:

1. The Qwen3:0.6b model is definitely installed and available (confirmed by `/api/tags` endpoint)
2. There are two main endpoints for generating text:
   - `/api/chat` - Designed for conversational interactions with structured message format
   - `/api/generate` - General purpose text generation with simpler prompt format

3. Key findings from the testing:
   - The `/api/chat` endpoint works well with the Qwen3 model
   - It handles message structure automatically and has good performance
   - The response includes the generated text in `message.content`
   - The current implementation in `OllamaModel` is using `/api/generate` instead of `/api/chat`

4. Qwen3 model specifics:
   - It supports both standard chat format and Qwen's specific format with `<|im_start|>` and `<|im_end|>` tags
   - It includes `<think>` tags in responses showing the model's reasoning

Based on these findings, we should modify our `OllamaModel` class to use the `/api/chat` endpoint instead of `/api/generate` since it's better suited for conversational applications and works well with the Qwen3 model.

## Step 3: Implemented Changes to models.py

I've updated the `models.py` file with the following key changes:

1. **Modified the `OllamaModel.__call__` method:**
   - Changed the endpoint from `/api/generate` to `/api/chat`
   - Added parsing logic to extract system and user messages from the formatted prompt
   - Updated the payload structure to use the `messages` format expected by the `/api/chat` endpoint
   - Changed the response handling to extract text from `message.content` instead of `response`
   - Added code to remove the `<think>` tags and content from the response

2. **Kept the `DummyTokenizer` class intact:**
   - The current formatting with `<|system|>`, `<|user|>`, and `<|assistant|>` tags works as an intermediate format
   - The `OllamaModel.__call__` method now parses this format and converts it to the structure expected by the `/api/chat` endpoint

3. **No changes to `generate_text` function:**
   - The function already works correctly with both HuggingFace pipelines and our `OllamaModel` wrapper

These changes should allow the `main.py` application to successfully invoke the Qwen3:0.6b model through Ollama using the more appropriate `/api/chat` endpoint.

## Step 4: Testing the Updated Implementation

Now let's test the updated implementation by running the FastAPI application and making a request to the `/generate/text` endpoint. We'll need to:

1. Run the FastAPI application:
```bash
python main.py
```

2. Make a request to the `/generate/text` endpoint:
```bash
curl "http://localhost:8000/generate/text?prompt=What%20is%20FastAPI%3F"
```

If everything is working correctly, we should receive a response from the Qwen3:0.6b model explaining what FastAPI is.