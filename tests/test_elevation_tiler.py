from elevation_tiler.cog_layer import get_raster_tile
from morecantile import Tile
from pathlib import Path
from rio_tiler.models import ImageData
from rio_tiler.errors import TileOutsideBounds
import numpy as N
from PIL import Image
from io import BytesIO

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


def test_overlay_cog_on_png():
    # Get the from the COG with overlay
    tile = Tile(z=14, x=8925, y=9338)
    img = get_raster_tile(dataset, tile.z, tile.x, tile.y)

    png = here / "fixtures" / "mapbox-14-8925-9338.png"
    with Image.open(png) as img0:
        base = N.array(img0)

    # Get the base image dimensions
    h, w = base.shape[:2]
    assert base.shape[2] == 3
    assert h == 512
    assert w == 512
    # Reshape the base image to match the COG
    base = base.transpose(2, 0, 1)

    assert N.allclose(img.array.shape, base.shape)

    # Fill the masked value with the base image
    _array = N.where(img.array.mask, base, img.array.data)
    _array = N.ma.masked_array(_array)
    assert _array.shape == (3, 512, 512)

    img_new = ImageData(_array)

    # Write to an in-memory PNG
    _bytes = img_new.render(add_mask=False)

    # Try reading the PNG back in
    with Image.open(BytesIO(_bytes)) as img1:
        assert img1.size == (512, 512)
        assert img1.format == "PNG"
        assert img1.mode == "RGB"
        arr = N.array(img1)
        assert arr.shape == (512, 512, 3)
        arr = arr.transpose(2, 0, 1)
        assert N.allclose(arr, img_new.array.data)
