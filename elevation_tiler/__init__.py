from fastapi import FastAPI, HTTPException, Request, Response
import httpx
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.models import ImageData
from PIL import Image
from io import BytesIO
import numpy as N
from contextvars import ContextVar

from .cog_layer import get_raster_tile

load_dotenv()

app = FastAPI()
base_url = os.environ.get("PROXY_TILE_LAYER")
overlay_dataset = os.environ.get("OVERLAY_DATASET")

_tilesize = ContextVar("tilesize", default=None)


@app.get("/tiles/{z}/{x}/{y}")
async def get_tile(request: Request, z: int, x: int, y: int):
    tile_url = base_url.format(z=z, x=x, y=y)
    base = None
    overlay = None
    tilesize = _tilesize.get()
    if tilesize is None:
        # We haven't set the tilesize yet, so we need to load a tile to get the size
        base = await get_base_tile(tile_url, dict(request.query_params))
        # Set the tilesize from this request
        _img = create_image_from_bytes(base.content)
        _tilesize.set(_img.array.shape[1])
        tilesize = _tilesize.get()

    try:
        overlay = get_raster_tile(overlay_dataset, z, x, y, tilesize=tilesize)
    except TileOutsideBounds:
        pass

    if overlay is not None and not overlay.array.mask.any():
        # The overlay fully covers the tile, so there is no need to fetch the base tile
        return Response(content=overlay.render(add_mask=False), media_type="image/png")

    # Get the base tile if we haven't already
    if base is None:
        base = await get_base_tile(tile_url, dict(request.query_params))

    if overlay is None:
        # There is no overlay content, so just return the base tile
        return Response(content=base.content, headers=base.headers)

    # Merge the base image with the overlay
    base_img = create_image_from_bytes(base.content)
    img = merge_base_image_with_overlay(base_img, overlay)
    content = img.render(add_mask=False)
    return Response(content=content)


async def get_base_tile(url: str, params: dict) -> Response:
    try:
        async with httpx.AsyncClient() as client:
            print(url)
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response
    except httpx.HTTPError:
        raise HTTPException(status_code=404, detail="Tile not found")


def create_image_from_bytes(_bytes: bytes) -> ImageData:
    with Image.open(BytesIO(_bytes)) as img1:
        # Remove alpha channel if it exists
        img1 = img1.convert("RGB")
        arr = N.array(img1)
        # transpose the array to match the rio-tiler format
        arr = arr.transpose(2, 0, 1)
        return ImageData(arr)


def merge_base_image_with_overlay(base: ImageData, overlay: ImageData) -> ImageData:
    # Get the from the COG with overlay

    # Fill the masked value with the base image

    # Create a constant-valued array with the same shape as the base image

    assert N.allclose(overlay.array.shape, base.array.shape)

    ##print(overlay.array)
    ##_array = overlay.array

    # Fill the masked value with zeros
    # _array = overlay.array.filled(0)

    # expand_mask = N.stack([overlay.array.mask] * 3, axis=-1)
    # assert expand_mask.shape == base.array.shape
    # assert expand_mask.shape == overlay.array.shape

    arr = base.array.data
    mask = overlay.array.mask
    arr[~mask] = overlay.array.data[~mask]

    return ImageData(arr)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"proxy-url": base_url}
