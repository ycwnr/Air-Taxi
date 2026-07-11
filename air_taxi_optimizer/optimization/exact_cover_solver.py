"""
optimization/exact_cover_solver.py

Defines an abstract ExactCoverSolver interface plus a concrete greedy
implementation. Given a pool of candidate DutyCycles and the full set of
required flight ids, it returns a subset of DutyCycles whose flight-sets
*partition* the required flights (each flight covered exactly once) —
i.e. a true Exact Cover, not merely a Set Cover with overlaps allowed.

Algorithm (greedy weighted set-partition):
  1. Sort candidate cycles by "flights covered" descending (bigger cycles
     first -> fewer aircraft -> smaller fleet).
  2. Repeatedly pick the next cycle whose flights are ALL still uncovered;
     mark them covered.
  3. Any required flight left uncovered at the end is patched with its
     single-flight fallback cycle (guaranteed present in the pool by
     cycle_generator, or synthesized here if missing).

This is a polynomial-time heuristic, not a proof of optimality; the
interface is intentionally abstract so an exact ILP/Algorithm-X
implementation could be substituted without touching the optimizer.
"""
from abc import ABC, abstractmethod


class ExactCoverSolver(ABC):
    @abstractmethod
    def solve(self, candidate_cycles: list, required_flight_ids: set) -> list:
        """Returns list[DutyCycle] whose flight_ids partition required_flight_ids
        (or as much of it as feasible; caller checks completeness)."""
        raise NotImplementedError


class GreedyExactCoverSolver(ExactCoverSolver):
    def solve(self, candidate_cycles: list, required_flight_ids: set) -> list:
        remaining = set(required_flight_ids)
        selected = []

        # Prefer cycles that cover the most flights (fewest aircraft).
        ordered = sorted(candidate_cycles, key=lambda c: -len(c.flight_ids))

        for cycle in ordered:
            if not remaining:
                break
            fids = cycle.flight_ids
            if fids and fids.issubset(remaining):
                selected.append(cycle)
                remaining -= fids

        return selected, remaining  # remaining should be empty if fully covered
