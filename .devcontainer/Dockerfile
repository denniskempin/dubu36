FROM docker.io/zmkfirmware/zmk-dev-arm:4.1

COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /uvx /bin/

# cairosvg (make diagrams / make all) dlopens libcairo at import time. The
# firmware image does not ship it.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY --chmod=644 zmk-workspace.sh /etc/profile.d/zmk-workspace.sh
