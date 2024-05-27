from elevation_tiler.cog_layer import get_raster_tile
from morecantile import Tile
from pathlib import Path
from rio_tiler.models import ImageData
from rio_tiler.errors import TileOutsideBounds
import numpy as N
from PIL import Image
from io import BytesIO
from elevation_tiler import create_image_from_bytes, merge_base_image_with_overlay
from rio_rgbify.encoders import _decode
from rio_tiler.io import COGReader

here = Path(__file__).parent
dataset = here / "fixtures" / "dem-14-8924-9338-buffered.tif"


def test_acquire_rgb_tile_from_cog():
    # Get a fully overlapping tile from the COG
    # NOTE: this type does not appear to actually fully overlap
    tile = Tile(z=14, x=8924, y=9338)
    img = get_raster_tile(dataset, tile.z, tile.x, tile.y)
    assert isinstance(img, ImageData)
    assert img.array.shape == (3, 512, 512)
    assert img.array.dtype == "uint8"

    # Check that the output is a masked array
    assert hasattr(img.array, "mask")

    # Check that the mask is all False
    # assert not img.array.mask.any()


def test_pixel_value_recovery_from_cog():
    tile = Tile(z=14, x=8924, y=9338)
    img = get_raster_tile(dataset, tile.z, tile.x, tile.y)
    png = img.render(add_mask=False)
    img1 = create_image_from_bytes(png)
    assert N.allclose(img1.array.data, img.array.data)


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


def test_overlay_cog_on_png_internal():
    # Get the from the COG with overlay
    tile = Tile(z=14, x=8925, y=9338)
    img = get_raster_tile(dataset, tile.z, tile.x, tile.y)

    png = here / "fixtures" / "mapbox-14-8925-9338.png"
    with open(png, "rb") as f:
        _bytes = f.read()
    base = create_image_from_bytes(_bytes)

    assert N.allclose(img.array.shape, base.array.shape)

    # Fill the masked value with the base image
    img_new = merge_base_image_with_overlay(base, img)

    # Write to an in-memory PNG
    _bytes = img_new.render(add_mask=False)

    # Try reading the PNG back in
    img2 = create_image_from_bytes(_bytes)
    assert N.allclose(img2.array.data, img_new.array.data)

    # Test that we get reasonable elevations
    arr = img_new.array

    # Check that there are no masked values in either image
    assert not N.any(base.array.mask)
    assert not N.any(img_new.array.mask)

    base_elevations = reconstruct_elevation(base.array)
    # # Check that the base elevations are within a reasonable range
    # assert base_elevations.min() > 0
    # assert base_elevations.max() < 2500

    # elevations = reconstruct_elevation(arr)

    # # Check that the elevations are within a reasonable range
    # assert elevations.min() > 0
    # assert elevations.max() < 2500


def reconstruct_elevation(arr):
    return _decode(arr, -10000, 0.1)


def test_reasonable_elevations_base():
    png = here / "fixtures" / "mapbox-14-8925-9338.png"
    base = create_image_from_bytes(png.read_bytes())

    base_elevations = reconstruct_elevation(base.array)
    # Check that the base elevations are within a reasonable range
    assert base_elevations.min() > 0
    assert base_elevations.max() < 2500


def test_reasonable_elevations_overlay():
    tile = Tile(z=14, x=8924, y=9338)

    with COGReader(dataset) as reader:
        img0 = reader.tile(tile.x, tile.y, tile.z, tilesize=512)
    assert img0.array.min() > 0
    assert img0.array.max() < 2500

    img = get_raster_tile(dataset, tile.z, tile.x, tile.y)

    elevations = reconstruct_elevation(img.array)

    # Check that the elevations are within a reasonable range
    assert elevations.min() > 0
    assert elevations.max() < 2500
