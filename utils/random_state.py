"""utils/random_state.py — single seeded RNG source for reproducibility."""
import random
import config


def seeded_rng(seed=None) -> random.Random:
    return random.Random(seed if seed is not None else config.RANDOM_SEED)
