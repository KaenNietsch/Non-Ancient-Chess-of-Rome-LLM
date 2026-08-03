from direct.gui.DirectGui import DirectLabel, DirectButton, DirectScrolledFrame, DirectFrame, DGG
from panda3d.core import TextNode
import threading

from .base_screen import BaseScreen
from ..config_manager import load_settings
from ..api_manager import fetch_models
from bot_local import LocalBot
from bot_llm import LLMBot
import chess


class ModeSelectScreen(BaseScreen):
    def __init__(self, base):
        super().__init__(base)
        self._error_label = None
        self.settings = load_settings()
        self.api_keys = self.settings.get("api_keys", {})
        self.available_models = []
        self.model_items = ["Fetching API models..."]
        
        self.white_idx = 0
        self.black_idx = 0
            
        self._setup_ui()
        self._fetch_models_async()

    def _setup_ui(self):
        self.create_title("SELECT MODE", pos_y=0.85, scale=0.15)

        btn_style = {
            "scale": 0.05,
            "text_font": self.base.font_regular,
            "text_fg": self.TEXT_WHITE,
            "text_align": TextNode.ALeft,
            "frameSize": (0, 16.0, -0.5, 1.2),
            "frameColor": (0.06, 0.06, 0.08, 0.95),
            "relief": DGG.FLAT,
        }

        self.create_label("WHITE PLAYER:", pos_y=0.55, scale=0.05, color=self.TEXT_GOLD)
        self.white_btn = DirectButton(
            parent=self.root,
            text=self.model_items[self.white_idx],
            pos=(-0.4, 0, 0.45),
            command=self._open_model_modal,
            extraArgs=["white"],
            **btn_style
        )

        self.create_label("BLACK PLAYER:", pos_y=0.25, scale=0.05, color=self.TEXT_GOLD)
        self.black_btn = DirectButton(
            parent=self.root,
            text=self.model_items[self.black_idx],
            pos=(-0.4, 0, 0.15),
            command=self._open_model_modal,
            extraArgs=["black"],
            **btn_style
        )

        self.create_button("START MATCH", scale=0.10, pos_y=-0.35, command=self._start_match)
        self.create_button("Back", scale=0.08, pos_y=-0.80, command=self._on_back)
        
        # Will be updated when fetch completes
        self._update_main_buttons()

    def _open_model_modal(self, color):
        self.modal_bg = DirectFrame(
            parent=self.root, frameSize=(-2, 2, -1, 1),
            frameColor=(0, 0, 0, 0.8), state=DGG.NORMAL, suppressMouse=False
        )
        
        self.modal = DirectFrame(
            parent=self.modal_bg, frameSize=(-0.8, 0.8, -0.7, 0.7),
            frameColor=(0.1, 0.1, 0.12, 1), relief=DGG.FLAT, suppressMouse=False
        )
        
        DirectLabel(
            parent=self.modal, text=f"SELECT {color.upper()} PLAYER", pos=(0, 0, 0.6),
            scale=0.08, text_font=self.base.font_old_english, text_fg=self.TEXT_GOLD, relief=None
        )
        
        DirectButton(
            parent=self.modal, text="Close", scale=0.06, pos=(0, 0, -0.6),
            command=self._close_modal, text_font=self.base.font_regular,
            text_fg=self.TEXT_WHITE, frameColor=(0.2, 0.2, 0.2, 1), relief=DGG.FLAT
        )
        
        canvas_height = max(1.0, len(self.model_items) * 0.15 + 0.05)
        self.scrolled_frame = DirectScrolledFrame(
            parent=self.modal,
            canvasSize=(-0.6, 0.55, -canvas_height, 0),
            frameSize=(-0.65, 0.65, -0.45, 0.5),
            frameColor=(0.06, 0.06, 0.08, 1),
            verticalScroll_relief=DGG.SUNKEN,
            verticalScroll_frameColor=(0.1, 0.1, 0.1, 1),
            verticalScroll_thumb_relief=DGG.RAISED,
            verticalScroll_thumb_frameColor=(0.3, 0.3, 0.3, 1),
            verticalScroll_resizeThumb=True,
            manageScrollBars=True,
            suppressMouse=False
        )
        
        def scroll_up(*args, **kwargs):
            self._scroll(-1)
        def scroll_down(*args, **kwargs):
            self._scroll(1)

        # Global binds
        self.base.accept('wheel_up', scroll_up)
        self.base.accept('wheel_down', scroll_down)
                
        current_y = 0
        current_idx = self.white_idx if color == "white" else self.black_idx
        
        for i, item_text in enumerate(self.model_items):
            # Highlight selected
            bg_color = (0.2, 0.5, 0.2, 1) if i == current_idx else (0.12, 0.12, 0.15, 1)
            txt_color = (1, 1, 1, 1) if i == current_idx else (0.7, 0.7, 0.7, 1)
            
            btn = DirectButton(
                parent=self.scrolled_frame.getCanvas(),
                text=item_text, text_font=self.base.font_regular, text_fg=txt_color,
                text_align=TextNode.ALeft,
                frameSize=(0, 23.0, -0.5, 1.2), frameColor=bg_color, relief=DGG.FLAT,
                scale=0.05, pos=(-0.6, 0, current_y - 0.05),
                command=self._select_model, extraArgs=[color, i, item_text],
                suppressMouse=False
            )

            def get_prov(text):
                if "(No API" in text: return "local"
                return text.strip().split(':')[0].lower()
                
            prov = get_prov(item_text)
            
            # Use exception handling in case a logo is missing
            try:
                btn["image"] = f"Assets/logos/{prov}.png"
                btn["image_scale"] = 0.4
                btn["image_pos"] = (0.5, 0, 0.35)
                # Adjust text so it doesn't overlap the logo
                btn["text_pos"] = (1.5, 0) 
            except Exception:
                pass
            
            current_y -= 0.15

    def _scroll(self, direction):
        if not hasattr(self, 'scrolled_frame'):
            return
        sb = self.scrolled_frame.verticalScroll
        if not sb or sb.isHidden():
            return
        try:
            # Calculate how much 1 item (0.15 units) is in percentage of total scrollable range
            frame_height = 0.95 # From -0.45 to 0.5
            canvas_height = -self.scrolled_frame['canvasSize'][2]
            scrollable_range = canvas_height - frame_height
            if scrollable_range <= 0:
                return
            
            step_pct = 0.15 / scrollable_range
            val = sb.getValue()
            sb.setValue(max(0.0, min(1.0, val + direction * step_pct)))
        except Exception:
            pass

    def _select_model(self, color, idx, item_text):
        if color == "white": self.white_idx = idx
        else: self.black_idx = idx
        self._update_main_buttons()
        self._close_modal()

    def _close_modal(self):
        self.base.ignore('wheel_up')
        self.base.ignore('wheel_down')
        if hasattr(self, "modal_bg"):
            self.modal_bg.destroy()

    def _update_main_buttons(self):
        def update_btn(btn, idx):
            item_text = self.model_items[idx]
            btn["text"] = item_text
            
            def get_prov(text):
                if "(No API" in text: return "local"
                return text.strip().split(':')[0].lower()
                
            prov = get_prov(item_text)
            try:
                btn["image"] = f"Assets/logos/{prov}.png"
                btn["image_scale"] = 0.4
                btn["image_pos"] = (0.5, 0, 0.35)
                btn["text_pos"] = (1.5, 0)
            except Exception:
                pass
            
        update_btn(self.white_btn, self.white_idx)
        update_btn(self.black_btn, self.black_idx)

    def _fetch_models_async(self):
        def worker():
            fetched = []
            chess_keywords = ["gpt-4", "claude", "gemini", "llama", "mistral", "qwen"]
            
            for prov, key in self.api_keys.items():
                if not key:
                    continue
                try:
                    models = fetch_models(prov, key)
                    for m in models:
                        name = m["id"].lower()
                        if any(k in name for k in chess_keywords):
                            m["provider"] = prov
                            fetched.append(m)
                except Exception:
                    pass
            
            self.base.taskMgr.doMethodLater(0.01, self._on_models_fetched_task, "modelsReady", extraArgs=[fetched], appendTask=True)
            
        threading.Thread(target=worker, daemon=True).start()

    def _on_models_fetched_task(self, models, task):
        self._on_models_fetched(models)
        return task.done

    def _on_models_fetched(self, models):
        if models:
            self.available_models = models
        else:
            from ..api_manager import get_available_models
            self.available_models = get_available_models(self.api_keys)
            
        self.model_items = ["    LOCAL: Local Bot"]
        self.model_items.extend([f"    {m['provider'].upper()}: {m['display_name']}" for m in self.available_models])
        
        if len(self.model_items) == 1:
            self.model_items.append("    (No API Models - Add Key)")
            
        self.white_idx = 0
        self.black_idx = 1 if len(self.model_items) > 1 else 0
        
        self._update_main_buttons()

    def _on_back(self):
        if hasattr(self.base, "show_main_menu"):
            self.base.show_main_menu()

    def _get_selected_model_data(self, idx: int):
        if idx == 0:
            return "local", None, None
            
        real_idx = idx - 1
        if not self.available_models or real_idx >= len(self.available_models):
            return None, None, None
            
        m = self.available_models[real_idx]
        prov = m["provider"]
        return prov, m["id"], self.api_keys.get(prov, "")

    def _start_match(self):
        w_prov, w_mid, w_key = self._get_selected_model_data(self.white_idx)
        b_prov, b_mid, b_key = self._get_selected_model_data(self.black_idx)

        depth = self.settings.get("local_depth", 3)
        
        # Setup White
        if w_prov == "local":
            white = LocalBot(chess.WHITE, depth=depth)
        else:
            if not w_key or not w_mid:
                self._show_error("Please configure API keys for White in Settings!")
                return
            white = LLMBot(api_key=w_key, model_name=w_mid, provider=w_prov, color=chess.WHITE)
            
        # Setup Black
        if b_prov == "local":
            black = LocalBot(chess.BLACK, depth=depth)
        else:
            if not b_key or not b_mid:
                self._show_error("Please configure API keys for Black in Settings!")
                return
            black = LLMBot(api_key=b_key, model_name=b_mid, provider=b_prov, color=chess.BLACK)

        self._start(white, black)

    def _start(self, white, black):
        self.hide()
        if hasattr(self.base, "start_game"):
            self.base.start_game(white, black)

    def _show_error(self, msg):
        if self._error_label:
            self._error_label.destroy()
        self._error_label = self.create_label(
            msg, pos_y=-0.15, scale=0.04, color=(1.0, 0.4, 0.35, 1)
        )