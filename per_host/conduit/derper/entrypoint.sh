#!/bin/sh
set -e

CERT_DIR="${DERP_CERT_DIR:-/certs}"
HOSTNAME="${DERP_DOMAIN:-localhost}"
CERT_FILE="$CERT_DIR/$HOSTNAME.crt"
KEY_FILE="$CERT_DIR/$HOSTNAME.key"

# Generate a self-signed certificate if one doesn't already exist.
# derper requires a cert even when running behind a reverse proxy;
# the cert is NOT used for client trust (Caddy terminates TLS).
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    mkdir -p "$CERT_DIR"
    openssl req -x509 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -days 3650 -nodes \
        -subj "/CN=$HOSTNAME" \
        -addext "subjectAltName=DNS:$HOSTNAME" 2>/dev/null
    echo "derper: generated self-signed cert for $HOSTNAME"
fi

exec /usr/local/bin/derper \
    --hostname="$HOSTNAME" \
    --a=:8080 \
    --http-port=-1 \
    --stun \
    --stun-port="${DERP_STUN_PORT:-3478}" \
    --certmode=manual \
    --certdir="$CERT_DIR" \
    --verify-clients="${DERP_VERIFY_CLIENTS:-false}"
