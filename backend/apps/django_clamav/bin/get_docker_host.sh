#!/bin/bash
# Get host IPv4 address (works cross-platform).
# This script is used to retrieve the IPv4 address of the host machine inside a Docker container.
# Usage: ./get_docker_host.sh

# Function to get the first non-loopback IPv4 address
get_ipv4() {
    local ipv4=""

    # Method 1: Try docker host if available
    if [ -z "$ipv4" ] && [ -n "$(command -v getent)" ]; then
        ipv4=$(getent hosts host.docker.internal | awk '{print $1}' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -n 1)
    fi

    # Method 2: Use default gateway as fallback
    if [ -z "$ipv4" ] && [ -n "$(command -v ip)" ]; then
        ipv4=$(ip route | grep -E '^default via' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)
    fi

    echo "$ipv4"
}

# Get and print the IPv4 address
HOST_IP=$(get_ipv4)
echo "$HOST_IP"

# vim: set ts=4 sw=4 tw=0 noet :
