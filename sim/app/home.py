from dataclasses import dataclass

from sim.app import hexagon


# @dataclass
# class Home:
#     """A home on the map."""

#     location: hexagon.Hex
#     name: str
#     inventory: dict[str, int]
#     money: int

#     def __post_init__(self):
#         """Create a home."""
#         self.inventory = self.inventory or {}
