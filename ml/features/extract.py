import chess
import chess.pgn
import chess.engine
import pandas as pd


def mean(nums):
    return sum(nums) / len(nums)


def varinace(nums):
    average = mean(nums)
    result = sum([(num - average) ** 2 for num in nums])
    return result


def count_threats(board: chess.Board, color: chess.Color):
    opponent = not color

    threats_from_opponent = 0

    # Считаем угрозы от противника
    for square in chess.SQUARES:
        if board.piece_at(square) and board.piece_at(square).color == color:
            attackers = board.attackers(opponent, square)  # Фигуры противника, атакующие клетку
            threats_from_opponent += len(attackers)

    return threats_from_opponent


def extract_features(game: chess.pgn.Game, engine: chess.engine.SimpleEngine, save_path: str, link: str = None, log: bool = False):
    features = {
        'link': [],
        'turn': [],
        'best_moves_score_dispresion': [],
        'moves_to_mate': [],
        'score_change_after_move': [],
        'seldepth_depth_ratio': [],
        'consecutive_score_increase': [],
        'threats_from_opponent': [],
        'threat_to_opponent': [],
        'depth_score_dispersion': []
    }

    MATE_VALUE = 1000

    def get_score(info):
        score = info['score']
        return score.pov(score.turn)

    if link is None and 'Site' in game.headers:
        link = game.headers['Site']

    board = chess.Board()
    moves = list(game.mainline_moves())
    cnt_increasing_score_white = 0
    cnt_increasing_score_black = 0
    infos = engine.analyse(board, chess.engine.Limit(depth=20), multipv=5)
    last_score_white = mean([get_score(info).score(mate_score=MATE_VALUE) for info in infos])
    last_score_black = -mean([get_score(info).score(mate_score=MATE_VALUE) for info in infos])

    for i, move in enumerate(moves):
        if log:
            print(f'[pre] move: {i}/{len(moves)}')

        cur_turn = board.turn

        features['link'].append(link)
        features['turn'].append(cur_turn)

        dif_depth_scores = []
        for depth in [5, 10, 15, 20, 25]:
            info = engine.analyse(board, chess.engine.Limit(depth=depth))
            dif_depth_scores.append(get_score(info).score(mate_score=MATE_VALUE))

        features['depth_score_dispersion'].append(varinace(dif_depth_scores))

        best_moves_scores = []
        mate_in = float('inf')
        depths = []
        seldetphs = []
        for info in infos:
            depths.append(info['depth'])
            seldetphs.append(info['seldepth'])

            copied_board = board.copy()
            copied_board.push(info['pv'][0])

            info = engine.analyse(copied_board, chess.engine.Limit(depth=20))
            score = get_score(info)
            best_moves_scores.append(score.score(mate_score=MATE_VALUE))

            if score.is_mate():
                mate_in = min(mate_in, score.mate())

        if log:
            print(f'[post] move: {i}/{len(moves)}')

        features['seldepth_depth_ratio'].append(mean(seldetphs) / mean(depths))
        features['best_moves_score_dispresion'].append(varinace(best_moves_scores))
        features['moves_to_mate'].append(mate_in if mate_in < float('inf') else 0)
        features['threats_from_opponent'].append(count_threats(board.copy(), board.turn))

        board.push(move)
        infos = engine.analyse(board, chess.engine.Limit(depth=20), multipv=5)
        cur_score = mean([get_score(info).score(mate_score=MATE_VALUE) for info in infos])

        features['threat_to_opponent'].append(count_threats(board.copy(), board.turn))
        features['score_change_after_move'].append(cur_score - (last_score_white if cur_turn == chess.WHITE else last_score_black))

        if cur_turn == chess.WHITE:
            if cur_score > last_score_white:
                cnt_increasing_score_white += 1
            else:
                cnt_increasing_score_white = 0
            last_score_white = cur_score
        else:
            if cur_score > last_score_black:
                cnt_increasing_score_black += 1
            else:
                cnt_increasing_score_black = 0
            last_score_black = cur_score

        features['consecutive_score_increase'].append(cnt_increasing_score_white if cur_turn == chess.WHITE else cnt_increasing_score_black)

    features_df = pd.DataFrame(features)
    features_df.to_csv(save_path, index=False)

    return features_df
