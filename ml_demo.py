from ml.ProcessPGN import ProcessPGN

process = ProcessPGN(path_to_pgn='C:/Users/matvey/Documents/chess_data/example_game.pgn')

# comments = process.make_description()
# print(comments)

advanced_comments = process.make_advanced_description()
print(advanced_comments)