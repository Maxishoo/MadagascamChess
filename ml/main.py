import features.datasets as ds

ds.read_dataset(
    path_to_games='marked_up/games.pgn',
    path_to_marks='marked_up/markers.txt',
    path_to_engine='stockfish/stockfish-ubuntu-x86-64-sse41-popcnt',
    save_path='tmp/markedup_dataset.csv',
    log=True
)
