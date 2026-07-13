#!/usr/bin/env bash
# sync-images.sh
# Pull images from .yml files in this directory, scp them to the NAS,
# and load them into Docker there.
#
# Usage:
#   ./sync-images.sh                   # uses defaults
#   NAS_HOST=zyxir-nas ./sync-images.sh  # override host

set -euo pipefail

NAS_HOST="${NAS_HOST:-zyxir-nas.tail2b5f2.ts.net}"
NAS_USER="${NAS_USER:-zyxir}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---- extract images from all .yml files --------------------
IMAGES=$(grep -h 'image:' "$SCRIPT_DIR"/*.yml \
    | sed 's/.*image:[[:space:]]*//' \
    | sort -u)

if [ -z "$IMAGES" ]; then
    echo "No images found in $SCRIPT_DIR/*.yml"
    exit 0
fi

echo "Images found:"
echo "$IMAGES" | sed 's/^/  /'

# ---- pull for linux/amd64 (NAS architecture) --------------
echo ""
echo "=== Pulling images (linux/amd64) ==="
for img in $IMAGES; do
    echo "  $img"
    docker pull --platform linux/amd64 "$img"
done

# ---- save to tar ------------------------------------------
TAR_FILE="$SCRIPT_DIR/nas-images.tar"
echo ""
echo "=== Saving to $TAR_FILE ==="
# shellcheck disable=SC2086
docker save $IMAGES -o "$TAR_FILE"

# ---- transfer to NAS --------------------------------------
echo ""
echo "=== Copying to $NAS_HOST ==="
scp "$TAR_FILE" "$NAS_USER@$NAS_HOST:/share/homes/$NAS_USER/"

# ---- load on NAS ------------------------------------------
echo ""
echo "=== Loading on $NAS_HOST ==="
ssh "$NAS_USER@$NAS_HOST" ". /etc/profile 2>/dev/null; docker load -i /share/homes/$NAS_USER/nas-images.tar && rm /share/homes/$NAS_USER/nas-images.tar"

# ---- cleanup ----------------------------------------------
rm "$TAR_FILE"

echo ""
echo "=== Done ==="
