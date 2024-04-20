from dataclasses import InitVar, dataclass
from functools import cached_property
from math import isclose

STEPS_PER_HOUR = 4
HOURS_PER_DAY = 24
DAYS_PER_MONTH = 8
MONTHS_PER_YEAR = 12

STEPS_PER_DAY = STEPS_PER_HOUR * HOURS_PER_DAY
STEPS_PER_MONTH = STEPS_PER_DAY * DAYS_PER_MONTH
STEPS_PER_YEAR = STEPS_PER_MONTH * MONTHS_PER_YEAR


@dataclass(frozen=True, kw_only=True)
class Time:
    """Simulation time class.

    Attributes:
        steps: The number of steps that have passed.
        hours: The number of hours that have passed.
        days: The number of days that have passed.
        months: The number of months that have passed.
        years: The number of years that have passed.

    Args:
        steps: Steps to add to steps attribute.
        hours: Hours to add to steps attribute.
        days: Days to add to steps attribute.
        months: Months to add to steps attribute.
        years: Years to add to steps attribute.
        non_int_steps: Whether to accept (and round) a non-int number of steps.
    """

    steps: int = 0
    hours: InitVar[float | None] = None
    days: InitVar[float | None] = None
    months: InitVar[float | None] = None
    years: InitVar[float | None] = None
    non_int_steps: InitVar[bool] = False

    def __post_init__(  # noqa: PLR0913
        self,
        hours: float | None,
        days: float | None,
        months: float | None,
        years: float | None,
        non_int_steps: bool,
    ) -> None:
        """Create a time object."""
        steps = float(self.steps)
        if hours is not None:
            steps += hours * STEPS_PER_HOUR
        if days is not None:
            steps += days * STEPS_PER_DAY
        if months is not None:
            steps += months * STEPS_PER_MONTH
        if years is not None:
            steps += years * STEPS_PER_YEAR

        if non_int_steps:
            rounded_steps = int(round(steps))
        else:
            rounded_steps = int(round(steps))
            if not isclose(steps, rounded_steps, abs_tol=1e-14):
                raise ValueError(f"steps must be an integer, is {steps}")

        object.__setattr__(self, "steps", rounded_steps)

    def __str__(self) -> str:
        """Return the time as a string."""
        return f"{self.year:05}-{self.month:02}-{self.day:02} {self.hour:02}:{self.minute:02}"

    def __add__(self, other: "Time | int") -> "Time":
        """Add two times together."""
        if isinstance(other, int):
            return Time(steps=self.steps + other)

        return Time(steps=self.steps + other.steps)

    def __sub__(self, other: "Time") -> "Time":
        """Subtract two times."""
        return Time(steps=self.steps - other.steps)

    def __mul__(self, k: int) -> "Time":
        """Multiply a time by a scalar."""
        return Time(steps=self.steps * k)

    def __neg__(self) -> "Time":
        """Negate a time."""
        return Time(steps=-self.steps)

    def __eq__(self, other: object) -> bool:
        """Check if two times are equal."""
        if getattr(other, "steps", None) is None:
            return False
        return bool(self.steps == other.steps)  # type: ignore[attr-defined]

    def __lt__(self, other: "Time") -> bool:
        """Check if one time is less than another."""
        return self.steps < other.steps

    def __le__(self, other: "Time") -> bool:
        """Check if one time is less than or equal to another."""
        return self.steps <= other.steps

    def __gt__(self, other: "Time") -> bool:
        """Check if one time is greater than another."""
        return self.steps > other.steps

    def __ge__(self, other: "Time") -> bool:
        """Check if one time is greater than or equal to another."""
        return self.steps >= other.steps

    # FIXME: is caching these actually faster?
    @cached_property
    def year(self) -> int:
        """Get the year."""
        return self.steps // STEPS_PER_YEAR

    @cached_property
    def top_of_year(self) -> bool:
        """Check if the time is at the top of the year."""
        return self.steps % STEPS_PER_YEAR == 0

    @cached_property
    def total_years(self) -> float:
        """Get the total number of years."""
        return self.steps / STEPS_PER_YEAR

    @cached_property
    def month(self) -> int:
        """Get the month."""
        return (self.steps % STEPS_PER_YEAR) // STEPS_PER_MONTH

    @cached_property
    def top_of_month(self) -> bool:
        """Check if the time is at the top of the month."""
        return self.steps % STEPS_PER_MONTH == 0

    @cached_property
    def total_months(self) -> float:
        """Get the total number of months."""
        return self.steps / STEPS_PER_MONTH

    @cached_property
    def day(self) -> int:
        """Get the day."""
        return (self.steps % STEPS_PER_MONTH) // STEPS_PER_DAY

    @cached_property
    def top_of_day(self) -> bool:
        """Check if the time is at the top of the day."""
        return self.steps % STEPS_PER_DAY == 0

    @cached_property
    def total_days(self) -> float:
        """Get the total number of days."""
        return self.steps / STEPS_PER_DAY

    @cached_property
    def hour(self) -> int:
        """Get the hour."""
        return (self.steps % STEPS_PER_DAY) // STEPS_PER_HOUR

    @cached_property
    def top_of_hour(self) -> bool:
        """Check if the time is at the top of the hour."""
        return self.steps % STEPS_PER_HOUR == 0

    @cached_property
    def total_hours(self) -> float:
        """Get the total number of hours."""
        return self.steps / STEPS_PER_HOUR

    @cached_property
    def minute(self) -> int:
        """Get the minute."""
        return self.steps % STEPS_PER_HOUR * (60 // STEPS_PER_HOUR)

    @cached_property
    def total_minutes(self) -> float:
        """Get the total number of minutes."""
        return self.steps / STEPS_PER_HOUR * 60
