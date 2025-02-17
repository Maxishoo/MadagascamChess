from g4f import ChatCompletion, Provider
import json
import os

def load_text(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Ошибка при чтении файла {file_path}: {e}") from e

def analyze_game(prompt_file: str, pgn_file: str, model: str = "deepseek-r1", verify: bool = True, max_attempts: int = 4):
    prompt_text = load_text(prompt_file)
    pgn_content = load_text(pgn_file)
    full_prompt = f"{prompt_text}\n\nPGN:\n{pgn_content}"
    
    for attempt in range(max_attempts):
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
            
            if verify:
                return json.loads(result)
            else:
                return result
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"Попытка {attempt+1} не удалась, пробую еще раз...")
            else:
                raise RuntimeError(f"Ошибка при вызове модели {model} после {max_attempts} попыток: {e}") from e

def process_directory(pgn_dir: str, prompt_file: str, model: str = "deepseek-r1", verify: bool = True,
                      output_pgn_file: str = "all_processed.pgn", output_segment_file: str = "all_segments.txt"):
    # Получаем список PGN-файлов в заданной директории
    files = [f for f in os.listdir(pgn_dir) if f.lower().endswith(".pgn")]
    files.sort()
    
    with open(output_pgn_file, "w", encoding="utf-8") as pgn_out, open(output_segment_file, "w", encoding="utf-8") as seg_out:
        for index, filename in enumerate(files):
            pgn_path = os.path.join(pgn_dir, filename)
            print(f"Обработка файла: {pgn_path}")
            try:
                analysis_result = analyze_game(prompt_file, pgn_path, model=model, verify=verify)
            except Exception as e:
                print(f"Ошибка при обработке файла {filename}: {e}")
                continue
            
            pgn_content = load_text(pgn_path)
            pgn_out.write(pgn_content + "\n\n")
            
            seg_out.write(f"{index+1}. {json.dumps(analysis_result, ensure_ascii=False)}\n")
            print(f"Файл {filename} обработан и данные записаны.")
