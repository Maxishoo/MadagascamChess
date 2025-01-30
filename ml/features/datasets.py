import chess
import chess.pgn
import chess.engine
import pandas as pd
import pathlib

from typing import IO
from .extract import extract_features


def read_mark(file: IO, n_moves: int) -> pd.Series:
    line = file.readline()
    if '-' in line:
        marks = line.split('; ')
        for mark in marks:
            left, right = mark.strip().split('-')
            start, start_color = int(left[:-1]), left[-1]
            end, end_color = int(right[:-1]), right[-1]

            before = [0] * ((start - 1) * 2 + (start_color == 'B'))
            middle = [1] * ((end - start + 1) * 2 - (start_color == 'W') - (end_color == 'B'))
            after = [0] * (n_moves - len(before) - len(middle))

            return pd.Series(before + middle + after)
    else:
        return None


# Размеченные игры
def read_dataset(path_to_games: str, path_to_marks: str, path_to_engine: str, save_path: str, log=False):
    engine = chess.engine.SimpleEngine.popen_uci(path_to_engine)
    engine.configure({'Threads': 2})
    engine.configure({'Hash': 1024})

    save_path_obj = pathlib.Path(save_path)
    save_path_dir = save_path_obj.parent
    tmp_path_obj = save_path_dir / 'tmp'
    tmp_path_obj.mkdir(parents=True, exist_ok=True)

    datasets = []
    with open(path_to_games, 'r') as pgn_file, open(path_to_marks, 'r') as marks_file:
        i = 1
        while (game := chess.pgn.read_game(pgn_file)):
            marks = read_mark(marks_file, len(list(game.mainline_moves())))
            if log:
                print(f'[GAME-{i}] Reading...')

            features = extract_features(game, engine, (tmp_path_obj / f'{i}.csv').resolve(), log=log)
            datasets.append(pd.concat([features, marks], axis=1))

            if log:
                print(f'[GAME-{i}] Done!')
            i += 1
    
    engine.close()
    return pd.concat(datasets, axis=0)
