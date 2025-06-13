# We need to use a Python image with rasterio
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.11.0

# Install python from deadsnakes PPA
RUN apt-get update -y && \
  apt-get install -y --no-install-recommends \
  software-properties-common && \
  add-apt-repository ppa:deadsnakes/ppa && \
  apt-get update -y && \
  apt-get install -y --no-install-recommends \
    gdb \
    g++ \
    make \
    python3.11 \
    python3.11-venv \
    python3.11-dev && \
  rm -rf /var/lib/apt/lists/*

# Install PIP
RUN python3.11 -m ensurepip && \
    python3.11 -m pip install uv

# Set the working directory in the container
WORKDIR /app

# Setup environment for UV
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy
# Ensure UV uses the correct Python version
ENV UV_PYTHON=python3.11

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Remove build dependencies
RUN apt-get remove -y \
  software-properties-common \
  g++ \
  make \
  python3.11-dev && \
  rm -rf /var/lib/apt/lists/*

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"


# Run the FastAPI application by default
# Uses `fastapi dev` to enable hot-reloading when the `watch` sync occurs
# Uses `--host 0.0.0.0` to allow access from outside the container
CMD ["fastapi", "run", "--host", "0.0.0.0", "elevation_tiler"]


