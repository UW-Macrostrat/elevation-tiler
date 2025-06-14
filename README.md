A prototype tile server that can overlay a local COG on a proxied global layer.

Eventually, we will extend and integrate this capability with other
tools.

This is configured to work with a local or remotely stored COG and a global
layer which will be used to fill in data gaps.

# Using the service

- Provide a COG URL using the `x-overlay-layer` query parameter.
- Provide a global overlay URL using the `x-fallback-layer` query parameter.

The fallback layer defaults to Mapbox Terrain DEM if not specified, or it can be set
usign the `FALLBACK_LAYER` environment variable.
The suffix `{z}/{x}/{y}.{ext}` is appended to layer URLs to fetch tiles.

# TODO

- Integrate with JSON Web Token (JWT) authentication
- More flexibility in service configuration
- More options for image processing
- Serve COG footprints
