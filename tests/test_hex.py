from sim.hexagon import (
    Hex,
    Layout,
    OffsetCoord,
    Point,
    flat_orientation,
    hex_to_pixel,
    line,
    pixel_to_hex,
    pointy_orientation,
)

# TODO: hypothesis testing


def equal_offsetcoord(name, a, b):
    assert a.col == b.col and a.row == b.row


def equal_doubledcoord(name, a, b):
    assert a.col == b.col and a.row == b.row


def equal_int(name, a, b):
    assert a == b


def test_hex_equality():
    assert Hex(3, 4, -7) == Hex(3, 4, -7)
    assert Hex(3, 4, -7) != Hex(3, 3, -6)
    assert Hex(3, 4, -7) != Hex(0, 0, 0)
    assert Hex(3, 4, -7) != Hex(4, -7, 3)


def test_hex_pixel_roundtrip():
    flat = Layout(flat_orientation, Point(10.0, 15.0), Point(35.0, 71.0))
    pointy = Layout(pointy_orientation, Point(10.0, 15.0), Point(35.0, 71.0))

    h = Hex(3, 4, -7)
    assert h == round(pixel_to_hex(hex_to_pixel(h, flat), flat))
    assert h == round(pixel_to_hex(hex_to_pixel(h, pointy), pointy))


def test_list_of_hexes():
    [
        Hex(0, 0, 0),
        Hex(0, -1, 1),
        Hex(0, -2, 2),
    ] == [
        Hex(0, 0, 0),
        Hex(0, -1, 1),
        Hex(0, -2, 2),
    ]

    [Hex(0, 0, 0), Hex(0, -1, 1)] != [Hex(0, 0, 0)]

    [Hex(0, 0, 0), Hex(0, -1, 1)] != [Hex(0, -1, 1)]

    [Hex(0, 0, 0), Hex(0, -1, 1)] != [Hex(0, -1, 1), Hex(0, 0, 0)]

    Hex(0, 0, 0) in [Hex(0, 0, 0), Hex(0, -1, 1)]

    Hex(0, 0, 0) not in [Hex(0, -1, 1), Hex(0, -2, 2)]


def test_hex_arithmetic():
    Hex(4, -10, 6) == Hex(1, -3, 2) + Hex(3, -7, 4)
    Hex(-2, 4, -2) == Hex(1, -3, 2) - Hex(3, -7, 4)


def test_hex_direction():
    Hex(0, -1, 1) == Hex.direction(2)


def test_hex_neighbor():
    Hex(1, -3, 2) == Hex(1, -2, 1).neighbor(2)


def test_hex_diagonal():
    Hex(-1, -1, 2) == Hex(1, -2, 1).diagonal_neighbor(3)


def test_hex_distance():
    7 == Hex(3, -7, 4).distance_to(Hex(0, 0, 0))


def test_hex_rotate_right():
    Hex(1, -3, 2).rotate_right() == Hex(3, -2, -1)


def test_hex_rotate_left():
    Hex(1, -3, 2).rotate_left() == Hex(-2, -1, 3)


def test_hex_round():
    a = Hex(0.0, 0.0, 0.0)
    b = Hex(1.0, -1.0, 0.0)
    c = Hex(0.0, -1.0, 1.0)
    Hex(5, -10, 5) == round(
        Hex(0.0, 0.0, 0.0).lerp_between(Hex(10.0, -20.0, 10.0), 0.5)
    )
    round(a) == round(a.lerp_between(b, 0.499))
    round(b) == round(a.lerp_between(b, 0.501))

    round(a) == round(
        Hex(
            a.q * 0.4 + b.q * 0.3 + c.q * 0.3,
            a.r * 0.4 + b.r * 0.3 + c.r * 0.3,
            a.s * 0.4 + b.s * 0.3 + c.s * 0.3,
        )
    )

    round(c) == round(
        Hex(
            a.q * 0.3 + b.q * 0.3 + c.q * 0.4,
            a.r * 0.3 + b.r * 0.3 + c.r * 0.4,
            a.s * 0.3 + b.s * 0.3 + c.s * 0.4,
        )
    )


def test_hex_linedraw():
    [
        Hex(0, 0, 0),
        Hex(0, -1, 1),
        Hex(0, -2, 2),
        Hex(1, -3, 2),
        Hex(1, -4, 3),
        Hex(1, -5, 4),
    ] == line(Hex(0, 0, 0), Hex(1, -5, 4)),


def test_layout():
    h = Hex(3, 4, -7)
    flat = Layout(flat_orientation, Point(10.0, 15.0), Point(35.0, 71.0))

    h == round(pixel_to_hex(hex_to_pixel(h, flat), flat))

    pointy = Layout(pointy_orientation, Point(10.0, 15.0), Point(35.0, 71.0))
    h == round(pixel_to_hex(hex_to_pixel(h, pointy), pointy))


def test_offset_roundtrip():
    a = Hex(3, 4, -7)
    b = OffsetCoord(1, -3)

    a == a.to_offset("even-q").to_cube("even-q")

    b == b.to_cube("even-q").to_offset("even-q")

    a == a.to_offset("odd-q").to_cube("odd-q")

    b == b.to_cube("odd-q").to_offset("odd-q")

    a == a.to_offset("even-r").to_cube("even-r")

    b == b.to_cube("even-r").to_offset("even-r")

    a == a.to_offset("odd-r").to_cube("odd-r")

    b == b.to_cube("odd-r").to_offset("odd-r")


def test_offset_from_cube():
    OffsetCoord(1, 3) == Hex(1, 2, -3).to_offset("even-q")

    OffsetCoord(1, 2) == Hex(1, 2, -3).to_offset("odd-q")


def test_offset_to_cube():
    Hex(1, 2, -3) == OffsetCoord(1, 3).to_cube("even-q")

    Hex(1, 2, -3) == OffsetCoord(1, 2).to_cube("odd-q")
