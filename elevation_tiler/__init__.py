from fastapi import FastAPI, HTTPException, Request, Response
import httpx
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from rio_tiler.errors import TileOutsideBounds

from .cog_layer import get_raster_tile

load_dotenv()

app = FastAPI()
base_url = os.environ.get("PROXY_TILE_LAYER")
overlay = os.environ.get("OVERLAY_DATASET")


@app.get("/tiles/{z}/{x}/{y}")
async def get_tile(request: Request, z: int, x: int, y: int):

    # try:
    #     img = get_raster_tile(overlay, z, x, y)
    #     # Fill masked values with zeros
    #     img.array = img.array.filled(0)

    #     return Response(content=img.render(), media_type="image/png")
    # except TileOutsideBounds:
    #     print(f"{z} {x} {y} is completely outside bounds")

    tile_url = base_url.format(z=z, x=x, y=y)

    try:
        # Replace the URL with the actual tile server URL
        async with httpx.AsyncClient() as client:
            # Pass query parameters to the upstream server
            params = dict(request.query_params)
            response = await client.get(tile_url, headers={}, params=params)
            response.raise_for_status()

            return Response(content=response.content, headers=response.headers)

    except httpx.HTTPError:
        raise HTTPException(status_code=404, detail="Tile not found")


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
