import threading

from direct.gui.DirectGui import DirectLabel, DirectEntry, DirectButton, DirectFrame, DirectScrolledFrame, DGG
from panda3d.core import TextNode

from .base_screen import BaseScreen
from ..api_manager import PROVIDER_CONFIG, fetch_models, chat_completion
from ..config_manager import load_settings, save_settings


class SettingsScreen(BaseScreen):
    def __init__(self, base):
        super().__init__(base)
        self.settings = load_settings()
        self.providers = list(PROVIDER_CONFIG.keys())
        self.fullscreen_mode = self.settings.get("fullscreen", True)
        self._setup_ui()

    # ---- UI construction -------------------------------------------------

    def _setup_ui(self):
        # Setup scrollable frame
        self.scroll_frame = DirectScrolledFrame(
            parent=self.root,
            canvasSize=(-1.0, 1.0, -3.2, 1.0),
            frameSize=(-1.1, 1.1, -0.9, 0.95),
            manageScrollBars=True,
            autoHideScrollBars=True,
            frameColor=(0, 0, 0, 0),
            relief=None,
            
            # Sleek scrollbar styling
            verticalScroll_frameColor=(0.1, 0.1, 0.12, 0.9),
            verticalScroll_frameSize=(-0.015, 0.015, -0.9, 0.95),
            verticalScroll_relief=DGG.FLAT,
            verticalScroll_thumb_frameColor=(0.7, 0.5, 0.15, 1.0), # Gold thumb
            verticalScroll_thumb_relief=DGG.FLAT,
            verticalScroll_incButton_frameColor=(0, 0, 0, 0),
            verticalScroll_decButton_frameColor=(0, 0, 0, 0),
        )
        self.scroll_canvas = self.scroll_frame.getCanvas()

        # Bind mouse wheel to scrolling
        self.base.accept("wheel_up", self._on_scroll_up)
        self.base.accept("wheel_down", self._on_scroll_down)

        title = self.create_title("SETTINGS", pos_y=0.88, scale=0.15)
        title.reparentTo(self.scroll_canvas)
        
        current_y = 0.65

        # API Status Table
        self._add_field_label("API STATUS", pos_y=current_y)
        current_y -= 0.10
        api_keys = self.settings.get("api_keys", {})
        self.api_status_labels = {}
        for p in self.providers:
            status = "CONNECTED" if api_keys.get(p) else "MISSING"
            color = (0.2, 0.8, 0.2, 1) if status == "CONNECTED" else (0.8, 0.2, 0.2, 1)
            
            DirectLabel(
                parent=self.scroll_canvas,
                text=f"{p.upper()}:",
                pos=(-0.05, 0, current_y),
                scale=0.05,
                text_fg=self.TEXT_WHITE,
                text_align=TextNode.ARight,
                text_font=self.base.font_regular,
                relief=None,
            )
            
            lbl = DirectLabel(
                parent=self.scroll_canvas,
                text=f"[{status}]",
                pos=(0.05, 0, current_y),
                scale=0.05,
                text_fg=color,
                text_align=TextNode.ALeft,
                text_font=self.base.font_regular,
                relief=None,
            )
            self.api_status_labels[p] = lbl
            current_y -= 0.08
            
        current_y -= 0.10
        
        # API key entry (centered, width fits ~30 chars, multi-line for long keys).
        entry_scale = 0.05
        entry_width = 32
        
        current_y -= 0.05
        self._add_field_label("API KEY (Auto-detects or use 'provider:key')", pos_y=current_y)
        current_y -= 0.10
        
        # We start empty so user can just paste whatever key they want
        # numLines=5 allows long keys to wrap vertically without being truncated
        self.api_key_entry = DirectEntry(
            parent=self.scroll_canvas,
            scale=entry_scale,
            pos=(-(entry_width * entry_scale) / 2.0, 0, current_y),
            width=entry_width,
            numLines=5,
            initialText="",
            suppressKeys=True,
            frameColor=(0.06, 0.06, 0.08, 0.95),
            borderWidth=(0.02, 0.02),
            relief=DGG.FLAT,
            text_fg=self.TEXT_WHITE,
            text_shadow=(0, 0, 0, 0.75),
            text_shadowOffset=(0.04, -0.04),
            text_font=self.base.font_regular,
        )

        current_y -= 0.35 # Make room for 5 lines of text
        
        self.status_label = DirectLabel(
            parent=self.scroll_canvas,
            text="",
            pos=(0, 0, current_y),
            scale=0.05,
            text_fg=self.TEXT_GOLD,
            text_shadow=(0, 0, 0, 1),
            text_shadowOffset=(0.04, -0.04),
            text_align=TextNode.ACenter,
            text_font=self.base.font_old_english,
            relief=None,
        )

        current_y -= 0.15
        btn_save = self.create_button("Save Key", scale=0.08, pos_y=current_y, command=self._save)
        btn_save.reparentTo(self.scroll_canvas)
        
        current_y -= 0.15
        self.fs_btn = self.create_button(f"Fullscreen: {'ON' if self.fullscreen_mode else 'OFF'}", scale=0.07, pos_y=current_y, command=self._toggle_fullscreen)
        self.fs_btn.reparentTo(self.scroll_canvas)
        
        current_y -= 0.20
        btn_back = self.create_button("Back", scale=0.08, pos_y=current_y, command=self._on_back)
        btn_back.reparentTo(self.scroll_canvas)
        
        # Adjust canvas size dynamically based on final current_y
        self.scroll_frame["canvasSize"] = (-1.0, 1.0, current_y - 0.2, 1.0)

    def _add_field_label(self, text, pos_y):
        lbl = self.create_label(text, pos_y=pos_y, scale=0.07, color=self.TEXT_DIM)
        lbl.reparentTo(self.scroll_canvas)

    def _on_scroll_up(self, event=None):
        sb = self.scroll_frame.verticalScroll
        if sb and not sb.isHidden():
            sb.setValue(sb.getValue() - 0.1)

    def _on_scroll_down(self, event=None):
        sb = self.scroll_frame.verticalScroll
        if sb and not sb.isHidden():
            sb.setValue(sb.getValue() + 0.1)

    def _update_api_status_table(self):
        api_keys = self.settings.get("api_keys", {})
        for p, lbl in self.api_status_labels.items():
            status = "CONNECTED" if api_keys.get(p) else "MISSING"
            color = (0.2, 0.8, 0.2, 1) if status == "CONNECTED" else (0.8, 0.2, 0.2, 1)
            lbl["text"] = f"[{status}]"
            lbl["text_fg"] = color

    def destroy(self):
        self.base.ignore("wheel_up")
        self.base.ignore("wheel_down")
        super().destroy()

    # ---- helpers ---------------------------------------------------------

    def _get_api_key(self):
        return self.api_key_entry.get().strip()

    def _toggle_fullscreen(self):
        self.fullscreen_mode = not self.fullscreen_mode
        self.fs_btn["text"] = f"Fullscreen: {'ON' if self.fullscreen_mode else 'OFF'}"

    # ---- actions ---------------------------------------------------------

    def _save(self):
        # Always save general settings first
        self.settings["fullscreen"] = self.fullscreen_mode
        if "api_keys" not in self.settings:
            self.settings["api_keys"] = {}
        
        # Then attempt to parse/save API Key if present
        key = self._get_api_key()
        if not key:
            save_settings(self.settings)
            self.status_label["text"] = "Settings saved (No new API key)."
            return
            
        # Auto-detect provider or parse explicit prefix
        provider = None
        
        # Explicit prefix check (e.g., "mistral: xxx")
        if ":" in key:
            parts = key.split(":", 1)
            possible_prov = parts[0].strip().lower()
            if possible_prov in self.providers:
                provider = possible_prov
                key = parts[1].strip()
                
        # Auto-detect if not explicitly provided
        if not provider:
            if key.startswith("sk-or-"):
                provider = "openrouter"
            elif key.startswith("nvapi-"):
                provider = "nvidia"
            elif key.startswith("AIza"):
                provider = "google"
            elif key.startswith("sk-ant-"):
                provider = "anthropic"
            elif key.startswith("gsk_"):
                provider = "groq"
            elif key.startswith("sk-"):
                # sk- could be openai, deepseek, or together. We default to openai unless specified.
                provider = "openai"
            elif len(key) > 50:
                # long random keys without prefix could be mistral or together, but hard to guess
                # User should use 'mistral: key' format.
                pass
            
        if not provider:
            save_settings(self.settings)
            self.status_label["text"] = "Settings saved, but Key format not recognized!"
            return
            
        self.settings["api_keys"][provider] = key
        save_settings(self.settings)
        
        self.status_label["text"] = f"Detected {provider.upper()} key. Saved!"
        self._update_api_status_table()
        self.api_key_entry.enterText("")

    def _on_back(self):
        self._save()
        if hasattr(self.base, "show_main_menu"):
            self.base.show_main_menu()

    def destroy(self):
        self.base.taskMgr.remove("modelsReady")
        self.base.taskMgr.remove("testDone")
        super().destroy()
