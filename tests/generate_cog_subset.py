"""Generate a spatial subset of COG data for testing purposes.

The resulting COG will fully overlap with the tile (14, 8924, 9338), with
a 10-pixel buffer on all sides. This will allow other tiles (e.g., (14, 8925, 9338))
to be partially overlapping and test overlay functionality.
"""

from rio_tiler.io import COGReader
from sys import argv
from rio_cogeo.cogeo import cog_translate
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds
from rio_cogeo.profiles import cog_profiles

# Define the input and output paths
input_path = argv[1]
# Define the tile and buffer size
tile = (14, 8924, 9338)
z, x, y = tile
buffer = 30
output_path = f"tests/fixtures/dem-{z}-{x}-{y}-buffered.tif"

# Create a COGReader object
with COGReader(input_path) as reader:
    # Get the tile
    img = reader.tile(
        tile[1],
        tile[2],
        tile[0],
        tilesize=512,
        buffer=buffer,
    )

    # Profile for the output COG
    size = dict(
        width=img.array.shape[2],
        height=img.array.shape[1],
    )
    nodata = img.array.fill_value

    profile = dict(
        driver="GTiff",
        crs=img.crs,
        count=img.count,
        dtype=img.array.dtype,
        transform=from_bounds(*img.bounds, **size),
        nodata=nodata,
        **size,
    )

    with MemoryFile() as memfile:
        with memfile.open(**profile) as mem:
            # Populate the input file with numpy array
            mem.write(img.array)

            dst_profile = cog_profiles.get("deflate")
            cog_translate(
                mem,
                output_path,
                dst_profile,
            )
