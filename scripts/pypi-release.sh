#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/pypi-release.sh --version <version>

Example:
  scripts/pypi-release.sh --version 0.7.0

This script runs, in order:
1) Build/check
   python3 -m build
   python3 -m twine check kinnoo-<version>-py3-none-any.whl kinnoo-<version>.tar.gz

2) Upload to TestPyPI
   python3 -m twine upload --repository-url https://test.pypi.org/legacy/ kinnoo-<version>-py3-none-any.whl kinnoo-<version>.tar.gz

3) Install smoke from TestPyPI
   python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple kinnoo==<version>

4) Upload to PyPI
   python3 -m twine upload kinnoo-<version>-py3-none-any.whl kinnoo-<version>.tar.gz
EOF
}

VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      VERSION="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: Unknown argument '$1'" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$VERSION" ]]; then
  echo "Error: --version is required" >&2
  usage
  exit 2
fi

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: --version must be a semantic version like 0.7.0" >&2
  exit 2
fi

WHEEL="kinnoo-${VERSION}-py3-none-any.whl"
SDIST="kinnoo-${VERSION}.tar.gz"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$REPO_ROOT"

echo "[step 1/4] Build artifacts"
python3 -m build

echo "[step 1/4] Twine check"
cd "$REPO_ROOT/dist"
python3 -m twine check "$WHEEL" "$SDIST"

echo "[step 2/4] Upload to TestPyPI"
python3 -m twine upload --repository-url https://test.pypi.org/legacy/ "$WHEEL" "$SDIST"

echo "[step 3/4] Install smoke from TestPyPI"
cd "$REPO_ROOT"
python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple "kinnoo==${VERSION}"

echo "[step 4/4] Upload to PyPI"
cd "$REPO_ROOT/dist"
python3 -m twine upload "$WHEEL" "$SDIST"

echo "Done: PyPI release flow completed for version ${VERSION}."
