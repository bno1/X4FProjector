"""
This module exports loaders, functions that parse the game files and return
data dictionaries.
"""


__all__ = [
    'engine_loader',
    'missilelauncher_loader',
    'shield_loader',
    'ship_loader',
    'weapon_loader',
    'ware_loader',
]


from loaders.macro_loaders import engine_loader
from loaders.macro_loaders import missilelauncher_loader
from loaders.macro_loaders import shield_loader
from loaders.macro_loaders import ship_loader
from loaders.macro_loaders import weapon_loader
from loaders.ware_loader import ware_loader
