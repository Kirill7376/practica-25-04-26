
import os
import sys
from urllib.request import urlretrieve

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

MODEL_URL = "https://huggingface.co/Andycurrent/Gemma-3-4B-VL-it-Gemini-Pro-Heretic-Uncensored-Thinking_GGUF/resolve/main/Gemma-3-4B-VL-it-Gemini-Pro-Heretic-Uncensored-Thinking_Q4_k_m.gguf"

MODEL_FILENAME = MODEL_URL.split("/")[-1]

MODELS_DIR = os.path.join(base_path, "models")
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_FILENAME)

def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    if os.path.exists(MODEL_PATH):
        print(f"Модель уже существует: {MODEL_PATH}")
        return

    print(f"Скачиваю модель ({MODEL_FILENAME})...")
    print("Это может занять несколько минут в зависимости от скорости интернета.")
    try:
        urlretrieve(MODEL_URL, MODEL_PATH)
        print(f"Модель успешно скачана: {MODEL_PATH}")
    except Exception as e:
        print(f"Ошибка при скачивании модели: {e}")
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        sys.exit(1)

if __name__ == "__main__":
    main()
