"""Deterministic UUIDs: the generator draws them in a fixed order from a seeded stream, so a rebuild reproduces
byte-identical KiCad files (clean diffs) while every item still gets a unique id."""
import random
import uuid

_rng = random.Random(0x0BF2C)


def U():
    return str(uuid.UUID(int=_rng.getrandbits(128), version=4))


def reset(seed=0x0BF2C):
    _rng.seed(seed)
