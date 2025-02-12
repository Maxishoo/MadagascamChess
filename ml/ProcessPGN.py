import chess
import chess.pgn
from . import api_key
from .ChatClient import ChatClient


def square_to_en_name(board: chess.Board, square: chess.Square):
    piece_type = board.piece_at(square).piece_type
    name = chess.piece_name(piece_type)
    return name


def find_targets(board: chess.Board, square: chess.Square):
    targets = set()
    for square in board.attacks(square):
        if board.piece_at(square) is not None:
            targets.add(square)
    return targets


def find_threats(board: chess.Board, square: chess.Square):
    color = board.piece_at(square).color
    return board.attackers(color, square)


def describe_move(board: chess.Board, move: chess.Move):
    genitive_case = {
        'king': 'короля',
        'queen': 'ферзя',
        'rook': 'ладьи',
        'bishop': 'слона',
        'knight': 'коня',
        'pawn': 'пешки'
    }

    dative_case = {
        'king': 'королю',
        'queen': 'ферзю',
        'rook': 'ладье',
        'bishop': 'слону',
        'knight': 'коню',
        'pawn': 'пешке'
    }

    accusative_case = {
        'king': 'короля',
        'queen': 'ферзя',
        'rook': 'ладью',
        'bishop': 'слона',
        'knight': 'коня',
        'pawn': 'пешку'
    }

    instrumental_case = {
        'king': 'королем',
        'queen': 'ферзем',
        'rook': 'ладьей',
        'bishop': 'слоном',
        'knight': 'конем',
        'pawn': 'пешкой'
    }

    move_to = chess.square_name(move.to_square)
    turn = 'Белые' if board.turn == chess.WHITE else 'Черные'
    en_piece_name = square_to_en_name(board, move.from_square)

    description = f'{turn} делают ход {instrumental_case[en_piece_name]} на {move_to}'
    if board.is_castling(move):
        description += ' (рокировка)'

    # Проверяем событие "съедая ...(accusative)"
    if board.is_capture(move):
        captured_name = accusative_case[square_to_en_name(board, move.to_square)]
        position = chess.square_name(move.to_square)
        description += '; съедая ' + f'{captured_name} на {position}'

    # Проверяем событие "уходя от атаки ...(genitive)"
    ru_attackers_names = []
    for attacker_square in find_threats(board, move.from_square):
        attacker_name = genitive_case[square_to_en_name(board, attacker_square)]
        position = chess.square_name(attacker_square)
        ru_attackers_names.append(f'{attacker_name} на {position}')

    if ru_attackers_names:
        description += '; уходя от атаки ' + ', '.join(ru_attackers_names) 

    # Проверяем событие "угрожая ...(dative)"
    ru_attacked_names = []
    board.push(move)
    for attacked_square in find_targets(board, move.to_square):
        attacked_name = dative_case[square_to_en_name(board, attacked_square)]
        position = chess.square_name(attacked_square)
        ru_attacked_names.append(f'{attacked_name} на {position}')
    board.pop()
    if ru_attacked_names:
        description += '; угрожая ' + ', '.join(ru_attacked_names)

    return description


