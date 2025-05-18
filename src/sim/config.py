from pathlib import Path

from sim import hexagon

HEX_LAYOUT = hexagon.Layout(
    hexagon.pointy_orientation, hexagon.Point(140 / 2, 140 / 2), hexagon.Point(0, 0)
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
ASSETS = PROJECT_ROOT / "assets"
MAP = ASSETS / "maps" / "4corners.tmj"
assert MAP.exists(), f"Map file not found: {MAP}"
