import sys
import os

from panda3d.core import Filename, WindowProperties
from direct.showbase.ShowBase import ShowBase
from src.config_manager import load_settings
from src.chess_renderer import ChessRenderer
from src.background_show import BackgroundShow
from src.screens.main_menu import MainMenuScreen
from src.screens.settings_screen import SettingsScreen
from src.screens.game_screen import GameScreen
from src.screens.history_screen import HistoryScreen
from src.screens.replay_screen import ReplayScreen


class ChessGame3D(ShowBase):
    def __init__(self):
        from panda3d.core import loadPrcFileData, AntialiasAttrib, Fog, WindowProperties
        # Enable MSAA before ShowBase initializes the window
        loadPrcFileData("", "framebuffer-multisample 1")
        loadPrcFileData("", "multisamples 4")
        ShowBase.__init__(self)
        self.render.setAntialias(AntialiasAttrib.MMultisample)
        
        # Set a very dark background color matching the fog
        self.setBackgroundColor(0.06, 0.05, 0.04)

        # Add cinematic fog to hide the table edges and blend into the background
        myFog = Fog("SceneFog")
        myFog.setColor(0.06, 0.05, 0.04)
        myFog.setExpDensity(0.02)
        self.render.setFog(myFog)

        # Setup camera rig for smooth pivoting
        self.cam_rig = self.render.attachNewNode("camRig")
        self.camera.reparentTo(self.cam_rig)
        
        # Stop ShowBase's built-in mouse driver from rotating the camera;
        # otherwise it hijacks clicks and breaks DirectGui buttons.
        self.disableMouse()
        self.setup_fonts()
        
        from src.config_manager import load_settings
        settings = load_settings()
        
        # Native Fullscreen Resolution Setup
        wp = WindowProperties()
        wp.setTitle("Non-Ancient Chess of Rome LLM")
        
        if settings.get("fullscreen", True):
            wp.setSize(self.pipe.getDisplayWidth(), self.pipe.getDisplayHeight())
            wp.setFullscreen(True)
        else:
            wp.setSize(1280, 720)
            wp.setFullscreen(False)
            
        self.win.requestProperties(wp)
        
        self.chess_renderer = ChessRenderer(self)
        self.background_show = BackgroundShow(self)
        self.current_screen = None

        self.show_main_menu()

    def setup_fonts(self):
        # Decorative gothic font for big TITLES/headings (user preference).
        oe_path = "OldeEnglish.ttf"
        if os.path.exists(oe_path):
            self.font_old_english = self.loader.loadFont(oe_path)
        else:
            self.font_old_english = None

        # Clean, highly readable font for buttons / body text.
        segoe_path = "SegoeUI.ttf"
        if os.path.exists(segoe_path):
            self.font_regular = self.loader.loadFont(segoe_path)
        else:
            self.font_regular = self.font_old_english

    def set_screen(self, new_screen):
        if self.current_screen:
            self.current_screen.destroy()
        self.current_screen = new_screen
        if self.current_screen:
            self.current_screen.show()
        # Menu screens keep the animated queen background playing; the actual
        # game screen switches to the fixed board camera instead.
        self._sync_background(new_screen)

    def _sync_background(self, screen):
        if self.background_show is None:
            return
        if isinstance(screen, GameScreen):
            self.background_show.hide()
        else:
            self.background_show.show()

    def _static_board_camera(self):
        # Realistic "sitting at the table" view:
        self.cam_rig.setH(0)
        # Increase FOV and pull back slightly to ensure it fits 16:9 full screens
        self.camLens.setFov(55)
        self.camera.setPos(0, 14.0, 11.0)
        self.camera.lookAt(0, 0, 0)

    def move_camera_to_side(self, is_white: bool):
        from direct.interval.LerpInterval import LerpHprInterval
        target_h = 0 if is_white else 180
        
        # If camera is at 0 and needs to go to 180, or 180 -> 0, it just rotates smoothly
        LerpHprInterval(
            self.cam_rig, 
            1.5, 
            (target_h, 0, 0), 
            startHpr=(self.cam_rig.getH(), 0, 0),
            blendType="easeInOut"
        ).start()

    def show_main_menu(self):
        self.set_screen(MainMenuScreen(self))

    def show_mode_select(self):
        from src.screens.mode_select_screen import ModeSelectScreen
        self.set_screen(ModeSelectScreen(self))

    def show_settings(self):
        self.set_screen(SettingsScreen(self))

    def show_history(self):
        self.set_screen(HistoryScreen(self))

    def show_replay(self, match_id):
        screen = ReplayScreen(self)
        screen.start_replay(match_id)
        self.set_screen(screen)

    def start_game(self, white, black):
        screen = GameScreen(self)
        screen.start_game(white, black)
        self.set_screen(screen)


def main():
    app = ChessGame3D()
    app.run()


if __name__ == "__main__":
    main()