"""The blade profile."""
import math


def bevel_height(p):
    return (p["wall"] - p["blade"]) / math.tan(math.radians(p["blade_angle"]))
