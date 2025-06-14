from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
import httpx
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.models import ImageData
from PIL import Image
from io import BytesIO
import numpy as N
from contextvars import ContextVar
from typing import Optional
from logging import getLogger
from os import environ

from .cog_layer import get_raster_tile

load_dotenv()

FALLBACK_LAYER=environ.get("FALLBACK_LAYER", "https://api.mapbox.com/raster/v1/mapbox.mapbox-terrain-dem-v1")


log = getLogger("uvicorn.error")

app = FastAPI()

_tilesize = ContextVar("tilesize", default=None)

@app.get("/tiles/{z}/{x}/{y}")
@app.get("/tiles/{z}/{x}/{y}.{ext}")
async def get_tile(request: Request, z: int, x: int, y: int, ext: Optional[str] = None):
    # Parse required query parameters
    params = dict(request.query_params)

    fallback_url = params.pop("x-fallback-layer", FALLBACK_LAYER)
    overlay_layer = params.pop("x-overlay-layer")

    fallback_url += f"/{z}/{x}/{y}"
    if ext:
        fallback_url += f".{ext}"

    fallback_url = get_base_url(fallback_url, params)

    base = None # The base tile
    overlay = None # The overlay tile

    tilesize = _tilesize.get()
    if tilesize is None:
        # We haven't set the tilesize yet, so we need to load a tile to get the size
        base = await get_base_tile(fallback_url)
        # Set the tilesize from this request
        _img = create_image_from_bytes(base.content)
        _tilesize.set(_img.array.shape[1])
        tilesize = _tilesize.get()
        log.debug("Setting tilesize to %d", tilesize)

    try:
        # This is where we could add advanced logic for overlaying multiple datasets
        log.debug("Subsetting overlay tile from: %s", overlay_layer)
        overlay = get_raster_tile(overlay_layer, z, x, y, tilesize=tilesize)
    except TileOutsideBounds:
        pass

    if overlay is not None and not overlay.array.mask.any():
        # The overlay fully covers the tile, so there is no need to fetch the base tile
        return Response(content=overlay.render(add_mask=False), media_type="image/png")

    if overlay is None:
        # There is no overlay content, so just proxy the base tile
        log.debug("Redirecting to base tile: %s", fallback_url)
        return RedirectResponse(url=fallback_url, status_code=307)

    # Here, we have both a base tile and an overlay tile that we need to merge.
    # Get the base tile if we haven't already
    if base is None:
        base = await get_base_tile(fallback_url)

    # Create a merged overlay image
    # Merge the base image with the overlay
    base_img = create_image_from_bytes(base.content)
    img = merge_base_image_with_overlay(base_img, overlay)
    content = img.render(add_mask=False)
    return Response(content=content, media_type="image/png")


def get_base_url(url: str, params: dict) -> str:
    """Construct a redirect URL with the given base URL and parameters."""
    if params:
        qp = [f"{k}={v}" for k, v in params.items() if v is not None]
        url += "?" + "&".join(qp)
    return url

async def get_base_tile(url: str) -> Response:
    try:
        async with httpx.AsyncClient() as client:
            log.debug("Fetching base tile: %s", url)
            response = await client.get(url)
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
    """Merge the overlay dataset onto the base dataset."""
    assert N.allclose(overlay.array.shape, base.array.shape)

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

