from dataclasses import dataclass
from random import randint

from sim import hexagon, tile
from sim.time import Time


@dataclass(kw_only=True)
class Agent:
    """An agent on the map."""

    location: hexagon.Hex
    target_location: hexagon.Hex
    home: tile.Home

    name: str
    fitness_multiplier: float
    age: Time
    satiety: int
    alive: bool = True

    inventory: dict[str, int]

    def __post_init__(self) -> None:
        """Create an agent."""
        self.inventory = self.inventory or {}
        self.satiety = self.satiety or 100
        self.age = self.age or Time(years=randint(18, 45))  # noqa: S311
        self.fitness_multiplier = self.fitness_multiplier or 1.0

    def update(self, time: Time) -> None:
        """Update the agent."""
        if not self.alive:
            msg = f"Agent {self}: Cannot update a dead agent"
            raise ValueError(msg)

        self.age += 1

        if self.age > Time(years=80) or self.satiety < 0:
            self.alive = False
            print(f"{self.name} died\n{self}")

        if self.satiety < 80:
            self.eat()
            self.satiety -= 1

        self.action_points = max(self.calculate_action_points + self.action_points, 100)

    def eat(self) -> None:
        """Eat food."""
        if self.home.inventory.get("food", 0) > 0:
            self.home.inventory["food"] -= 1
            self.satiety += 20

    @property
    def action_points(self) -> int:
        """Get the action points of the agent."""
        return self.action_points

    @action_points.setter
    def action_points(self, value: int) -> None:
        """Set the action points of the agent."""
        if value < 0:
            msg = f"Agent {self}: Action points cannot be negative"
            raise ValueError(msg)
        self.action_points = value

    @property
    def calculate_action_points(self) -> int:
        """Get the speed of the agent.

        Speed is based on age and satiety.
        """
        # cubic regression model for age
        # 1 -> 1
        # 10 -> 10
        # 25 -> 15
        # 50 -> 10
        # 65 -> 4
        # 80 -> 3

        age_multiplier = (
            -0.2213291
            + 1.310579 * self.age.total_years
            - 0.03292493 * self.age.total_years**2
            + 0.0002129029 * self.age.total_years**3
        ) / 15
        assert age_multiplier >= 0

        # Cubic regression model for satiety
        # 100 -> 100
        # 75 -> 90
        # 50 -> 75
        # 25 -> 50
        # 20 -> 40
        # 15 -> 30
        # 10 -> 20
        # 5 -> 10
        satiety_multiplier = (
            -3.509472
            + 2.692242 * self.satiety
            - 0.02765572 * self.satiety**2
            + 0.0001109142 * self.satiety**3
        ) / 100
        assert satiety_multiplier >= 0
        modifier = max(age_multiplier, 1) * max(satiety_multiplier, 1)
        if modifier == 0:
            modifier = 0.01

        if modifier < 0:
            msg = f"Agent {self}: Action points cannot be negative"
            raise ValueError(msg)

        return int(round(modifier * self.fitness_multiplier * 100))