class ProcessPGN:
    def __init__(self, path_to_pgn: str):
        with open(path_to_pgn, 'r') as pgn_file:
            self.game = chess.pgn.read_game(pgn_file)
        self.model = ChatClient(api_key=api_key, model='meta-llama/llama-3.3-70b-instruct:free')

    def make_description(self):
        # def describe_board(board: chess.Board):
        #     description = 'Ситуация на доске следующая:\n'
        #     for piece_type in chess.PIECE_TYPES:
        #         white_squares = board.pieces(piece_type, chess.WHITE)
        #         black_squares = board.pieces(piece_type, chess.BLACK)

        #         description += '1. У белых:\n'
        #         for i, square in enumerate(white_squares, start=1):
        #             pass

        # n_full_moves = 3
        description = ''

        board = chess.Board()
        for i, move in enumerate(self.game.mainline_moves(), start=1):
            description += describe_move(board, move) + '\n'
            board.push(move)

            # if i % (n_full_moves * 2) == 0:
            #     description += describe_board(board) + '\n'
    
        return description
    
    def make_advanced_description(self):
        n_full_moves = 3

        def generate_user_prompt(n_moves):
            intro = (
                'Тебе будет дано описание доски и саммари последних событий, '
                f'которые привели к этому состоянию, а также {n_moves} полных хода с кратким описанием. '
                'Твоя задача состоит из трёх шагов:\n'
            )

            step_1 = (
                '1. Проанализируй каждый ход подробно, отвечая на следующие вопросы:\n'
                '   - Является ли этот ход хорошим?\n'
                '   - Почему игрок сделал этот ход?\n'
                '   - Пытается ли игрок выполнить тактический приём?\n'
            )

            step_2 = (
                '2. Опиши текущее состояние доски, сделав акцент на ключевых фигурах и их взаимодействии. Не надо приводить вид доски\n'
            )

            step_3 = (
                '3. Напиши краткое саммари указанных ходов. Если ты видишь незаконченную связку, '
                'укажи это. Если ничего особенного не происходило, так и напиши.\n\n'
            )

            response_format = (
                'Формат твоего ответа должен быть таким:\n'
                '<АНАЛИЗ ХОДОВ> ... </АНАЛИЗ ХОДОВ>\n'
                '<ОПИСАНИЕ ДОСКИ> ... </ОПИСАНИЕ ДОСКИ>\n'
                '<САММАРИ> ... </САММАРИ>\n'
            )

            return ''.join([intro, step_1, step_2, step_3, response_format])

        system_prompt = (
            'Ты - эксперт по анализу шахматных партий. Ты умеешь находить тактические идеи, '
            'выделять важные моменты игры и предоставлять четкие комментарии. '
            'Твой стиль — яркий, но лаконичный.'
        )

        user_prompt = generate_user_prompt(n_full_moves)

        def generate_information(
                description: str, summary: str):
            return (
                f'<ОПИСАНИЕ ДОСКИ> {description} </ОПИСАНИЕ ДОСКИ>\n'
                f'<САММАРИ> {summary} </САММАРИ>\n'
            )

        def extract_tags(completion):
            """
            Извлекает содержимое тегов из ответа модели.
            Возвращает кортеж (analysis, board_description, summary) или None, если теги отсутствуют.
            """
            try:
                start_analysis = completion.index('<АНАЛИЗ ХОДОВ>') + len('<АНАЛИЗ ХОДОВ>')
                end_analysis = completion.index('</АНАЛИЗ ХОДОВ>')
                analysis = completion[start_analysis:end_analysis].strip()

                start_board = completion.index('<ОПИСАНИЕ ДОСКИ>') + len('<ОПИСАНИЕ ДОСКИ>')
                end_board = completion.index('</ОПИСАНИЕ ДОСКИ>')
                board_description = completion[start_board:end_board].strip()

                start_summary = completion.index('<САММАРИ>') + len('<САММАРИ>')
                end_summary = completion.index('</САММАРИ>')
                summary = completion[start_summary:end_summary].strip()

                return analysis, board_description, summary
            except ValueError:
                return None

        board = chess.Board()
        last_answer = generate_information('Обычная стартовая доска', 'Игра началась')
        moves_description = ''
        advanced_description = f'{last_answer}\n'

        for i, move in enumerate(self.game.mainline_moves(), start=1):
            moves_description += describe_move(board, move) + '\n'
            board.push(move)

            if i % (2 * n_full_moves) == 0:
                while True:
                    # Объединяем все данные для одного запроса
                    input_data = f'{last_answer}\n{moves_description}'
                    completion = self.model.create_completion([
                        self.model.make_system_prompt(system_prompt),
                        self.model.make_user_prompt(user_prompt),
                        self.model.make_user_prompt(input_data)
                    ])['content']

                    # Пытаемся извлечь теги
                    result = extract_tags(completion)

                    if result:  # Если все теги найдены
                        print('[LOG] completion =', completion, '[/LOG]')
                        analysis, board_description, summary = result
                        break  # Выходим из цикла
                    else:
                        print('[INFO] Ответ модели не содержит всех необходимых тегов. Повторный запрос...')
                        continue  # Повторяем запрос

                # Формируем последнее описание
                last_answer = generate_information(board_description, summary)
                print('[LOG] last_answer =', last_answer, '[/LOG]')
                advanced_description += f'{last_answer}\n'
                moves_description = ''

        return advanced_description