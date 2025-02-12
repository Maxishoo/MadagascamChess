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
        self.model = ChatClient(api_key=api_key, model='mistralai/mistral-small-24b-instruct-2501:free')

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
        raw_description = self.make_description()

        def generate_user_promt(n_moves):
            intro = (
                'Тебе будет дано описание доски и саммари последних событий, '
                'которые привели к этому состоянию, а также {} полных хода с кратким описанием. '
                'Твоя задача состоит из трёх шагов:\n'.format(n_moves)
            )
            
            step_1 = (
                '1. Дать более подробное описание каждого хода, отвечая на вопросы:\n'
                '   - Является ли этот ход хорошим?\n'
                '   - Почему игрок сделал этот ход?\n'
                '   - Пытается ли игрок выполнить тактический приём?\n'
            )
            
            step_2 = (
                '2. Описать доску, сделав упор на анализе ключевых фигур.\n'
            )
            
            step_3 = (
                '3. Написать краткое саммари указанных ходов. Если ты видишь незаконченную связку, '
                'укажи это. Если ничего особенного не происходило, так и напиши.\n\n'
            )
            
            response_format = (
                'Итак, формат твоего ответа должен быть таким (Обязательно указывай теги в угловых скобках):\n'
                '1. <АНАЛИЗ ХОДОВ> ... </АНАЛИЗ ХОДОВ> # Описание ходов в свободной форме. '
                'Проведи весь необходимый анализ без ограничений.\n'
                '2. <ОПИСАНИЕ ДОСКИ> ... </ОПИСАНИЕ ДОСКИ> # Расскажи, что происходит на доске, '
                'расскажи какой игрок обладает преимуществом и почему.\n'
                '3. <САММАРИ> ... </САММАРИ> # Расскажи о начатых тактических приёмах, интересных '
                'действиях и всё, что поможет для дальнейшего анализа.\n'
            )
            
            return ''.join([intro, step_1, step_2, step_3, response_format])
    
        system_promt = (
            'Ты - специалист в области анализа шахматных игр. Ты прекрасно подмечаешь '
            'красивые связки и тактические приёмы, способен выделить интересные моменты '
            'и ярко, но лаконично прокомментировать их.'
        )

        user_promt = generate_user_promt(n_full_moves)

        def generate_information(board: chess.Board, description: str, summary: str):
            return (
                f'<ДОСКА> {board} </ДОСКА>'
                f'<ОПИСАНИЕ ДОСКИ> {description} </ОПИСАНИЕ ДОСКИ>\n'
                f'<САММАРИ> {summary} </САММАРИ>\n'
            )

        board = chess.Board()
        last_answer = generate_information(board, 'Обычная стартовая доска', 'Игра началась')
        moves_description = ''

        advanced_description = f'{last_answer}\n'
        for i, move in enumerate(self.game.mainline_moves(), start=1):
            moves_description += describe_move(board, move) + '\n'
            board.push(move)

            if i % (2 * n_full_moves) == 0:
                completion = self.model.create_completion([
                    self.model.make_system_promt(system_promt),
                    self.model.make_user_promt(f'{last_answer}\n{moves_description}')
                ])['content']

                print('[LOG] completion =', completion, '[/LOG]')

                extract_desc_promt = 'Перепиши текст, связанный с описанием доски. Вероятно, он обрамлён тегами <ОПИСАНИЕ ДОСКИ> и  </ОПИСАНИЕ ДОСКИ>. Лишние теги следует убрать.'
                board_description = self.model.create_completion([
                    self.model.make_user_promt(f'{extract_desc_promt}\n{completion}')
                ])['content']

                print('[LOG] board_description =', board_description, '[/LOG]')

                extract_sum_promt = 'Перепиши текст, связанный с саммари ходов. Вероятно, он обрамлён тегами <САММАРИ> и </САММАРИ>. Лишние теги следует убрать.'
                summary = self.model.create_completion([
                    self.model.make_user_promt(f'{extract_sum_promt}\n{completion}')
                ])['content']

                print('[LOG] summary =', summary, '[/LOG]')

                last_answer = generate_information(board, board_description, summary)
                print('[LOG]', last_answer, '[/LOG]')
                advanced_description += f'{last_answer}\n'
                moves_description = ''
        
        return advanced_description