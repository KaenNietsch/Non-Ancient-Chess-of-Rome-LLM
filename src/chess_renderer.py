import os
from typing import Dict, Optional

from panda3d.core import (
    NodePath, Material, AmbientLight, DirectionalLight, PointLight,
    Filename, CardMaker, LPoint3f, Vec4, TransparencyAttrib
)
from direct.interval.LerpInterval import LerpPosInterval
from direct.interval.IntervalGlobal import Sequence, Func
import chess

MODEL_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "chess_models"
)

MODEL_FILES = {
    "king": "Şah.glb",
    "queen": "Vezir.glb",
    "rook": "Kale.glb",
    "bishop": "Fil.glb",
    "knight": "At.glb",
    "pawn": "Piyon.glb",
}

# Target piece height in world units (a square is 1.0 unit).
TARGET_HEIGHT = {
    "pawn": 0.85, "rook": 1.15, "knight": 1.25,
    "bishop": 1.30, "queen": 1.45, "king": 1.55,
}

# Warm, realistic palette resembling Screenshot 4.
BOARD_LIGHT = (0.90, 0.82, 0.68, 1.0)   # pale ash/maple
BOARD_DARK = (0.28, 0.22, 0.18, 1.0)    # dark ebony/walnut
BOARD_FRAME = (0.75, 0.62, 0.45, 1.0)   # wooden rim, oak

PIECE_NAMES = {
    (chess.KING, chess.WHITE): "king",
    (chess.QUEEN, chess.WHITE): "queen",
    (chess.ROOK, chess.WHITE): "rook",
    (chess.BISHOP, chess.WHITE): "bishop",
    (chess.KNIGHT, chess.WHITE): "knight",
    (chess.PAWN, chess.WHITE): "pawn",
    (chess.KING, chess.BLACK): "king",
    (chess.QUEEN, chess.BLACK): "queen",
    (chess.ROOK, chess.BLACK): "rook",
    (chess.BISHOP, chess.BLACK): "bishop",
    (chess.KNIGHT, chess.BLACK): "knight",
    (chess.PAWN, chess.BLACK): "pawn",
}


