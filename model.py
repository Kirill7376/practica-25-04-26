import os
import sys
from llama_cpp import Llama

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

MODEL_FILENAME = "Gemma-3-4B-VL-it-Gemini-Pro-Heretic-Uncensored-Thinking_Q4_k_m.gguf"
MODEL_PATH = os.path.join(base_path, "models", MODEL_FILENAME)

if not os.path.exists(MODEL_PATH):
    print(f"ОШИБКА: Файл модели не найден по пути: {MODEL_PATH}")

llm = Llama(
    model_path=MODEL_PATH,
    chat_format="gemma",
    n_ctx=16384,
    n_threads=4,
    verbose=False
)

def generate_text_response(messages: list, temperature=0.7, max_tokens=150):
    output = llm.create_chat_completion(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return output['choices'][0]['message']['content']
