from elevation_tiler.cog_layer import get_raster_tile
from morecantile import Tile
from os import environ
from pathlib import Path
from rio_tiler.models import ImageData


def test_acquire_rgb_tile_from_cog():
    # Get a fully overlapping tile from the COG
    dataset = Path(environ.get("OVERLAY_DATASET"))
    tile = Tile(z=14, x=8925, y=9338)
    img = get_raster_tile(dataset, tile.z, tile.x, tile.y)
    assert isinstance(img, ImageData)
    assert img.array.shape == (3, 512, 512)
    assert img.array.dtype == "uint8"

    # Check that the output is a masked array
    assert img.array.mask.any()
