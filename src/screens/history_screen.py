from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DGG
from panda3d.core import TextNode

from .base_screen import BaseScreen
from ..stats_tracker import load_match_history


class HistoryScreen(BaseScreen):
    def __init__(self, base):
        super().__init__(base)
        self._setup_ui()

    def _setup_ui(self):
        self.create_title("MATCH HISTORY", pos_y=0.85)

        self.list_frame = DirectFrame(
            parent=self.root,
            frameSize=(-0.85, 0.85, -0.60, 0.55),
            frameColor=self.PANEL_DARK,
            borderWidth=(0.02, 0.02),
            relief=DGG.FLAT,
            pos=(0, 0, -0.12),
        )

        self.back_btn = self.create_button("Back", scale=0.04, pos_y=-0.78, command=self._on_back)

        self._populate()

    def _populate(self):
        history = load_match_history()
        if not history:
            DirectLabel(
                parent=self.list_frame,
                text="No matches found",
                pos=(0, 0, 0),
                scale=0.05,
                text_fg=self.TEXT_DIM,
                text_shadow=(0, 0, 0, 0.3),
            )
            return

        y_offset = 0.48
        for i, match in enumerate(history[-10:]):
            white = match.get('white', '?')
            black = match.get('black', '?')
            raw_result = match.get('result', '?')
            
            # Parse result into readable Win/Lose/Equality and a color
            display_result = "Equality"
            color = (0.7, 0.7, 0.7, 1.0) # Grey for Equality
            
            if "1-0" in raw_result:
                display_result = "White Win"
                color = (0.2, 0.8, 0.2, 1.0) # Green for White Win
            elif "0-1" in raw_result:
                display_result = "Black Win"
                color = (0.8, 0.2, 0.2, 1.0) # Red for Black Win
                
            btn_text = f"  {white} vs {black}  [{display_result}]"
            w = self._measure_text(btn_text, self.base.font_regular)
            half_w = max(w / 2 + 0.45, 0.8)
            DirectButton(
                parent=self.list_frame,
                text=btn_text,
                text_fg=color,
                text_shadow=(0, 0, 0, 1),
                text_shadowOffset=(0.02, -0.02),
                text_align=TextNode.ACenter,
                text_pos=(0, -0.1),
                scale=0.035,
                pos=(0, 0, y_offset - i * 0.10),
                frameSize=(-half_w, half_w, -0.75, 0.75),
                frameColor=(0.1, 0.1, 0.14, 0.9),
                relief=DGG.FLAT,
                command=self._on_replay,
                extraArgs=[match.get("match_id", "")],
            )

    def _on_replay(self, match_id):
        if hasattr(self.base, "show_replay"):
            self.base.show_replay(match_id)

    def _on_back(self):
        if hasattr(self.base, "show_main_menu"):
            self.base.show_main_menu()

    def refresh(self):
        children = list(self.list_frame.getChildren())
        for child in children:
            try:
                child.destroy()
            except Exception:
                child.remove_node()
        self._populate()