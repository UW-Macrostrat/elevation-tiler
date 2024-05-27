from rio_rgbify.encoders import data_to_rgb
from morecantile import Tile
from rio_tiler.io import COGReader
from rio_tiler.models import ImageData
from pathlib import Path
import numpy as N


def get_raster_tile(dataset: Path, z: int, x: int, y: int, tilesize: int = 512):
    """Get a tile of a raster dataset in terrain RGB format."""

    # Create a COGReader object
    with COGReader(dataset) as reader:
        img = reader.tile(x, y, z, tilesize=tilesize)
        return convert_to_rgb(img)


def convert_to_rgb(img: ImageData) -> ImageData:
    """Convert a DEM tile to a terrain RGB tile."""
    mask = img.array.mask

    # Create a three-band mask
    mask = N.stack([mask] * 3, axis=0)
    rgb = data_to_rgb(img.array[0], -10000, 0.1)
    rgb = N.ma.array(rgb, mask=mask)
    return ImageData(rgb)
