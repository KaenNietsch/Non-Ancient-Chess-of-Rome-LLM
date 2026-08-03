import chess
import time
import os

from bot_local import LocalBot
from bot_llm import LLMBot


def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def _board_to_display(board: chess.Board) -> str:
    lines = board.unicode().split("\n")
    border = "  " + "+" + "---+" * 8
    result = [border]
    for i, line in enumerate(lines):
        row_label = 8 - i
        row_str = str(row_label) + " |"
        parts = line.split(" ")
        for p in parts:
            row_str += " " + (p if p != "." else " ") + "|"
        result.append(row_str)
        result.append(border)
    result.append("    a   b   c   d   e   f   g   h")
    return "\n".join(result)


def _player_name(player) -> str:
    if isinstance(player, LocalBot):
        color_name = "Beyaz" if player.color == chess.WHITE else "Siyah"
        return f"LocalBot ({color_name})"
    elif isinstance(player, LLMBot):
        color_name = "Beyaz" if player.color == chess.WHITE else "Siyah"
        return f"LLMBot [{player.model_name}] ({color_name})"
    else:
        return "Bilinmeyen Oyuncu"


def play_game(white_player, black_player, delay: float = 1.0):
    board = chess.Board()

    white_name = _player_name(white_player)
    black_name = _player_name(black_player)

    move_count = 0

    while not board.is_game_over():
        _clear_screen()

        if board.turn == chess.WHITE:
            current = white_player
            name = white_name
        else:
            current = black_player
            name = black_name

        move_count += 1

        turn_str = "Beyaz" if board.turn == chess.WHITE else "Siyah"

        print("================== SATRANC SIMULATORU ==================")
        print(f" Hamle: {move_count}.  Sirayla oynayan: {turn_str}")
        print(f" Oyuncu: {name}")
        print()
        print(f" FEN: {board.fen()}")
        print()
        print(_board_to_display(board))
        print()

        try:
            move = current.get_move(board)
        except Exception as e:
            print(f"  [!] Hamle alinamadi: {e}")
            if board.turn == chess.WHITE:
                print(f"  [!] Siyah kazandi (beyaz hata yapti): {black_name}")
            else:
                print(f"  [!] Beyaz kazandi (siyah hata yapti): {white_name}")
            return

        if move is None:
            break

        san_move = board.san(move)
        board.push(move)

        print(f"\n  {turn_str} oynandi: {san_move}  ({move.uci()})")
        time.sleep(delay)

    _clear_screen()
    print("  ========== OYUN SONU ==========")
    print()
    print(_board_to_display(board))
    print()

    outcome = board.outcome()
    if outcome is None:
        print("  Oyun beklenmedik sekilde sonlandi.")
        return

    if outcome.winner is None:
        print(f"  Sonuc: Beraberlik! ({outcome.termination})")
    elif outcome.winner == chess.WHITE:
        print(f"  Beyaz kazandi! ({outcome.termination})")
    else:
        print(f"  Siyah kazandi! ({outcome.termination})")

    print()
    print(f"  Sonuc: {board.result()}")
    print(f"  Son FEN: {board.fen()}")