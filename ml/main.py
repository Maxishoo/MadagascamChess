import features.datasets as ds
import pandas as pd

dataset = ds.read_dataset(
    path_to_games='/home/matvey/chess_data/lichess_db_standard_rated_2014-07.pgn',
    # path_to_games='features/tmp_data/example_data.pgn',
    # path_to_marks='marked_up/markers.txt',
    path_to_engine='stockfish/stockfish-ubuntu-x86-64-avx2',
    save_path='/home/matvey/chess_data',
    n_read=100,
    analyze_detph=16,
    log=True,
)

# dataset.to_csv('train.csv', index=False)