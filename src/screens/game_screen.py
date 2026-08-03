import chess
import time
import threading

from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DGG
from panda3d.core import TextNode

from .base_screen import BaseScreen
from bot_local import LocalBot
from bot_llm import LLMBot


class GameScreen(BaseScreen):
    def __init__(self, base):
        super().__init__(base)
        self.board = chess.Board()
        self.white_player = None
        self.black_player = None
        self.is_playing = False
        self.play_thread = None
        self.is_thinking = False
        self._thinking_start_time = 0

    def start_game(self, white_player, black_player):
        from src.stats_tracker import StatsTracker
        self.white_player = white_player
        self.black_player = black_player
        self.board = chess.Board()

        wn = self.player_name(white_player)
        bn = self.player_name(black_player)
        self.tracker = StatsTracker(wn, bn, "game")

        self._create_hud()
        self.base.chess_renderer.update_from_board(self.board)
        if hasattr(self.base, "_static_board_camera"):
            self.base._static_board_camera()
        self.is_playing = True
        self._last_move_text = ""
        self.play_thread = threading.Thread(target=self._game_loop, daemon=True)
        self.play_thread.start()
        self.base.taskMgr.add(self._update_hud_task, "updateHud")

    def _create_hud(self):
        self.hud_frame = DirectFrame(
            parent=self.base.aspect2d,
            frameSize=(-1.3, 1.3, -1.0, 1.0),
            frameColor=(0, 0, 0, 0),
        )
        
        # Elegant thin gold-bordered top bar
        self.top_bar_border = DirectFrame(
            parent=self.hud_frame,
            frameSize=(-1.3, 1.3, 0.88, 1.0),
            frameColor=(0.85, 0.75, 0.45, 1), # Gold border
            relief=DGG.FLAT
        )
        self.top_bar_inner = DirectFrame(
            parent=self.top_bar_border,
            frameSize=(-1.3, 1.3, 0.89, 1.0),
            frameColor=(0.15, 0.12, 0.1, 1), # Dark warm brown/gray
            relief=DGG.FLAT
        )

        self.hud_last = DirectLabel(
            parent=self.top_bar_inner,
            text="Last Move: -",
            pos=(-1.25, 0, 0.925),
            scale=0.05,
            text_fg=(0.95, 0.95, 0.95, 1),
            text_align=TextNode.ALeft,
            text_font=self.base.font_regular,
            relief=None,
        )

        self.hud_turn = DirectLabel(
            parent=self.top_bar_inner,
            text="White to move",
            pos=(1.25, 0, 0.925),
            scale=0.05,
            text_fg=(0.95, 0.95, 0.95, 1),
            text_align=TextNode.ARight,
            text_font=self.base.font_regular,
            relief=None,
        )

        self.hud_center = DirectLabel(
            parent=self.top_bar_inner,
            text="",
            pos=(0, 0, 0.925),
            scale=0.05,
            text_fg=(1.0, 0.85, 0.35, 1), # Gold color for emphasis
            text_align=TextNode.ACenter,
            text_font=self.base.font_regular,
            relief=None,
        )

    def _update_hud_task(self, task):
        if not self.is_playing:
            return task.done
            
        turn_str = "White to move" if self.board.turn == chess.WHITE else "Black to move"
        if self.hud_turn["text"] != turn_str:
            self.hud_turn["text"] = turn_str
            
        if self._last_move_text:
            last_str = f"Last Move: {self._last_move_text}"
            if self.hud_last["text"] != last_str:
                self.hud_last["text"] = last_str
                
        if self.is_thinking:
            elapsed = time.time() - self._thinking_start_time
            dots = "." * (int(elapsed * 3) % 4)
            thinking_str = f"Thinking{dots}"
            if self.hud_center["text"] != thinking_str:
                self.hud_center["text"] = thinking_str
        else:
            if self.hud_center["text"] != "":
                self.hud_center["text"] = ""
                
        return task.cont

    def player_name(self, player):
        if isinstance(player, LocalBot):
            return "LocalBot"
        elif isinstance(player, LLMBot):
            return f"LLM [{getattr(player, 'model_name', '?')}]"
        return "Unknown"

    def _game_loop(self):
        while self.is_playing and not self.board.is_game_over():
            is_white_turn = (self.board.turn == chess.WHITE)
            if hasattr(self.base, "move_camera_to_side"):
                self.base.move_camera_to_side(is_white=is_white_turn)

            current = self.white_player if is_white_turn else self.black_player
            move_start = time.time()
            
            self.is_thinking = isinstance(current, LLMBot)
            if self.is_thinking:
                self._thinking_start_time = time.time()

            try:
                move = current.get_move(self.board)
            except Exception as e:
                print(f"[!] Error getting move: {e}")
                move = None
            finally:
                self.is_thinking = False

            if move is not None and move not in self.board.legal_moves:
                print(f"[!] Illegal move returned: {move}. Using fallback.")
                import random
                legal_moves = list(self.board.legal_moves)
                move = random.choice(legal_moves) if legal_moves else None

            elapsed = (time.time() - move_start) * 1000

            if move is None:
                break

            from_file = chess.square_file(move.from_square)
            from_rank = chess.square_rank(move.from_square)
            to_file = chess.square_file(move.to_square)
            to_rank = chess.square_rank(move.to_square)

            capture = self.board.is_capture(move)
            san_move = self.board.san(move)
            self.board.push(move)

            moved_piece = self.board.piece_at(move.to_square)

            self.base.chess_renderer.animate_move(
                from_file, from_rank, to_file, to_rank,
                moved_piece, capture=capture
            )

            ply = self.board.fullmove_number
            color = "white" if self.board.turn == chess.BLACK else "black"
            extra = {}
            get_stats = getattr(current, "get_stats", None)
            if callable(get_stats):
                try:
                    s = get_stats()
                    if s:
                        extra = {
                            "tokens_in": s.get("tokens_in"),
                            "tokens_out": s.get("tokens_out"),
                            "retries": s.get("retries"),
                            "fallback": s.get("fallback"),
                        }
                except Exception:
                    pass
            self.tracker.record_move({
                "ply": ply,
                "color": color,
                "move_uci": move.uci(),
                "move_san": san_move,
                "player": self.player_name(current),
                "is_legal": True,
                "latency_ms": elapsed,
                **extra,
            })

            self._last_move_text = f"{san_move}  ({move.uci()})"

            # Wait for animation to finish
            time.sleep(1.5)

        self._end_game()

    def _end_game(self):
        self.is_playing = False
        self.base.taskMgr.remove("updateHud")
        outcome = self.board.outcome()
        result = self.board.result()
        termination = str(outcome.termination) if outcome else "done"

        # Detect LLM disqualification (3 illegal retries exhausted -> fallback)
        disqualify = None
        for player in (self.white_player, self.black_player):
            stats = getattr(player, "get_stats", lambda: {})()
            if stats.get("fallback"):
                color = "White" if getattr(player, "color", chess.WHITE) == chess.WHITE else "Black"
                disqualify = f"{color} exceeded illegal move limit"

        self.tracker.set_result(result, termination, disqualify)
        self._summary = self.tracker.finalize()
        self.base.taskMgr.doMethodLater(0.5, self._deferred_game_over, "gameOver")

    def _deferred_game_over(self, task):
        self.show_game_over()
        return task.done

    def show_game_over(self):
        if not hasattr(self, "_summary") or self._summary is None:
            return
        summary = self._summary
        
        # Center Dark Gray Panel with Gold Border
        self.summary_border = DirectFrame(
            parent=self.base.aspect2d,
            frameSize=(-0.82, 0.82, -0.62, 0.62),
            frameColor=(0.85, 0.75, 0.45, 1), # Bright Gold
            relief=DGG.FLAT,
        )
        self.summary_frame = DirectFrame(
            parent=self.summary_border,
            frameSize=(-0.8, 0.8, -0.6, 0.6),
            frameColor=(0.18, 0.18, 0.20, 0.98), # Dark gray
            relief=DGG.FLAT,
        )
        
        self.game_over_lbl = DirectLabel(
            parent=self.summary_frame,
            text="GAME OVER",
            pos=(0, 0, 0.45),
            scale=0.10,
            text_fg=(1.0, 0.85, 0.35, 1), # Bright Gold
            text_shadow=(0, 0, 0, 1),
            text_shadowOffset=(0.03, -0.03),
            text_font=self.base.font_old_english,
            relief=None,
        )
        
        DirectLabel(
            parent=self.summary_frame,
            text=f"Result: {summary.get('result', '?')} (Termination: {summary.get('termination', '?').upper()})",
            pos=(0, 0, 0.35),
            scale=0.045,
            text_fg=(1, 1, 1, 1), # White on dark panel
            text_font=self.base.font_regular,
            relief=None,
        )

        # Creamy white inner panel
        self.inner_panel = DirectFrame(
            parent=self.summary_frame,
            frameSize=(-0.7, 0.7, -0.32, 0.28),
            frameColor=(0.96, 0.94, 0.88, 1), # Creamy white
            relief=DGG.FLAT,
        )

        left_labels = [
            "White Model:",
            "Black Model:",
            "Total Moves:",
            "Total Illegal Moves:",
            "Avg Latency White:",
            "Avg Latency Black:",
            "Total LLM Retries:"
        ]
        
        right_values = [
            str(summary.get('white', '?')),
            str(summary.get('black', '?')),
            str(summary.get('total_moves', 0)),
            str(summary.get('total_illegal_moves', 0)),
            f"{summary.get('avg_latency_white_ms', 0)} ms",
            f"{summary.get('avg_latency_black_ms', 0)} ms",
            str(summary.get('total_retries', 0))
        ]
        
        disq = summary.get("llm_disqualification")
        if disq:
            left_labels.append("Disqualification:")
            right_values.append(str(disq))

        start_y = 0.20
        line_spacing = 0.075

        for i, (lbl, val) in enumerate(zip(left_labels, right_values)):
            y = start_y - i * line_spacing
            
            # Left column (label)
            DirectLabel(
                parent=self.inner_panel,
                text=lbl,
                pos=(-0.05, 0, y),
                scale=0.04,
                text_fg=(0.1, 0.1, 0.1, 1), # Black
                text_align=TextNode.ARight,
                text_font=self.base.font_regular,
                relief=None,
            )
            
            # Right column (value)
            DirectLabel(
                parent=self.inner_panel,
                text=val,
                pos=(0.05, 0, y),
                scale=0.04,
                text_fg=(0.1, 0.1, 0.1, 1), # Black
                text_align=TextNode.ALeft,
                text_font=self.base.font_regular,
                relief=None,
            )

        # PLAY AGAIN button
        self.play_again_border = DirectFrame(
            parent=self.summary_frame,
            frameSize=(-0.31, 0.31, -0.52, -0.36),
            frameColor=(1.0, 0.85, 0.35, 1), # Bright Gold
            relief=DGG.FLAT
        )
        self.play_again_btn = DirectButton(
            parent=self.play_again_border,
            text="PLAY AGAIN",
            pos=(0, 0, -0.455),
            scale=0.055,
            text_fg=(1, 1, 1, 1),
            text_font=self.base.font_regular,
            frameSize=(-5.4, 5.4, -1.0, 1.0),
            frameColor=(0.15, 0.15, 0.18, 1),
            relief=DGG.FLAT,
            command=self._on_accept
        )

        self.base.accept("enter", self._on_accept)

    def _on_accept(self):
        if hasattr(self, "summary_border") and self.summary_border:
            self.summary_border.destroy()
            self.summary_border = None
        if hasattr(self, "top_bar_border") and self.top_bar_border:
            self.top_bar_border.destroy()
            self.top_bar_border = None
        if hasattr(self, "hud_frame") and self.hud_frame:
            self.hud_frame.destroy()
        self.base.taskMgr.remove("updateHud")
        self.base.ignore("enter")
        if hasattr(self.base, "show_main_menu"):
            self.base.show_main_menu()

    def hide(self):
        self.is_playing = False
        self.base.taskMgr.remove("updateHud")
        super().hide()

    def destroy(self):
        self.is_playing = False
        self.base.taskMgr.remove("updateHud")
        self.base.taskMgr.remove("gameOver")
        if hasattr(self, "hud_frame") and self.hud_frame:
            self.hud_frame.destroy()
        super().destroy()