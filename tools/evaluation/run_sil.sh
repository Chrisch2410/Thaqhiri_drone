#!/usr/bin/env bash
# Build and run the corrected SIL pipeline in an existing ROS Jazzy setup.
set -eo pipefail

project_dir="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
cd "$project_dir"

if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  echo 'ROS 2 Jazzy is required. Run this launcher in your Linux simulation environment.' >&2
  exit 1
fi
source /opt/ros/jazzy/setup.bash
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

if [[ -z "${WEBOTS_HOME:-}" || ! -x "$WEBOTS_HOME/webots" ]]; then
  for candidate in "$HOME/.local/opt/webots" /usr/local/webots /usr/share/webots /opt/webots; do
    if [[ -x "$candidate/webots" ]]; then
      export WEBOTS_HOME="$candidate"
      break
    fi
  done
fi
if [[ -z "${WEBOTS_HOME:-}" || ! -x "$WEBOTS_HOME/webots" ]]; then
  echo 'Webots was not found; set WEBOTS_HOME to your existing installation.' >&2
  exit 1
fi

# The Docker image builds in its own workspace (THAQHIRI_WS) to keep build
# artifacts out of the checkout; elsewhere the checkout is the workspace.
cd "${THAQHIRI_WS:-$project_dir}"
python3 -c 'from colcon_core.command import main; raise SystemExit(main())' build --symlink-install \
  --packages-up-to thaqhiri_bringup \
  --cmake-args "-DPython3_EXECUTABLE=$(command -v python3)" \
               "-DPYTHON_EXECUTABLE=$(command -v python3)"
source install/setup.bash
cd "$project_dir"
exec python3 tools/evaluation/run_sil.py "$@"
