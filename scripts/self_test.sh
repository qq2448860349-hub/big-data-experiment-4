#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
python3 -m unittest discover -s tests -v
