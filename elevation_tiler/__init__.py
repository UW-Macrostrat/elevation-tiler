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

from .cog_layer import get_raster_tile

load_dotenv()

app = FastAPI()
base_url = os.environ.get("PROXY_TILE_LAYER")
overlay_dataset = os.environ.get("OVERLAY_DATASET")


@app.get("/tiles/{z}/{x}/{y}")
async def get_tile(request: Request, z: int, x: int, y: int):

    overlay = None
    try:
        overlay = get_raster_tile(overlay_dataset, z, x, y)
        if not overlay.array.mask.any():
            # The overlay fully covers the tile, so there is no need to fetch the base tile
            return Response(
                content=overlay.render(add_mask=False), media_type="image/png"
            )
    except TileOutsideBounds:
        pass

    # Get the base tile
    tile_url = base_url.format(z=z, x=x, y=y)

    try:
        # Replace the URL with the actual tile server URL
        async with httpx.AsyncClient() as client:
            # Pass query parameters to the upstream server
            params = dict(request.query_params)
            response = await client.get(tile_url, headers={}, params=params)
            response.raise_for_status()

            if overlay is None:
                # There is no overlay content, so just return the base tile
                return Response(content=response.content, headers=response.headers)

            # Merge the base image with the overlay
            base = create_image_from_bytes(response.content)
            img = merge_base_image_with_overlay(base, overlay)
            content = img.render(add_mask=False)
            return Response(content=content)

    except httpx.HTTPError:
        raise HTTPException(status_code=404, detail="Tile not found for basemap")


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
