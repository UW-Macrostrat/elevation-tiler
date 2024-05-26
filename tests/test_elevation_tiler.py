from elevation_tiler.cog_layer import get_raster_tile
from morecantile import Tile
from pathlib import Path
from rio_tiler.models import ImageData
from rio_tiler.errors import TileOutsideBounds

here = Path(__file__).parent
dataset = here / "fixtures" / "dem-14-8924-9338-buffered.tif"


def test_acquire_rgb_tile_from_cog():
    # Get a fully overlapping tile from the COG
    tile = Tile(z=14, x=8924, y=9338)
    img = get_raster_tile(dataset, tile.z, tile.x, tile.y)
    assert isinstance(img, ImageData)
    assert img.array.shape == (3, 512, 512)
    assert img.array.dtype == "uint8"

    # Check that the output is a masked array
    assert hasattr(img.array, "mask")

    # Check that the mask is all False
    assert not img.array.mask.any()


def test_partially_overlapping_tile_from_cog():
    # Get a partially overlapping tile from the COG
    tile = Tile(z=14, x=8925, y=9338)
    img = get_raster_tile(dataset, tile.z, tile.x, tile.y)
    assert isinstance(img, ImageData)
    assert img.array.shape == (3, 512, 512)
    assert img.array.dtype == "uint8"

    # Check that the output is a masked array
    assert hasattr(img.array, "mask")

    # Check that some values are masked
    assert img.array.mask.any()


def test_non_overlapping_tile_from_cog():
    # Get a non-overlapping tile from the COG
    tile = Tile(z=14, x=8926, y=9338)
    try:
        get_raster_tile(dataset, tile.z, tile.x, tile.y)
        assert False
    except TileOutsideBounds:
        assert True
