from rio_rgbify.encoders import data_to_rgb
from morecantile import Tile
from rio_tiler.io import COGReader
from rio_tiler.models import ImageData
from pathlib import Path
import numpy as N


def get_raster_tile(dataset: Path, z: int, x: int, y: int):
    """Get a tile of a raster dataset in terrain RGB format."""

    # Create a COGReader object
    with COGReader(dataset) as reader:
        img = reader.tile(x, y, z, tilesize=512)
        # Convert NaNs to zeros
        # Fill all NaN values with zeros
        src = img.array[0]

        rgb = data_to_rgb(src, -10000, 0.1)
        # Stack three copies of the mask
        mask = N.stack([src.mask] * 3, axis=-1)
        masked = N.ma.masked_array(rgb, mask=mask)
        new_image = ImageData(masked)
        return new_image
