from chess_analysis import analyze_game

prompt_file = "prompt2.txt"
pgn_file = "event1.pgn"

result_alt = analyze_game(prompt_file, pgn_file, model="deepseek-r1")
print("Ответ модели:")
print(result_alt)