class ChessRenderer:
    def __init__(self, base):
        self.base = base
        self.scene = base.render.attach_new_node("ChessScene")
        self.piece_models: Dict[str, NodePath] = {}
        self.placed_pieces: Dict[int, NodePath] = {}
        self.move_highlights = []
        self._load_models()
        self._build_board()
        self._setup_lights()

    def _find_model(self, fname: str) -> Optional[str]:
        path = os.path.join(MODEL_DIR, fname)
        if os.path.exists(path):
            return path
        up = os.path.join(MODEL_DIR, fname.replace(".glb", ".GLB"))
        if os.path.exists(up):
            return up
        return None

    def _load_models(self):
        """Load GLB pieces (Y-up per glTF), rotate them so +Y becomes +Z,
        scale to a uniform target height, and shift the pivot so the base of
        every piece sits exactly at z=0."""
        for name, fname in MODEL_FILES.items():
            path = self._find_model(fname)
            if path is None:
                print(f"[chess_renderer] model not found: {fname}")
                continue
            try:
                m = self.base.loader.loadModel(Filename.fromOsSpecific(path))
                m.reparent_to(self.scene)
                m.hide()
                # glTF models are Y-up; rotate 90° about X to stand on Z.
                m.setP(90)
                target_h = TARGET_HEIGHT.get(name, 1.2)
                bmin = LPoint3f()
                bmax = LPoint3f()
                m.calcTightBounds(bmin, bmax)
                h = bmax[2] - bmin[2]
                if h > 1e-6:
                    s = target_h / h
                    m.setScale(s)
                    # Move the base of the piece down to z=0.
                    m.setZ(-bmin[2] * s)
                self.piece_models[name] = m
            except Exception as e:
                print(f"[chess_renderer] failed to load {fname}: {e}")

    def _build_board(self):
        sz = 1.0
        half = 4.0

        board = self.scene.attach_new_node("Board")

        # Panda3D CardMaker creates cards in the X-Z plane (vertical, facing
        # +/-Y). Rotating each card -90° about X lays it flat in the X-Y
        # plane so the board reads as a horizontal slab when viewed from above.
        cm = CardMaker("sq")
        cm.setFrame(-sz / 2, sz / 2, -sz / 2, sz / 2)
        for row in range(8):
            for col in range(8):
                color = BOARD_LIGHT if (row + col) % 2 == 0 else BOARD_DARK
                cm.setColor(*color)
                sq = board.attach_new_node(cm.generate())
                sq.setTwoSided(True)
                sq.setP(-90)
                x = col * sz - half + sz / 2
                y = row * sz - half + sz / 2
                sq.setPos(x, y, 0)

        # Solid wood base below the squares (board thickness) as a flat slab.
        # Top/bottom faces lie flat; the 4 walls are vertical.
        bs = 8.0 + 0.5
        top = board.attach_new_node(cm.generate())
        cm.setFrame(-bs / 2, bs / 2, -bs / 2, bs / 2)
        cm.setColor(*BOARD_FRAME)
        top.setTwoSided(True)
        top.setP(-90)
        top.setPos(0, 0, -0.05)

        bot = board.attach_new_node(cm.generate())
        bot.setTwoSided(True)
        bot.setP(-90)
        bot.setPos(0, 0, -0.23)

        # Side walls (raw cards are already vertical / X-Z plane).
        wall_color = (0.65, 0.52, 0.35, 1.0)
        wall = CardMaker("wall")
        wall.setFrame(-bs / 2, bs / 2, -0.23, 0.0)
        wall.setColor(*wall_color)

        def make_vertical_wall(hpr, pos):
            w = board.attach_new_node(wall.generate())
            w.setTwoSided(True)
            w.setHpr(*hpr)
            w.setPos(*pos)
            return w

        # front / back edges (span x, vertical in z)
        make_vertical_wall((0, 0, 0), (0, -bs / 2, -0.115))
        make_vertical_wall((0, 180, 0), (0, bs / 2, -0.115))
        # left / right edges: heading 90° about Z swings the wall's X extent
        # into Y so it runs along the left/right sides.
        make_vertical_wall((90, 0, 0), (-bs / 2, 0, -0.115))
        make_vertical_wall((-90, 0, 0), (bs / 2, 0, -0.115))

        # Add a large wooden table underneath the board
        table = CardMaker("table")
        table.setFrame(-30, 30, -30, 30)
        table.setColor(0.40, 0.30, 0.22, 1.0)
        tbl = board.attach_new_node(table.generate())
        tbl.setP(-90)
        tbl.setPos(0, 0, -0.231)

    def _setup_lights(self):
        """Warm, realistic lighting with soft shadows."""
        self.scene.setShaderAuto()

        # Warm ambient
        al = AmbientLight("ambient")
        al.setColor((0.45, 0.40, 0.35, 1.0))
        self.scene.setLight(self.scene.attach_new_node(al))

        # Golden hour / warm key light
        dl = DirectionalLight("key")
        dl.setColor((1.6, 1.4, 1.1, 1.0))
        dl.setSpecularColor((1.0, 0.9, 0.8, 1.0))
        dl.setShadowCaster(True, 2048, 2048)
        dl.getLens().setFilmSize(25, 25)
        dl.getLens().setNearFar(-20, 30)
        dnp = self.scene.attach_new_node(dl)
        dnp.setHpr(-45, -55, 0)
        self.scene.setLight(dnp)

        # Cooler, subtle fill light
        fl = DirectionalLight("fill")
        fl.setColor((0.3, 0.35, 0.45, 1.0))
        fl.setSpecularColor((0.1, 0.15, 0.2, 1.0))
        fnp = self.scene.attach_new_node(fl)
        fnp.setHpr(135, -30, 0)
        self.scene.setLight(fnp)

    def _sq_pos(self, file_val: int, rank_val: int):
        size = 1.0
        half = 4.0
        x = file_val * size - half + size / 2
        y = (7 - rank_val) * size - half + size / 2
        return x, y, ChessRenderer.PIECE_BASE

    # Pieces must hover slightly above the board surface so their bases never
    # z-fight with the squares (which looks like sinking / flickering).
    PIECE_BASE = 0.02

    def _piece_key(self, piece: chess.Piece) -> Optional[str]:
        return PIECE_NAMES.get((piece.piece_type, piece.color))

    def _set_metal(self, node: NodePath, is_white: bool):
        mat = Material()
        if is_white:
            # Pure Silver
            mat.set_shininess(90.0)
            mat.set_ambient((0.4, 0.4, 0.4, 1.0))
            mat.set_diffuse((0.85, 0.85, 0.9, 1.0))
            mat.set_specular((1.0, 1.0, 1.0, 1.0))
        else:
            # Pure Gold
            mat.set_shininess(80.0)
            mat.set_ambient((0.3, 0.2, 0.05, 1.0))
            mat.set_diffuse((0.95, 0.75, 0.15, 1.0))
            mat.set_specular((1.0, 0.85, 0.3, 1.0))
        node.set_texture_off()
        for g in node.find_all_matches("**/+GeomNode"):
            g.set_material(mat)

    def place_piece(self, piece: chess.Piece, fl: int, rnk: int, animate: bool = False) -> Optional[NodePath]:
        key = self._piece_key(piece)
        if not key or key not in self.piece_models:
            return None

        squ = chess.square(fl, rnk)
        x, y, z = self._sq_pos(fl, rnk)

        src = self.piece_models[key]
        nd = src.copy_to(self.scene)
        nd.show()
        
        if piece.color == chess.BLACK:
            nd.setH(180)
            
        # The GLB models are loaded with a centered pivot: their geometry base
        # sits below the node origin, and _load_models lifted each source so
        # the base lands on world z=0 (via src.setZ = -local_base). copy_to
        # carries that transform, but setPos overrides it — so re-apply the
        # source's lift so the piece base rests on PIECE_BASE above the board.
        nd.setPos(x, y, z + src.getZ())
        self._set_metal(nd, piece.color == chess.WHITE)

        if animate:
            nd.setZ(4.0)
            LerpPosInterval(nd, 0.30, (x, y, z + src.getZ())).start()

        self.placed_pieces[squ] = nd
        return nd

    def _clear_highlights(self):
        for h in self.move_highlights:
            h.remove_node()
        self.move_highlights.clear()

    def _highlight_square(self, file_val: int, rank_val: int):
        cm = CardMaker("hl")
        sz = 1.0
        cm.setFrame(-sz/2, sz/2, -sz/2, sz/2)
        # Golden glowing transparent square
        cm.setColor(0.9, 0.8, 0.2, 0.45)
        hl = self.scene.attach_new_node(cm.generate())
        hl.setTwoSided(True)
        hl.setP(-90)
        x, y, _ = self._sq_pos(file_val, rank_val)
        hl.setPos(x, y, 0.01) # Slightly above board squares (which are at 0.0)
        hl.setTransparency(TransparencyAttrib.MAlpha)
        self.move_highlights.append(hl)

    def animate_move(self, frf: int, frr: int, tof: int, tor: int, piece: chess.Piece, capture: bool = False):
        self._clear_highlights()
        self._highlight_square(frf, frr)
        self._highlight_square(tof, tor)
        
        frs = chess.square(frf, frr)
        tos = chess.square(tof, tor)

        if capture and tos in self.placed_pieces:
            cap = self.placed_pieces.pop(tos)
            Sequence(
                LerpPosInterval(cap, 0.2, (cap.getX(), cap.getY(), 3.0)),
                Func(cap.remove_node),
            ).start()

        nd = self.placed_pieces.pop(frs, None)
        if nd is None:
            nd = self.place_piece(piece, frf, frr, animate=False)
            if nd is None:
                return

        # The node origin is lifted by the source pivot (see place_piece), so
        # every lerp target must carry that same +src.getZ() offset.
        zoff = self.piece_models.get(self._piece_key(piece), nd).getZ()
        fx, fy, zf = self._sq_pos(frf, frr)
        tx, ty, _ = self._sq_pos(tof, tor)
        zt = zf + zoff
        lift = 1.0 + max(nd.getScale().getZ(), 0.8) * 0.5

        seq = Sequence(
            LerpPosInterval(nd, 0.15, (fx, fy, zt + lift), blendType="easeInOut"),
            LerpPosInterval(nd, 0.40, (tx, ty, zt + lift), blendType="easeInOut"),
            LerpPosInterval(nd, 0.15, (tx, ty, zt), blendType="easeInOut"),
        )
        seq.start()
        self.placed_pieces[tos] = nd

    def update_from_board(self, board: chess.Board):
        self._clear_highlights()
        for p in self.placed_pieces.values():
            p.remove_node()
        self.placed_pieces.clear()
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece:
                f = chess.square_file(sq)
                r = chess.square_rank(sq)
                self.place_piece(piece, f, r, animate=False)

    def reset(self):
        self._clear_highlights()
        for p in self.placed_pieces.values():
            p.remove_node()
        self.placed_pieces.clear()

    def destroy(self):
        self.reset()
        if self.scene:
            self.scene.remove_node()
        for m in self.piece_models.values():
            m.remove_node()
