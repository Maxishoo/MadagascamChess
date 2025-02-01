import chess
import chess.pgn
import chess.engine
import pandas as pd
import os

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
def read_dataset(path_to_games: str, path_to_engine: str, save_path: str, offset: int = None, n_read: int = 10, path_to_marks: str = None, analyze_detph: int = 16, log=False):
    engine = chess.engine.SimpleEngine.popen_uci(path_to_engine)
    # engine.configure({'Threads': 1})
    # engine.configure({'Hash': 512})

    tmp_path = f'{save_path}/tmp'
    os.makedirs(tmp_path, exist_ok=True)

    if offset is None:
        offset = 0
        for item in os.listdir(tmp_path):
            if os.path.isfile(os.path.join(tmp_path, item)):
                offset = max(offset, int(item.split('.')[0]))

    marks_file = None
    datasets = []
    with open(path_to_games, 'r') as pgn_file:
        if path_to_marks is not None:
            marks_file = open(path_to_marks, 'r')

        i = 0
        while (game := chess.pgn.read_game(pgn_file)):
            i += 1
            if i - offset > n_read:
                break
            if i <= offset:
                continue

            if log:
                print(f'[GAME-{i}] Reading...')

            cur_save_path = os.path.join(tmp_path, f'{i}.csv')
            features = extract_features(game, engine, cur_save_path, log=log, analyze_detph=analyze_detph)
            if marks_file is not None:
                marks = read_mark(marks_file, features.shape[0])
                cur_train = pd.concat([features, marks], axis=1)
            else:
                cur_train = features
            cur_train.to_csv(cur_save_path, index=False)
            datasets.append(cur_train)

            if log:
                print(f'[GAME-{i}] Done!')
        
        if marks_file is not None:
            marks_file.close()
    
    engine.close()
    return pd.concat(datasets, axis=0)
