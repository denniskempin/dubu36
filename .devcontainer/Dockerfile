FROM docker.io/zmkfirmware/zmk-dev-arm:4.1

COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /uvx /bin/

COPY --chmod=644 zmk-workspace.sh /etc/profile.d/zmk-workspace.sh
