from dataclasses import dataclass, field

import arcade
from sim.app import hexagon
from sim.app.config import HEX_LAYOUT


@dataclass(frozen=True)
class Tile:
    """A tile on the map."""

    hex: hexagon.Hex
    sprite: arcade.Sprite

    traversable: bool
    traversal_cost: int


def create_tile(hex_: hexagon.Hex, sprite: arcade.Sprite) -> Tile:
    """Create a tile from a hex and a sprite."""
    traversable = False
    traversal_cost = None

    match sprite.properties.get("class"):

        case "mountain":
            traversable = False

        case "grass":
            traversable = True
            traversal_cost = 5

        case "desert":
            traversable = True
            traversal_cost = 10

        case "tree":
            traversable = True
            traversal_cost = 30

        case "cactus":
            traversable = True
            traversal_cost = 15

        case "stone":
            traversable = True
            traversal_cost = 20

        case "house":
            traversable = True
            traversal_cost = 1

    return Tile(
        hex=hex_,
        sprite=sprite,
        traversable=traversable,
        traversal_cost=traversal_cost,
    )
