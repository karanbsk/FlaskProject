#!/bin/sh
# usage: strip-sqlite.sh /install
set -eu

INSTALL_DIR="${1:-/install}"
TMPF="$(mktemp)"
echo "Scanning $INSTALL_DIR for native libs that link to libsqlite3.so.0..."

# find candidate binaries (.so, .pyd, etc.)
find "$INSTALL_DIR" -type f \( -name "*.so" -o -name "*.so.*" -o -name "*.pyd" -o -name "*.dll" \) -print0 \
  | while IFS= read -r -d '' f; do
    # Use ldd where available and suppress errors
    if ldd "$f" 2>/dev/null | grep -q 'libsqlite3\.so\.0'; then
      echo " -> $f links to libsqlite3.so.0"
      # Heuristic: remove the package dir (parent/upstream) which contains the .so
      # We attempt to remove the nearest top-level package directory under /install
      pkg_dir=$(echo "$f" | sed -E "s|($INSTALL_DIR/[^/]+).*|\1|")
      echo "    removing package subtree: $pkg_dir"
      rm -rf "$pkg_dir" || echo "    failed to remove $pkg_dir"
    fi
done

echo "Done scan."
