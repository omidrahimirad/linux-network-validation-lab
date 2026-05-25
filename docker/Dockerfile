FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        iperf3 \
        iproute2 \
        iputils-ping \
        procps \
        tcpdump \
        traceroute \
    && rm -rf /var/lib/apt/lists/*

CMD ["sleep", "infinity"]
