"""
optimization/base_optimizer.py — Strategy-pattern base class so GA/ACO/PSO
are interchangeable from main.py.
"""
from abc import ABC, abstractmethod


class MetaheuristicOptimizer(ABC):
    def __init__(self, ordered_vertiport_ids, required_flights, specs, dist_matrix, **kwargs):
        self.ordered_vertiport_ids = ordered_vertiport_ids
        self.required_flights = required_flights
        self.specs = specs
        self.dist_matrix = dist_matrix
        self.history = []

    @abstractmethod
    def initialize_population(self):
        raise NotImplementedError

    @abstractmethod
    def evaluate_population(self, population):
        raise NotImplementedError

    @abstractmethod
    def evolve_step(self, population, scored):
        raise NotImplementedError

    def stopping_criterion(self, iteration, max_iterations):
        return iteration >= max_iterations

    @abstractmethod
    def run(self):
        """Returns dict with best solution + diagnostics."""
        raise NotImplementedError
