# Generated code -- CC0 -- No Rights Reserved -- http://www.redblobgames.com/grids/hexagons/


import collections
import math
from dataclasses import dataclass
from math import isclose
from typing import Literal, NamedTuple, cast

_EVEN: Literal[1] = 1
_ODD: Literal[-1] = -1

offset_system = Literal["odd-r", "even-r", "odd-q", "even-q"]


# FIXME: does arcade have a point we should use?
class Point(NamedTuple):
    """A point in 2D space."""

    x: float
    y: float


class _Orientation(NamedTuple):
    """Helper class to store forward and inverse matrix for hexagon conversion.

    Also stores the start angle for hexagon corners.
    """

    f0: float
    f1: float
    f2: float
    f3: float
    b0: float
    b1: float
    b2: float
    b3: float
    start_angle: float


pointy_orientation = _Orientation(
    math.sqrt(3.0),
    math.sqrt(3.0) / 2.0,
    0.0,
    3.0 / 2.0,
    math.sqrt(3.0) / 3.0,
    -1.0 / 3.0,
    0.0,
    2.0 / 3.0,
    0.5,
)
flat_orientation = _Orientation(
    3.0 / 2.0,
    0.0,
    math.sqrt(3.0) / 2.0,
    math.sqrt(3.0),
    2.0 / 3.0,
    0.0,
    -1.0 / 3.0,
    math.sqrt(3.0) / 3.0,
    0.0,
)


class Layout(NamedTuple):
    """Helper class to store hexagon layout information."""

    orientation: _Orientation
    size: Point
    origin: Point


