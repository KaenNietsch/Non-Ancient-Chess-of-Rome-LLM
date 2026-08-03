import chess

from direct.gui.DirectGui import DirectLabel, DirectButton, DirectSlider
from panda3d.core import TextNode

from .base_screen import BaseScreen
from ..stats_tracker import get_match


class ReplayScreen(BaseScreen):
    def __init__(self, base):
        super().__init__(base)
        self.match = None
        self.board = chess.Board()
        self.moves = []
        self.play_idx = 0
        self._playing = False
        self._play_task_name = "replayStep"
        self._setup_ui()

    def start_replay(self, match_id):
        self.match = get_match(match_id)
        if not self.match:
            return
        self.moves = self.match.get("moves", [])
        self.board = chess.Board()
        self.play_idx = 0
        self.base.chess_renderer.update_from_board(self.board)
        if hasattr(self.base, "_static_board_camera"):
            self.base._static_board_camera()
        if self.moves:
            self.slider["range"] = (0, len(self.moves))
            self.slider["value"] = 0
        self._show_info()

    def _setup_ui(self):
        self.create_title("REPLAY", pos_y=0.85)

        header = self.match or {}
        self.header_label = DirectLabel(
            parent=self.root,
            text="",
            pos=(0, 0, 0.68),
            scale=0.04,
            text_fg=self.TEXT_DIM,
            text_shadow=(0, 0, 0, 0.3),
            text_font=self.base.font_regular,
        )

        self.slider = DirectSlider(
            parent=self.root,
            range=(0, 1),
            value=0,
            pos=(0, 0, -0.48),
            scale=(0.6, 1, 1),
            command=self._on_slider,
        )

        self.info_label = DirectLabel(
            parent=self.root,
            text="",
            pos=(0, 0, 0.55),
            scale=0.04,
            text_fg=self.TEXT_GOLD,
            text_shadow=(0, 0, 0, 0.3),
            text_font=self.base.font_regular,
        )

        self.create_button("Play/Pause", scale=0.04, pos_y=-0.62, command=self._toggle_play)
        self.create_button("Back", scale=0.04, pos_y=-0.78, command=self._on_back)

        if self.match:
            self.header_label["text"] = (
                f"{self.match.get('white', '?')} vs {self.match.get('black', '?')}   "
                f"Result: {self.match.get('result', '?')}   "
                f"Moves: {len(self.moves)}"
            )

    def _on_slider(self):
        self._stop_play()
        try:
            idx = int(round(self.slider["value"]))
        except (ValueError, TypeError):
            return
        if 0 <= idx < len(self.moves):
            self.play_idx = idx
            self._jump_to(idx)

    def _jump_to(self, idx):
        self.board = chess.Board()
        for i in range(idx + 1):
            m = self.moves[i]
            uci = m.get("move_uci")
            if uci:
                try:
                    move = chess.Move.from_uci(uci)
                    if self.board.is_legal(move):
                        self.board.push(move)
                except ValueError:
                    pass
        self.base.chess_renderer.update_from_board(self.board)
        self._show_info()

    def _toggle_play(self):
        if self._playing:
            self._stop_play()
        else:
            self._playing = True
            if self.play_idx >= len(self.moves) - 1:
                self.play_idx = 0
                self._jump_to(0)
            self.base.taskMgr.doMethodLater(0.6, self._step_play, self._play_task_name)

    def _stop_play(self):
        self._playing = False
        self.base.taskMgr.remove(self._play_task_name)

    def _step_play(self, task):
        if not self._playing:
            return task.done
        nxt = self.play_idx + 1
        if nxt < len(self.moves):
            self.play_idx = nxt
            self._jump_to(nxt)
            self.slider["value"] = nxt
            return task.again
        else:
            self._playing = False
            return task.done

    def _show_info(self):
        if not self.moves:
            self.info_label["text"] = "No moves to replay"
            return
        idx = min(self.play_idx, len(self.moves) - 1)
        m = self.moves[idx]
        color = m.get("color", "?")
        text = (
            f"{idx + 1}/{len(self.moves)}  {color.title()}: "
            f"{m.get('move_san', m.get('move_uci', '?'))}"
        )
        if m.get("latency_ms") is not None:
            text += f"  ({int(m.get('latency_ms', 0))} ms)"
        self.info_label["text"] = text

    def _on_back(self):
        self._stop_play()
        if hasattr(self.base, "show_history"):
            self.base.show_history()

    def destroy(self):
        self._stop_play()
        super().destroy()