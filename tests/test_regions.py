"""The DFW location rule."""

import pytest

from job_watcher.regions import in_dfw


@pytest.mark.parametrize("location", [
    "Dallas, TX",
    "Plano, Texas",
    "Irving, Texas, United States",
    "TX - Plano",
    "Richardson, TX 75082",
    "Fort Worth",                    # standalone
    "Dallas-Fort Worth Metroplex",
    "Westlake, TX",
    "North Richland Hills, TX",
    "Las Colinas",
    "US-TX-Dallas",
])
def test_in_dfw(location):
    assert in_dfw(location)


@pytest.mark.parametrize("location", [
    "Arlington, VA",                 # same city name, other state
    "Plano, IL",
    "Frisco, CO",
    "Texas - Abilene",               # Texas, but not DFW
    "Austin, TX",
    "Houston, Texas",
    "Dallas",                        # no state: could be Dallas, GA
    "Westlake",
    "Remote - USA",
    "2 Locations",
    "Allentown, PA",                 # 'Allen' inside a word
    "",
])
def test_not_in_dfw(location):
    assert not in_dfw(location)


def test_texas_any_case_but_tx_upper():
    assert in_dfw("Addison, TEXAS, United States")
    assert not in_dfw("Addison, tx")  # lower-case 'tx' is too likely to be part of other text


def test_sherman_is_outside_the_metro():
    assert not in_dfw("Sherman, TX")