# TODO: should this be a np.array?
# TODO: should this be in rust?
# TODO: should this be cached/memoized?
# TODO: benchmark
@dataclass(frozen=True)
class Hex:
    """A hexagon in cube coordinates."""

    q: float
    r: float
    s: float

    def __post_init__(self):
        """Create a hexagon in cube coordinates."""
        cube_sum = self.q + self.r + self.s
        assert isclose(
            0, cube_sum, abs_tol=1e-14
        ), f"q + r + s must be 0, is {cube_sum}"  # noqa: PLR2004

    def __eq__(self, other: object) -> bool:
        """Check if two hexagons are equal."""
        return self.q == other.q and self.r == other.r and self.s == other.s  # type: ignore

    def __add__(self, other: "Hex") -> "Hex":
        """Add two hexagons."""
        return Hex(self.q + other.q, self.r + other.r, self.s + other.s)

    def __sub__(self, other: "Hex") -> "Hex":
        """Subtract two hexagons."""
        return Hex(self.q - other.q, self.r - other.r, self.s - other.s)

    def __mul__(self, k: int) -> "Hex":
        """Multiply a hexagon by a scalar."""
        return Hex(self.q * k, self.r * k, self.s * k)

    def __neg__(self) -> "Hex":
        """Negate a hexagon."""
        return Hex(-self.q, -self.r, -self.s)

    def __round__(self) -> "Hex":
        """Round a hexagon."""
        qi = int(round(self.q))
        ri = int(round(self.r))
        si = int(round(self.s))
        q_diff = abs(qi - self.q)
        r_diff = abs(ri - self.r)
        s_diff = abs(si - self.s)
        if q_diff > r_diff and q_diff > s_diff:
            qi = -ri - si
        elif r_diff > s_diff:
            ri = -qi - si
        else:
            si = -qi - ri
        return Hex(qi, ri, si)

    def rotate_left(self) -> "Hex":
        """Rotate a hexagon to the left."""
        return Hex(-self.s, -self.q, -self.r)

    def rotate_right(self) -> "Hex":
        """Rotate a hexagon to the right."""
        return Hex(-self.r, -self.s, -self.q)

    @staticmethod
    def direction(direction: int) -> "Hex":
        """Return a relative hexagon in a given direction."""
        hex_directions = [
            Hex(1, 0, -1),
            Hex(1, -1, 0),
            Hex(0, -1, 1),
            Hex(-1, 0, 1),
            Hex(-1, 1, 0),
            Hex(0, 1, -1),
        ]
        return hex_directions[direction]

    def neighbor(self, direction: int) -> "Hex":
        """Return the neighbor in a given direction."""
        return self + self.direction(direction)

    def neighbors(self) -> list["Hex"]:
        """Return the neighbors of a hexagon."""
        return [self.neighbor(i) for i in range(6)]

    def diagonal_neighbor(self, direction: int) -> "Hex":
        """Return the diagonal neighbor in a given direction."""
        hex_diagonals = [
            Hex(2, -1, -1),
            Hex(1, -2, 1),
            Hex(-1, -1, 2),
            Hex(-2, 1, 1),
            Hex(-1, 2, -1),
            Hex(1, 1, -2),
        ]
        return self + hex_diagonals[direction]

    def length(self) -> int:
        """Return the length of a hexagon."""
        return int((abs(self.q) + abs(self.r) + abs(self.s)) // 2)

    def distance_to(self, other: "Hex") -> float:
        """Return the distance between self and another Hex."""
        return (self - other).length()

    def line_to(self, other: "Hex") -> list["Hex"]:
        """Return a list of hexagons between self and another Hex."""
        return line(self, other)

    def lerp_between(self, other: "Hex", t: float) -> "Hex":
        """Perform a linear interpolation between self and another Hex."""
        return lerp(self, other, t)

    def to_pixel(self, layout: Layout) -> Point:
        """Convert a hexagon to pixel coordinates."""
        return hex_to_pixel(self, layout)

    def to_offset(self, system: offset_system) -> "OffsetCoord":
        """Convert a hexagon to offset coordinates."""
        if system == "odd-r":
            return roffset_from_cube(self, _ODD)
        if system == "even-r":
            return roffset_from_cube(self, _EVEN)
        if system == "odd-q":
            return qoffset_from_cube(self, _ODD)
        if system == "even-q":
            return qoffset_from_cube(self, _EVEN)

        raise ValueError("system must be odd-r, even-r, odd-q, or even-q")


def lerp(a: Hex, b: Hex, t: float) -> Hex:
    """Perform a linear interpolation between two hexagons."""
    return Hex(
        a.q * (1.0 - t) + b.q * t,
        a.r * (1.0 - t) + b.r * t,
        a.s * (1.0 - t) + b.s * t,
    )


def distance(a: Hex, b: Hex) -> int:
    """Return the distance between two hexagons."""
    return (a - b).length()


def line(a: Hex, b: Hex) -> list[Hex]:
    """Return a list of hexagons between two hexagons."""
    n = distance(a, b)
    # epsilon to nudge points by to falling on an edge
    a_nudge = Hex(a.q + 1e-06, a.r + 1e-06, a.s - 2e-06)
    b_nudge = Hex(b.q + 1e-06, b.r + 1e-06, b.s - 2e-06)
    step = 1.0 / max(n, 1)
    return [round(lerp(a_nudge, b_nudge, step * i)) for i in range(n + 1)]


def hex_to_pixel(h: Hex, layout: Layout) -> Point:
    """Convert axial hexagon coordinates to pixel coordinates."""
    M = layout.orientation
    size = layout.size
    origin = layout.origin
    x = (M.f0 * h.q + M.f1 * h.r) * size.x
    y = (M.f2 * h.q + M.f3 * h.r) * size.y
    return Point(x + origin.x, y + origin.y)


def pixel_to_hex(
    p: Point,
    layout: Layout,
) -> Hex:
    """Convert pixel coordinates to cubic hexagon coordinates."""
    M = layout.orientation
    size = layout.size
    origin = layout.origin
    pt = Point((p.x - origin.x) / size.x, (p.y - origin.y) / size.y)
    q = M.b0 * pt.x + M.b1 * pt.y
    r = M.b2 * pt.x + M.b3 * pt.y
    return Hex(q, r, -q - r)


def hex_corner_offset(corner: int, layout: Layout) -> Point:
    """Return the offset of a hexagon corner."""
    # Hexagons have 6 corners
    assert 0 <= corner < 6  # noqa: PLR2004
    M = layout.orientation
    size = layout.size
    angle = 2.0 * math.pi * (M.start_angle - corner) / 6.0
    return Point(size.x * math.cos(angle), size.y * math.sin(angle))


hex_corners = tuple[Point, Point, Point, Point, Point, Point]


def polygon_corners(h: Hex, layout: Layout) -> hex_corners:
    """Return the corners of a hexagon in a list of pixels."""
    corners = []
    center = hex_to_pixel(h, layout)
    for i in range(6):
        offset = hex_corner_offset(i, layout)
        corners.append(Point(center.x + offset.x, center.y + offset.y))
    result = tuple(corners)
    # Hexagons have 6 corners
    assert len(result) == 6  # noqa: PLR2004
    return cast(hex_corners, result)


@dataclass(frozen=True)
class OffsetCoord:
    """Offset coordinates."""

    col: float
    row: float

    def to_cube(self, system: offset_system) -> Hex:
        """Convert offset coordinates to cube coordinates."""
        if system == "odd-r":
            return roffset_to_cube(self, _ODD)
        if system == "even-r":
            return roffset_to_cube(self, _EVEN)
        if system == "odd-q":
            return qoffset_to_cube(self, _ODD)
        if system == "even-q":
            return qoffset_to_cube(self, _EVEN)

        raise ValueError("system must be EVEN (+1) or ODD (-1)")


def qoffset_from_cube(h: Hex, offset: Literal[-1, 1]) -> OffsetCoord:
    """Convert a hexagon in cube coordinates to q offset coordinates."""
    if offset not in (_EVEN, _ODD):
        raise ValueError("offset must be EVEN (+1) or ODD (-1)")
    col = h.q
    row = h.r + (h.q + offset * (h.q & 1)) // 2
    return OffsetCoord(col, row)


def qoffset_to_cube(h: OffsetCoord, offset: Literal[-1, 1]) -> Hex:
    """Convert a hexagon in q offset coordinates to cube coordinates."""
    if offset not in (_EVEN, _ODD):
        raise ValueError("offset must be EVEN (+1) or ODD (-1)")

    q = h.col
    r = h.row - (h.col + offset * (h.col & 1)) // 2
    s = -q - r
    return Hex(q, r, s)


def roffset_from_cube(h: Hex, offset: Literal[-1, 1]) -> OffsetCoord:
    """Convert a hexagon in cube coordinates to r offset coordinates."""
    col = h.q + (h.r + offset * (h.r & 1)) // 2
    row = h.r
    if offset not in (_EVEN, _ODD):
        raise ValueError("offset must be EVEN (+1) or ODD (-1)")
    return OffsetCoord(col, row)


def roffset_to_cube(h: OffsetCoord, offset: Literal[-1, 1]) -> Hex:
    """Convert a hexagon in r offset coordinates to cube coordinates."""
    q = h.col - (h.row + offset * (h.row & 1)) // 2
    r = h.row
    s = -q - r
    if offset not in (_EVEN, _ODD):
        raise ValueError("offset must be EVEN (+1) or ODD (-1)")
    return Hex(q, r, s)
