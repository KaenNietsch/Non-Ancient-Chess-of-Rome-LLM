from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DGG
from panda3d.core import TextNode


class BaseScreen:
    def __init__(self, base):
        self.base = base
        # Transparent, zero-sized root frame: it must NOT swallow mouse events
        # meant for the child buttons.
        self.root = DirectFrame(
            parent=base.aspect2d,
            frameSize=(0, 0, 0, 0),
            frameColor=(0, 0, 0, 0),
        )
        self.root.hide()

    def show(self):
        self.root.show()

    def hide(self):
        self.root.hide()

    def destroy(self):
        self.root.destroy()

    def _measure_text(self, text, font):
        # Compute the actual rendered width of the text in widget units.
        try:
            tn = TextNode("measure")
            tn.set_font(font)
            tn.set_text(text)
            tn.set_align(TextNode.ACenter)
            return tn.get_width()
        except Exception:
            return len(text) * 0.65

    # Consistent "white text on black" theme used by every screen.
    TEXT_WHITE = (1.0, 1.0, 1.0, 1)
    TEXT_GOLD = (1.0, 0.85, 0.35, 1)
    TEXT_DIM = (0.82, 0.82, 0.82, 1)
    PANEL_BLACK = (0.04, 0.04, 0.05, 0.92)
    PANEL_DARK = (0.10, 0.10, 0.13, 0.92)
    BUTTON_FRAME = (
        (0.12, 0.12, 0.16, 1),
        (0.18, 0.18, 0.24, 1),
        (0.26, 0.26, 0.34, 1),
        (0.08, 0.08, 0.10, 1),
    )

    def create_title(self, text, pos_y=0.85, scale=0.15):
        return DirectLabel(
            parent=self.root,
            text=text,
            pos=(0, 0, pos_y),
            scale=scale,
            text_fg=self.TEXT_WHITE,
            text_shadow=(0, 0, 0, 0.75),
            text_shadowOffset=(0.04, -0.04),
            text_align=TextNode.ACenter,
            text_font=self.base.font_old_english,
            relief=None,
        )

    def create_label(self, text, pos_y=0, scale=0.07, color=TEXT_DIM, font=None):
        if font is None:
            font = self.base.font_old_english
        
        w = self._measure_text(text, font)
        half_w = max(w / 2 + 0.1, 0.8)
        
        return DirectLabel(
            parent=self.root,
            text=text,
            pos=(0, 0, pos_y),
            scale=scale,
            text_fg=color,
            text_shadow=(0, 0, 0, 0.75),
            text_shadowOffset=(0.04, -0.04),
            text_align=TextNode.ACenter,
            text_font=font,
            relief=DGG.FLAT,
            frameSize=(-half_w, half_w, -0.4, 0.6),
            frameColor=(0, 0, 0, 0.4), # Transparent black background for readability
        )

    def create_button(self, text, scale=0.10, pos_y=0, command=None, extraArgs=None):
        if extraArgs is None:
            extraArgs = []
        w = self._measure_text(text, self.base.font_old_english)
        # Bounding box for background and click
        half_w = max(w / 2 + 0.2, 1.2)
        half_h = 0.5
        return DirectButton(
            parent=self.root,
            text=text,
            text_fg=self.TEXT_WHITE,
            text_shadow=(0, 0, 0, 0.75),
            text_shadowOffset=(0.04, -0.04),
            text_pos=(0, -0.15),
            scale=scale,
            pos=(0, 0, pos_y),
            frameSize=(-half_w, half_w, -half_h, half_h),
            frameColor=(
                (0, 0, 0, 0.6),      # Normal
                (0.3, 0.3, 0.3, 0.8), # Clicked
                (0.2, 0.2, 0.2, 0.7), # Hover
                (0, 0, 0, 0.2)       # Disabled
            ),
            relief=DGG.FLAT,
            pressEffect=1,
            command=command,
            extraArgs=extraArgs,
            text_font=self.base.font_old_english,
        )