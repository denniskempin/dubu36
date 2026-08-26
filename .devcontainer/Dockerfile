FROM docker.io/zmkfirmware/zmk-dev-arm:3.2

# git is required for Cloud Agent checkout; sudo is recommended for agent tooling.
USER root
RUN apt-get update \
	&& DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
		ca-certificates \
		curl \
		git \
		sudo \
	&& rm -rf /var/lib/apt/lists/*

COPY .bashrc /tmp/.bashrc
RUN mv /tmp/.bashrc ~/.bashrc
