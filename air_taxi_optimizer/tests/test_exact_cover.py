import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.flight import Flight
from core.duty_cycle import DutyCycle
from optimization.exact_cover_solver import GreedyExactCoverSolver


def _cycle(flights):
    return DutyCycle(flights=flights, aircraft_class="4seat", is_feasible=True)


def test_exact_cover_picks_disjoint_full_partition():
    f1 = Flight("1", "a", "b", 10, 2, 4)
    f2 = Flight("2", "b", "c", 10, 2, 4)
    f3 = Flight("3", "c", "d", 10, 2, 4)

    big_cycle = _cycle([f1, f2, f3])   # covers all three
    overlapping_cycle = _cycle([f1])   # overlaps with big_cycle on f1
    solver = GreedyExactCoverSolver()

    required = {"1", "2", "3"}
    selected, uncovered = solver.solve([big_cycle, overlapping_cycle], required)

    assert len(uncovered) == 0
    assert len(selected) == 1
    assert selected[0] is big_cycle


def test_exact_cover_falls_back_to_singles_when_no_big_cycle_exists():
    f1 = Flight("1", "a", "b", 10, 2, 4)
    f2 = Flight("2", "x", "y", 10, 2, 4)  # unrelated leg, no chain possible
    single1 = _cycle([f1])
    single2 = _cycle([f2])
    solver = GreedyExactCoverSolver()

    selected, uncovered = solver.solve([single1, single2], {"1", "2"})
    assert len(uncovered) == 0
    assert len(selected) == 2


if __name__ == "__main__":
    test_exact_cover_picks_disjoint_full_partition()
    test_exact_cover_falls_back_to_singles_when_no_big_cycle_exists()
    print("test_exact_cover.py: all tests passed")
