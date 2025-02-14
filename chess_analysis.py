from g4f import ChatCompletion, Provider
import json

def load_text(file_path: str) -> str:

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Ошибка при чтении файла {file_path}: {e}") from e


def analyze_game(prompt_file: str, pgn_file: str, model: str = "deepseek-r1") -> str:

    prompt_text = load_text(prompt_file)
    pgn_content = load_text(pgn_file)

    full_prompt = f"{prompt_text}\n\nPGN:\n{pgn_content}"
    
    try:
        response = ChatCompletion.create(
            model=model,
            provider=Provider.Blackbox,
            messages=[{"role": "user", "content": full_prompt}],
            stream=False,
        )

        if "</think>" in response:
            result = response.split("</think>", 1)[1].strip()
        else:
            result = response.strip()
            
        return json.loads(result)

    except Exception as e:
        raise RuntimeError(f"Ошибка при вызове модели {model}: {e}") from e
