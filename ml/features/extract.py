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


import chess
import chess.engine
import chess.pgn
import pandas as pd
from typing import List

def count_material(board, side):
    material_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    material_count = 0
    for piece in board.piece_map().values():
        if piece.color == side:
            material_count += material_values.get(piece.piece_type, 0)
    return material_count

# Функция для вычисления дистанции до мата
def get_mate_distance(info: List[chess.engine.InfoDict]):
    distances = []
    for i in info:
        if i['score'].relative.is_mate():
            distances.append(i['score'].relative.mate())
    if len(distances) == 0:
        return 0
    return sum(distances) / len(distances)

# Функция для вычисления средней оценки
def get_score(info: List[chess.engine.InfoDict]):
    scores = []
    for i in info:
        scores.append(i['score'].relative.score(mate_score=10_000))
    return sum(scores) / len(scores)

# Функция для получения списка лучших ходов
def get_best_moves(info: List[chess.engine.InfoDict]):
    return [i['pv'][0] for i in info]

def extract_features(game: chess.pgn.Game, engine: chess.engine.SimpleEngine, output_csv_path: str, analyze_detph: int = 20, log: bool = False):
    data = {
        'delta_score': [],
        'deviation_from_pv': [],
        'threats_to_opponent': [],
        'threats_from_opponent': [],
        'legal_moves_diff': [],
        'sacrifice': [],
        'advantage_change': [],
        'mate_distance': [],
        'king_under_attack': [],

        'is_capture': [],
        'is_check': [],
        'is_checkmate': [],
        'cnt_promotion': [],
        'is_used_promotion': [],
        'is_castling': []
    }

    # Анализируем позицию после каждого хода
    board = chess.Board()
    infos = [engine.analyse(board, limit=chess.engine.Limit(depth=analyze_detph), multipv=3)]
    mainline_moves = list(game.mainline_moves())
    for i, move in enumerate(mainline_moves, start=1):
        board.push(move)
        info = engine.analyse(board, limit=chess.engine.Limit(depth=analyze_detph), multipv=3)
        infos.append(info)
        if log:
            print(f'move {i}/{len(mainline_moves)}')
    
    # Вычисляем сами признаки
    board = chess.Board()
    for i, move in enumerate(mainline_moves, start=1):
        # 1. Изменение оценки позции
        delta_score = -get_score(infos[i]) - get_score(infos[i - 1])
        data['delta_score'].append(delta_score)

        # 2. Отклонение от Principal Variation
        deviation_from_pv = 1 if move not in get_best_moves(infos[i - 1]) else 0
        data['deviation_from_pv'].append(deviation_from_pv)

        # 3-4. Угрозы противнику и угрозы от противника
        player_color = board.turn
        opponent_color = not board.turn
        threats_to_opponent = 0
        threats_from_opponent = 0

        board.push(move)
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == opponent_color:
                if board.is_attacked_by(player_color, square):
                    threats_to_opponent += 1
            if piece and piece.color == player_color:
                if board.is_attacked_by(opponent_color, square):
                    threats_from_opponent += 1
        board.pop()

        data['threats_to_opponent'].append(threats_to_opponent)
        data['threats_from_opponent'].append(threats_from_opponent)

        # 5. Изменение количества легальных ходов у противника
        board.turn = not board.turn # Меняем сторону, чтобы посмотреть, какие ходы он впринципе мог бы сейчас сделать
        legal_moves_before = len(list(board.legal_moves))
        board.turn = not board.turn
        board.push(move)
        legal_moves_after = len(list(board.legal_moves))
        board.pop()

        legal_moves_diff = legal_moves_after - legal_moves_before
        data['legal_moves_diff'].append(legal_moves_diff)

        # 6. Жертва материала
        if 'pv' in infos[i]:
            cur_turn = board.turn
            material_before = count_material(board, cur_turn)
            board.push(move)
            best_move_from_opponent = get_best_moves(infos[i])[0]
            board.push(best_move_from_opponent)
            material_after = count_material(board, cur_turn)
            board.pop()
            board.pop()

            data['sacrifice'] = material_after - material_before
        else:
            data['sacrifice'] = 0

        # 7. Смена преимущества
        data['advantage_change'].append(1 if get_score(infos[i - 1]) * get_score(infos[i]) > 0 else 0)

        # 8. Близость к мату
        data['mate_distance'].append(-get_mate_distance(infos[i]))

        # 9. Уязвимость короля противника
        board.push(move)
        king_square = board.king(board.turn)
        data['king_under_attack'].append(1 if board.is_attacked_by(not board.turn, king_square) else 0)
        board.pop()

        # 10-12. Тактические угрозы и приёмы
        data['is_capture'].append(board.is_capture(move))
        board.push(move)
        data['is_check'].append(board.is_check())
        data['is_checkmate'].append(board.is_checkmate())
        board.pop()
        data['cnt_promotion'].append(sum(1 for mv in board.legal_moves if mv.promotion) // 4)
        data['is_used_promotion'].append(move.promotion is not None)
        data['is_castling'].append(board.is_castling(move))
    
        # Делаем ход и переходим на следующую итерацию
        board.push(move)
    
    return pd.DataFrame(data)
