from direct.gui.DirectGui import DirectLabel
from panda3d.core import TextNode

from .base_screen import BaseScreen


class MainMenuScreen(BaseScreen):
    def __init__(self, base):
        super().__init__(base)
        self._setup_menu_ui()

    def _setup_menu_ui(self):
        # Two-line title.
        self.create_title("NON-ANCIENT CHESS", pos_y=0.75, scale=0.15)
        self.create_title("OF ROME LLM", pos_y=0.55, scale=0.10)

        btn_y = 0.15
        spacing = 0.22

        self.play_btn = self.create_button("Play", pos_y=btn_y, command=self._on_play)
        self.history_btn = self.create_button("History", pos_y=btn_y - spacing, command=self._on_history)
        self.settings_btn = self.create_button("Settings", pos_y=btn_y - spacing * 2, command=self._on_settings)
        self.quit_btn = self.create_button("Quit", pos_y=btn_y - spacing * 3, command=self._on_quit)

    def _on_play(self):
        if hasattr(self.base, "show_mode_select"):
            self.base.show_mode_select()

    def _on_history(self):
        if hasattr(self.base, "show_history"):
            self.base.show_history()

    def _on_settings(self):
        if hasattr(self.base, "show_settings"):
            self.base.show_settings()

    def _on_quit(self):
        self.base.userExit()
