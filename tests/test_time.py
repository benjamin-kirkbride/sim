from sim.app.time import (
    DAYS_PER_MONTH,
    HOURS_PER_DAY,
    MONTHS_PER_YEAR,
    STEPS_PER_DAY,
    STEPS_PER_HOUR,
    STEPS_PER_MONTH,
    STEPS_PER_YEAR,
    Time,
)


def test_init():
    t1 = Time()
    assert t1.steps == 0

    t2 = Time(hours=1 / STEPS_PER_HOUR)
    assert t2.steps == 1
    assert t2.total_hours == 0.25

    t3 = Time(hours=1)
    assert t3.steps == STEPS_PER_HOUR
    assert t3.total_hours == 1.0

    t4 = Time(days=1)
    assert t4.steps == STEPS_PER_DAY
    assert t4.total_days == 1.0
    assert t4.total_hours == HOURS_PER_DAY

    t5 = Time(years=STEPS_PER_DAY / STEPS_PER_YEAR)
    assert t5.total_days == 1


def test_rounding():
    t1 = Time(hours=1 / (STEPS_PER_HOUR + 1), non_int_steps=True)
    assert t1.steps == 1


def test_conversions():
    assert str(Time(steps=0)) == "00000-00-00 00:00"
    assert Time(steps=0).year == 0
    assert Time(steps=0).month == 0
    assert Time(steps=0).day == 0
    assert Time(steps=0).hour == 0
    assert Time(steps=0).minute == 0

    assert Time(steps=STEPS_PER_HOUR).year == 0
    assert Time(steps=STEPS_PER_HOUR).month == 0
    assert Time(steps=STEPS_PER_HOUR).day == 0
    assert Time(steps=STEPS_PER_HOUR).hour == 1
    assert Time(steps=STEPS_PER_HOUR).total_hours == 1.0
    assert Time(steps=STEPS_PER_HOUR).minute == 0
    assert Time(steps=STEPS_PER_HOUR).total_minutes == 60

    assert Time(steps=STEPS_PER_DAY).year == 0
    assert Time(steps=STEPS_PER_DAY).month == 0
    assert Time(steps=STEPS_PER_DAY).day == 1
    assert Time(steps=STEPS_PER_DAY).total_days == 1.0
    assert Time(steps=STEPS_PER_DAY).hour == 0
    assert Time(steps=STEPS_PER_DAY).total_hours == 24.0
    assert Time(steps=STEPS_PER_DAY).minute == 0
    assert Time(steps=STEPS_PER_DAY).total_minutes == 1440

    assert Time(steps=STEPS_PER_MONTH).year == 0
    assert Time(steps=STEPS_PER_MONTH).month == 1
    assert Time(steps=STEPS_PER_MONTH).total_months == 1.0
    assert Time(steps=STEPS_PER_MONTH).day == 0
    assert Time(steps=STEPS_PER_MONTH).total_days == 8.0
    assert Time(steps=STEPS_PER_MONTH).hour == 0
    assert Time(steps=STEPS_PER_MONTH).total_hours == 192.0
    assert Time(steps=STEPS_PER_MONTH).minute == 0
    assert Time(steps=STEPS_PER_MONTH).total_minutes == 11520.0

    assert Time(steps=STEPS_PER_YEAR).year == 1
    assert Time(steps=STEPS_PER_YEAR).total_years == 1.0
    assert Time(steps=STEPS_PER_YEAR).month == 0
    assert Time(steps=STEPS_PER_YEAR).total_months == 12.0
    assert Time(steps=STEPS_PER_YEAR).day == 0
    assert Time(steps=STEPS_PER_YEAR).total_days == 96.0
    assert Time(steps=STEPS_PER_YEAR).hour == 0
    assert Time(steps=STEPS_PER_YEAR).total_hours == 2304.0
    assert Time(steps=STEPS_PER_YEAR).minute == 0
    assert Time(steps=STEPS_PER_YEAR).total_minutes == 138240.0

    assert Time(steps=STEPS_PER_YEAR * 2).year == 2
    assert Time(steps=STEPS_PER_MONTH + 1).month == 1
    assert Time(steps=STEPS_PER_MONTH + 4).hour == 1


def test_math():
    t1 = Time(hours=1)
    t2 = Time(days=1)

    assert t1 + t2 == Time(steps=STEPS_PER_DAY + STEPS_PER_HOUR)
    assert t1 + t2 == t2 + t1

    assert t1 - t2 == Time(steps=STEPS_PER_HOUR - STEPS_PER_DAY)
