from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import arcade
from extended_int import int_inf
from sim.app import hexagon
from sim.app.time import Time

if TYPE_CHECKING:
    from sim.app.agent import Agent


@dataclass(kw_only=True)
class Tile(ABC):
    """A tile."""

    hex: hexagon.Hex
    sprite: arcade.Sprite

    traversable: bool = field(init=False)
    traversal_cost: int | None = field(init=False)

    def __post_init__(self) -> None:
        """Create a tile."""
        self.traversable = self.sprite.properties.get("traversable", False)
        if self.traversable:
            self.traversal_cost = self.sprite.properties.get("traversal_cost")
        else:
            self.traversal_cost = None

    def __hash__(self) -> int:
        """Hash the tile based on the hex."""
        # FIXME: Is this a bad idea?
        return hash(self.hex)


class ResourceTile(Tile):
    """A resource tile."""

    resources: int
    max_resources: int = int_inf
    harvested_resources: int = 0
    resource: str = field(init=False)
    harvest_cost: int = 50
    work_progress: int = 0

    @abstractmethod
    def update(self, time: Time) -> None:
        """Update the tile."""

    def calculate_harvest_work(
        self, quantity: int, *, consider_progress: bool = True
    ) -> int:
        """Get the work required to harvest a quantity of resource.

        Takes into account work progress by default.
        """
        work = self.harvest_cost * quantity
        if consider_progress:
            work -= self.work_progress
        return work

    def harvest(self, work: int, *, refund_work: bool = False) -> tuple[int, int]:
        """Harvest resource.

        If there are no resources to harvest, refunds the work.

        If refund_work is True, refunds the work that was not used to harvest,
        otherwise, the work is saved for the next harvest.

        Returns a tuple:
            int: the amount of resource harvested
            int: refunded excess work
        """
        if self.resources < 0:
            # No resources to harvest
            return 0, work

        harvested_resources = min(
            self.resources, work + self.work_progress // self.harvest_cost
        )
        self.work_progress = work - (harvested_resources * self.harvest_cost)

        self.harvested_resources += harvested_resources

        refunded_work = self.work_progress if refund_work else 0

        return harvested_resources, refunded_work


class Forest(ResourceTile):
    """A forest tile."""

    resources: int = 10
    max_resources: int = 10
    resource = "wood"

    def update(self, time: Time) -> None:
        """Add one tree every year."""
        if time.top_of_year and self.resources < self.max_resources:
            self.resources += 1


class Stone(ResourceTile):
    """A stone tile."""

    resources: int = int_inf
    resource = "stone"
    harvest_cost = 200

    def update(self, time: Time) -> None:
        """Stone does not regenerate."""


class Food(ResourceTile):
    """A food tile."""

    resources: int = 15
    max_resources: int = 20
    resource = "food"
    harvest_cost = 15

    def update(self, time: Time) -> None:
        """Add one food every month."""
        if time.top_of_month and self.resources < self.max_resources:
            self.resources += 1


class House(Tile):
    """A house tile."""


class Desert(Tile):
    """A desert tile."""


class Mountain(Tile):
    """A mountain tile."""


class Grass(Tile):
    """A grass tile."""


class Cactus(ResourceTile):
    """A cactus tile."""

    resources: int = 5
    max_resources: int = 8
    resource = "food"

    def update(self, time: Time) -> None:
        """Add five food every year."""
        if time.top_of_year and self.resources < self.max_resources:
            self.resources += 5
            if self.resources > self.max_resources:
                self.resources = self.max_resources


class Gem(ResourceTile):
    """A gem tile."""

    resources: int = int_inf
    resource = "gem"
    harvest_cost = 5000

    def update(self, time: Time) -> None:
        """Gems do not regenerate."""


class Building(Tile):
    """A building tile."""

    inventory: dict[str, int] = field(default_factory=dict)
    wear: int
    destruction_threshold: int
    occupants: set["Agent"] = field(default_factory=set)

    @abstractmethod
    def update(self, time: Time) -> None:
        """Update the building."""


class ResourceAssignment:
    """A resource assignment."""

    resource: ResourceTile
    goal: int


class Market(Building):
    """A market tile."""

    def update(self, time: Time) -> None:
        """Update the market."""


class Home(Building):
    """A home tile."""

    wear = 0
    destruction_threshold = 100
    destroyed = False
    agent_assignments: dict["Agent", str] = field(default_factory=dict)
    resource_assignments: dict[str, list[ResourceTile]] = field(default_factory=dict)

    def update(self, time: Time) -> None:
        """Homes degrade 1 point per day."""
        if time.top_of_hour:
            # Repair the home once an hour
            self._repair()
        if time.top_of_day:
            self.wear += 1
            if self.wear >= self.destruction_threshold:
                for agent in self.occupants:
                    agent.alive = False
                self.destroyed = True
                print(f"{self} has been destroyed.")

        for agent in self.occupants:
            agent.update(time)
            if not agent.alive:
                self.occupants.remove(agent)

    def _repair(self) -> None:
        """Repair the home."""
        stone_repair_value = 5
        wood_repair_value = 1

        if self.inventory.get("stone", 0) >= 1:
            if self.wear <= stone_repair_value:
                return
            self.inventory["stone"] -= 1
            self.wear -= stone_repair_value
            return

        if self.wear > 0 and self.inventory.get("wood", 0) >= wood_repair_value:
            self.inventory["wood"] -= 1
            self.wear -= wood_repair_value
            return

    @staticmethod
    def _get_resource_priority(resource: str) -> int:
        """Get the priority of resources for this home."""
        resource_priorities = {
            "wood": 1,
            "stone": 2,
            "gem": 2,
            "food": 10,
        }
        return resource_priorities.get(resource, -int_inf)

    def get_resource_assignment(self, agent: "Agent") -> str:
        """Assign agent to gather resource."""

    def resign_assignment(self, agent: "Agent"):
        """Resign from assignment."""
        # Retrieve resources from agent
        self.inventory.update(agent.inventory)
        agent.inventory.clear()

        # Remove agent from assignments
        self.agent_assignments.pop(agent)


def create_tile(hex_: hexagon.Hex, sprite: arcade.Sprite) -> Tile:  # noqa: PLR0911
    """Create a tile from a hex and a sprite."""
    match sprite.properties.get("class"):

        case "mountain":
            return Mountain(hex=hex_, sprite=sprite)

        case "grass":
            return Grass(hex=hex_, sprite=sprite)

        case "desert":
            return Desert(hex=hex_, sprite=sprite)

        case "forest":
            return Forest(hex=hex_, sprite=sprite)

        case "cactus":
            return Cactus(hex=hex_, sprite=sprite)

        case "stone":
            return Stone(hex=hex_, sprite=sprite)

        case "house":
            return House(hex=hex_, sprite=sprite)

        case "food":
            return Food(hex=hex_, sprite=sprite)

        case "gem":
            return Gem(hex=hex_, sprite=sprite)

        case "market":
            return Market(hex=hex_, sprite=sprite)

    msg = f"Unknown tile class at {hex_}, {sprite.properties.get('class')=}"
    raise ValueError(msg)
