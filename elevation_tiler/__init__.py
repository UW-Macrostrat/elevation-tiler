from fastapi import FastAPI, HTTPException, Request
import httpx
import os

app = FastAPI()


@app.get("/tiles/{z}/{x}/{y}")
async def get_tile(request: Request, z: int, x: int, y: int):
    try:
        # Replace the URL with the actual tile server URL
        base_url = os.environ.get("PROXY_TILE_LAYER")
        tile_url = base_url.format(z=z, x=x, y=y)

        async with httpx.AsyncClient() as client:
            headers = dict(
                request.headers
            )  # Pass request headers to the upstream server

            # Pass query parameters to the upstream server
            params = dict(request.query_params)
            response = await client.get(tile_url, headers=headers, params=params)
            response.raise_for_status()

            return response.content

    except httpx.HTTPError:
        raise HTTPException(status_code=404, detail="Tile not found")


if __name__ == "__main__":
    from dotenv import load_dotenv
    import uvicorn

    load_dotenv()

    uvicorn.run(app)
