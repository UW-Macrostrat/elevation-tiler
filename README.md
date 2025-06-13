A prototype tile server that can overlay a local COG on a proxied global layer.

Right now, this is configured with environment variables:
```bash
# Global tile layer to proxy
PROXY_TILE_LAYER=https://api.mapbox.com/raster/v1/mapbox.mapbox-terrain-dem-v1/{z}/{x}/{y}.webp
# Local or cloud-stored COG to overlay
OVERLAY_DATASET=data/S23982E015994_S24407E016361_UM_DSM.tif
```

Eventually, we will extend and integrate this capability with other
tools.
