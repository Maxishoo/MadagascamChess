import chess
import chess.pgn
import chess.engine
import pandas as pd
import pathlib

from typing import IO
from .extract import extract_features


def read_mark(file: IO, n_moves: int) -> pd.Series:
    line = file.readline()

    def mark_to_idx(mark: str):
        number, letter = int(mark[:-1]), mark[-1]
        return (number - 1) * 2 + int(letter == 'B')

    if '-' in line:
        marks = line.split('; ')
        answer = [0] * n_moves
        for mark in marks:
            left, right = mark.strip().split('-')
            il, ir = mark_to_idx(left), mark_to_idx(right) + 1
            answer = answer[:il] + [1] * (ir - il) + answer[ir:]
        return pd.Series(answer, name='target')
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
            if log:
                print(f'[GAME-{i}] Reading...')

            cur_save_path = (tmp_path_obj / f'{i}.csv').resolve()
            features = extract_features(game, engine, cur_save_path, log=log, analyze_detph=16)
            marks = read_mark(marks_file, features.shape[0])
            cur_train = pd.concat([features, marks], axis=1)
            cur_train.to_csv(cur_save_path, index=False)
            datasets.append(cur_train)

            if log:
                print(f'[GAME-{i}] Done!')
            i += 1
    
    engine.close()
    return pd.concat(datasets, axis=0)
