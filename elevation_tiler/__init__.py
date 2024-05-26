from fastapi import FastAPI, HTTPException, Request, Response
import httpx
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
base_url = os.environ.get("PROXY_TILE_LAYER")


@app.get("/tiles/{z}/{x}/{y}")
async def get_tile(request: Request, z: int, x: int, y: int):
    try:
        # Replace the URL with the actual tile server URL
        tile_url = base_url.format(z=z, x=x, y=y)

        async with httpx.AsyncClient() as client:
            headers = dict(
                request.headers
            )  # Pass request headers to the upstream server

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
