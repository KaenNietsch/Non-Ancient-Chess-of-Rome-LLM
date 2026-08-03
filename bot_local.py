import chess
import random


class LocalBot:
    """Full-width chess engine using negamax + alpha-beta + quiescence.

    Scans every legal move (captures, castling, en passant, promotion all
    come from python-chess's legal_moves) and picks the move that maximizes
    the score for its side, seeing captures at the search horizon via a
    capture-only quiescence search so it never blunders hanging material.
    """

    def __init__(self, color: chess.Color, depth: int = 3):
        self.color = color
        self.depth = depth
        self._history = {}

    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000,
    }

    PAWN_TABLE = [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -20, -20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0,
    ]

    KNIGHT_TABLE = [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -30, -20, -20, -30, -40, -50,
    ]

    BISHOP_TABLE = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 5, 10, 10, 10, 10, 5, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20,
    ]

    ROOK_TABLE = [
        0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, 10, 10, 10, 10, 5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        0, 0, 0, 5, 5, 0, 0, 0,
    ]

    QUEEN_TABLE = [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, -10, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20,
    ]

    KING_MIDDLEGAME_TABLE = [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20, 20, 0, 0, 0, 0, 20, 20,
        20, 30, 10, 0, 0, 10, 30, 20,
    ]

    KING_ENDGAME_TABLE = [
        -50, -40, -30, -20, -20, -30, -40, -50,
        -30, -20, -10, 0, 0, -10, -20, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -30, 0, 0, 0, 0, -30, -30,
        -50, -30, -30, -30, -30, -30, -30, -50,
    ]

    PIECE_TABLES = {
        chess.PAWN: PAWN_TABLE,
        chess.KNIGHT: KNIGHT_TABLE,
        chess.BISHOP: BISHOP_TABLE,
        chess.ROOK: ROOK_TABLE,
        chess.QUEEN: QUEEN_TABLE,
        chess.KING: KING_MIDDLEGAME_TABLE,
    }

    # Small book so the opening looks natural instead of h4 etc.
    OPENING_BOOK = {
        (): ["e2e4", "d2d4"],
        ("e2e4",): ["e7e5", "c7c5", "e7e6"],
        ("d2d4",): ["d7d5", "g8f6"],
        ("e2e4", "e7e5"): ["g1f3", "b1c3", "f1c4"],
        ("d2d4", "d7d5"): ["c2c4", "g1f3"],
        ("e2e4", "c7c5"): ["g1f3", "b1c3"],
        ("e2e4", "e7e6"): ["d2d4"],
        ("e2e4", "e7e5", "g1f3"): ["b8c6", "g8f6"],
        ("d2d4", "g8f6"): ["c2c4", "g1f3", "e2e3"],
    }

    def _is_endgame(self, board: chess.Board) -> bool:
        queens = board.pieces(chess.QUEEN, chess.WHITE) | board.pieces(chess.QUEEN, chess.BLACK)
        total_material = 0
        for piece_type in [chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
            total_material += len(board.pieces(piece_type, chess.WHITE)) * self.PIECE_VALUES[piece_type]
            total_material += len(board.pieces(piece_type, chess.BLACK)) * self.PIECE_VALUES[piece_type]
        return len(queens) == 0 and total_material < 2600

    def evaluate_board(self, board: chess.Board) -> float:
        """Static evaluation from the perspective of the side to move
        (positive = good for board.turn). Tiles the pieces, adds piece-square
        bonuses, and bonuses for castling rights / king safety so the engine
        actually castles and stops shuffling pawns."""
        if board.is_checkmate():
            return -99999 if board.turn == chess.WHITE else 99999
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0

        endgame = self._is_endgame(board)
        score = 0.0

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue

            value = self.PIECE_VALUES[piece.piece_type]
            sq_index = square if piece.color == chess.WHITE else (7 - square // 8) * 8 + (square % 8)

            if piece.piece_type == chess.KING:
                if endgame:
                    pos_bonus = self.KING_ENDGAME_TABLE[sq_index]
                else:
                    pos_bonus = self.KING_MIDDLEGAME_TABLE[sq_index]
            else:
                table = self.PIECE_TABLES.get(piece.piece_type)
                if table:
                    pos_bonus = table[sq_index]
                else:
                    pos_bonus = 0

            total = value + pos_bonus
            if piece.color == chess.WHITE:
                score += total
            else:
                score -= total

        # King safety: reward a castled king. (A naive "+has_castling_rights"
        # bonus backfires because castling removes the right, so we score the
        # actual king position instead. The piece-square tables already nudge
        # an uncastled king away from the centre.)
        for color in (chess.WHITE, chess.BLACK):
            king_sq = board.king(color)
            if king_sq is None:
                continue
            file_ = chess.square_file(king_sq)
            rank = chess.square_rank(king_sq)
            if color == chess.WHITE and rank == 0:
                if file_ == 6:      # O-O: g1
                    score += 70
                elif file_ == 2:    # O-O-O: c1
                    score += 60
            elif color == chess.BLACK and rank == 7:
                if file_ == 6:      # O-O: g8
                    score -= 70
                elif file_ == 2:    # O-O-O: c8
                    score -= 60

        return score if board.turn == chess.WHITE else -score

    def _order_moves(self, board: chess.Board, moves: list) -> list:
        """MVV-LVA move ordering so good captures are examined first."""
        def key(move):
            s = 0
            if board.is_capture(move) or board.is_en_passant(move):
                victim = board.piece_at(move.to_square)
                aggressor = board.piece_at(move.from_square)
                s += 10 * self.PIECE_VALUES.get(victim.piece_type if victim else chess.PAWN, 0)
                s -= self.PIECE_VALUES.get(aggressor.piece_type if aggressor else 0, 0) // 10
            if move.promotion:
                s += self.PIECE_VALUES[chess.QUEEN]
            if board.gives_check(move):
                s += 35
            h = self._history.get(move, 0)
            return s + h
        return sorted(moves, key=key, reverse=True)

    def _quiescence(self, board: chess.Board, alpha: float, beta: float) -> float:
        """Search only captures/en-passant/promotions after the horizon so the
        engine sees hanging pieces and recaptures instead of trading down
        blind."""
        stand_pat = self.evaluate_board(board)
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        captures = [m for m in board.legal_moves
                    if board.is_capture(m) or board.is_en_passant(m) or m.promotion]
        for move in self._order_moves(board, captures):
            board.push(move)
            score = -self._negamax(board, 0, -beta, -alpha)
            board.pop()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def _negamax(self, board: chess.Board, depth: int, alpha: float, beta: float) -> float:
        if board.is_checkmate():
            return -99999 - depth
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        if depth == 0:
            return self._quiescence(board, alpha, beta)

        best = -float("inf")
        for move in self._order_moves(board, list(board.legal_moves)):
            board.push(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha)
            board.pop()
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                self._history[move] = self._history.get(move, 0) + depth * depth
                break
        return best

    def get_move(self, board: chess.Board) -> chess.Move:
        return self.get_best_move(board, self.depth)

    def get_best_move(self, board: chess.Board, depth: int = 3) -> chess.Move:
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        # Natural opening moves from a small book. Only use it when the game
        # actually started from the standard position (move_stack empty), or
        # when the exact book line has been played; this stops the book from
        # firing on arbitrary test positions.
        hist = tuple(m.uci() for m in board.move_stack)
        if hist and hist in self.OPENING_BOOK:
            candidates = []
            for uci in self.OPENING_BOOK[hist]:
                try:
                    m = chess.Move.from_uci(uci)
                except ValueError:
                    continue
                if m in legal_moves:
                    candidates.append(m)
            if candidates:
                return random.choice(candidates)
        if not hist and board.fen() == chess.Board().fen():
            book = self.OPENING_BOOK[()]
            candidates = []
            for uci in book:
                m = chess.Move.from_uci(uci)
                if m in legal_moves:
                    candidates.append(m)
            if candidates:
                return random.choice(candidates)

        best_move = legal_moves[0]
        best_eval = -float("inf")
        alpha = -float("inf")
        beta = float("inf")

        for move in self._order_moves(board, legal_moves):
            board.push(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha)
            board.pop()

            if score > best_eval:
                best_eval = score
                best_move = move
            if score > alpha:
                alpha = score

        return best_move
