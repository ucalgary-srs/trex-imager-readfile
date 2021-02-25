__version__ = "1.0.3"

# core functions for easy use
from .blueline import read as read_blueline
from .nir import read as read_nir
from .rgb import read as read_rgb
# from .rgb import read_rgb_burst
from .spectrograph import read as read_spectrograph

# module imports
from trex_imager_readfile import blueline
from trex_imager_readfile import nir
from trex_imager_readfile import rgb
from trex_imager_readfile import spectrograph
