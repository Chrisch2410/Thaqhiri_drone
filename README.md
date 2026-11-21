# Thaqhiri Dron

This repository is a **ROS 2 Jazzy simulation workspace for the Thaqhiri quadrotor**, designed for testing autonomous aerial robotics in mine-like environments using **Webots**. The main objective is to develop and validate flight control, inertial sensing, stereo vision, LiDAR-based localization, and 3D mapping before moving toward integration with a real or simulated ArduPilot flight stack.

The workspace is split into `thaqhiri_*` ROS 2 packages (see [Repository Layout](#repository-layout)); the full simulation starts from `thaqhiri_bringup`.

## Main Features

The simulation provides a complete sensing and control pipeline for the quadrotor, including:

- Quadrotor dynamics and motor control in Webots.
- Keyboard-based manual flight commands.
- Altitude and attitude stabilization.
- Cube accelerometer and gyroscope simulation.
- IMU synchronization, axis conversion, and Madgwick orientation filtering.
- Stereo cameras with image conversion, calibration correction, and stereo processing.
- A 40-layer simulated LiDAR.
- RTAB-Map integration for LiDAR/stereo 3D mapping.
- ICP-based odometry.
- ROS 2 bag recording for experimental data.
- Automated Software-in-the-Loop (SIL) validation tools.
- Experimental components for future ArduPilot integration.

Two simulation environments are available: a controlled mine-like test arena and an imported model of the **Cerro Rico mine**.

## Control Architecture

The default configuration does not use ArduPilot. Instead, a Python Webots controller directly controls the four propeller motors.

The main control flow is:

```text
Keyboard commands
       |
       v
    /cmd_pos
       |
       v
 DroneDriver
       |
       v
Motor mixing -> Webots motors -> Webots physics
       ^
       |
Altitude + filtered IMU attitude
```

The controller automatically waits for a valid filtered IMU orientation before starting the motors. It stabilizes:

- altitude,
- roll,
- pitch,
- yaw rate.

Horizontal position is not actively controlled, so some lateral drift is expected.

The nominal hover motor speed is approximately **469 rad/s**, with PID-based altitude and attitude control and additional motor trims to compensate for the simulated payload imbalance.

## IMU Processing

The simulated Cube accelerometer and gyroscope are synchronized before being merged into a ROS IMU message.

The IMU pipeline:

```text
Cube accelerometer + gyroscope
        |
        v
IMU merger
        |
        v
Axis conversion to ROS FLU frame
        |
        v
Madgwick filter
        |
        v
/imu/data
        |
        v
Flight controller
```

The Cube native coordinate system is converted to the ROS `forward-left-up` convention. The merger also waits for the initial spawn and contact motion to settle before orientation initialization.

The current Madgwick gain is **0.01**. Previous tests showed that the earlier gain of `0.1` significantly attenuated real vehicle tilt during flight reconstruction.

## Stereo Vision and LiDAR

The robot contains two upright 640 × 480 cameras with a **5 cm stereo baseline** (`camera_left` on the vehicle's left, standard positive disparity), published at **12.5 Hz** by default (`camera_rate`). Webots images are converted from BGRA to BGR, and the camera calibration information is corrected before being sent to `stereo_image_proc`.

The stereo processing produces rectified images and disparity data.

The simulated LiDAR provides:

- 360° horizontal coverage,
- approximately 59° vertical field of view,
- 40 vertical layers,
- 1000 horizontal samples,
- 0.1–40 m range,
- 10 Hz scans.

Although it is labelled as a Livox sensor, it does not reproduce Livox's real non-repetitive scanning pattern. It is a Webots `fixed` LiDAR: each 360° scan is captured at a single instant, so a moving drone produces no in-scan motion distortion. A `rotating` Webots LiDAR gives the same cloud but costs about 10× more rendering (see [Performance](#performance)).

## RTAB-Map Mapping

RTAB-Map combines the stereo cameras and LiDAR to build a 3D map of the environment.

The current configuration uses:

- **ICP odometry**
- LiDAR point clouds
- rectified stereo images
- filtered IMU data
- `map -> odom -> base_footprint` TF structure

Visual odometry is disabled.

ICP uses a local point-cloud map of up to 15,000 points, 0.10 m sampling, and a 0.50 m correspondence search distance. These parameters were introduced to improve tracking with the dense simulated LiDAR.

Mapping is primarily intended as an integration experiment. A nonempty RTAB-Map map should not yet be interpreted as proof of accurate localization.

## Cerro Rico Simulation

The repository also includes an imported model of the **Cerro Rico mine**, stored as:

```text
cerro_rico.wbt
```

It can be launched using:

```bash
ros2 launch thaqhiri_bringup thaqhiri_sim.launch.py world:=cerro_rico.wbt
```

An automated SIL experiment is provided to test stabilization, mapping, trajectory behavior, and environmental interaction inside the mine.

Current SIL results demonstrate functional stabilization and mapping, but several issues remain, including:

- lateral drift,
- return-path tracking error,
- poor camera contrast in some mine regions,
- incomplete traversal of the intended trajectory.

Therefore, the complete mine-navigation acceptance criteria have not yet been achieved.

## Gas Sensor Payload

The quadrotor model visually includes a gas sensing payload containing components labelled for gases such as:

- CO,
- H₂S,
- NO₂,
- O₂.

However, the gas sensors currently exist **only as 3D geometry**.

The repository does not yet simulate:

- gas dispersion,
- gas concentration fields,
- sensor response,
- environmental interference,
- gas ROS topics,
- gas measurement processing.

Implementing the gas sensing system is therefore an important future extension of the simulation.

## Repository Layout

```text
src/
  thaqhiri_description/   URDF (geometry, static TF) + description.launch.py
  thaqhiri_sim_webots/    Webots worlds/PROTOs, DroneDriver plugin, camera adapters,
                          SIL ground-truth observer + sim_webots.launch.py
  thaqhiri_perception/    IMU merger, Madgwick, stereo_image_proc, RTAB-Map
                          (perception.launch.py, slam.launch.py)
  thaqhiri_navigation/    teleop, SIL route/metrics, ArduPilot bridges
  thaqhiri_bringup/       thaqhiri_sim.launch.py composes everything above; rviz/ config
  third_party/ardupilot_msgs/   vendored ArduPilot interfaces (GPL-3.0)
compose.yaml              simulation container (docker compose up); settings in .env
.env.example              template for .env: host platform, world, launch arguments
start_windows.cmd         Windows: native Webots + the container in one double-click
docker/                   Dockerfile.sim, Dockerfile.ardupilot_sitl, entrypoint
  bin/                    container commands: build, sim
  platforms/              per-host compose settings (linux, wsl, windows)
  python/                 container fix: webots_ros2 must not treat Docker Desktop as WSL
tools/evaluation/         SIL runner, criteria, summaries, attitude replay
tools/blender/            Cerro Rico Blender -> Webots exporter
tools/env/                pinned Python requirements for a native setup
tools/webots_host/        Windows-side scripts used by start_windows.cmd
docs/                     simulation reports and architecture notes
```

There is no `thaqhiri_interfaces` package yet: every node uses standard ROS
messages. Create it (ament_cmake + rosidl) together with the first node that
publishes project-specific data, e.g. gas readings. `third_party/ardupilot_msgs`
is ArduPilot's own interface package, not a place for project messages.

Important modules:

- `thaqhiri_sim_webots/drone_driver.py` — active quadrotor controller (Webots plugin).
- `thaqhiri_sim_webots/bgra_to_bgr.py` — camera image conversion.
- `thaqhiri_sim_webots/fix_camera_info.py` — stereo calibration correction.
- `thaqhiri_sim_webots/sil_observer.py` — ground-truth observer used only for SIL evaluation.
- `thaqhiri_sim_webots/webots_vehicle.py` — Webots/ArduPilot SITL bridge (not imported by any node); its `AP_FLAKE8_CLEAN` marker indicates it was copied from ArduPilot (GPL-3.0).
- `thaqhiri_perception/imu_merger_node.py` — Cube IMU synchronization and coordinate transformation.
- `thaqhiri_perception/imu_validation.py` — reference attitude filter for offline validation.
- `thaqhiri_navigation/teleop_drone.py` — keyboard command publisher.
- `thaqhiri_navigation/sil_route.py`, `sil_metrics.py` — SIL route fixture and scoring.
- `thaqhiri_navigation/odom_to_ardupilot.py` — experimental external-navigation bridge.
- `thaqhiri_navigation/gps_pose_publisher.py` — incomplete experimental ArduPilot GPS helper.

Frame conventions and known REP-105 deviations are documented in
[docs/architecture/frames_and_tf.md](docs/architecture/frames_and_tf.md).

## Running the simulation

### Start

From the repository root:

| Host | Webots runs | Start | Once |
|---|---|---|---|
| Ubuntu + NVIDIA GPU | in Docker | `docker compose up` | `xhost +local:` after each login |
| Windows + Docker Desktop | natively on Windows (fastest) | double-click `start_windows.cmd`, or `start_windows.cmd cerro_rico.wbt` | install Webots R2025a on Windows |
| Windows + Docker Desktop | in Docker, windows through WSLg | `docker compose up` (PowerShell, cmd or a WSL shell) | `.env` with `HOST_PLATFORM=wsl` |

The container builds the workspace (incremental colcon build) and launches the
stack: Webots with the drone on its pad, sensors, RTAB-Map, RViz2 and RTAB-Map's
viewer. Nothing flies or runs tests on its own; the drone takes commands once the
log shows `Controller successfully connected` (about 45 s; the very first
`docker compose up` also builds the image, which takes several minutes).
Ctrl+C stops everything; `start_windows.cmd` also closes Webots and starts
Docker Desktop if it is not running.

### Settings (`.env`)

Copy `.env.example` to `.env` and edit it. Without `.env` the defaults below apply.

| Setting | Default | Effect |
|---|---|---|
| `HOST_PLATFORM` | `linux` | `linux` (Ubuntu) or `wsl` (Windows, Webots in Docker). `start_windows.cmd` sets `windows` itself. |
| `WORLD` | `mine_test_arena.wbt` | `mine_test_arena.wbt` or `cerro_rico.wbt`; also used by `start_windows.cmd` |
| `SIM_ARGS` | empty | Extra [launch arguments](#launch-arguments-thaqhiri_bringup-thaqhiri_simlaunchpy), space-separated |
| `SIM_AUTOSTART` | `true` | `false`: the container only builds; launch by hand with `sim` |
| `WSL_GPU_ADAPTER` | `NVIDIA` | Windows: GPU used for OpenGL (part of the adapter name, e.g. `AMD`, `Intel`) |

```ini
# .env: Windows, everything in Docker, Cerro Rico, no viewers
HOST_PLATFORM=wsl
WORLD=cerro_rico.wbt
SIM_ARGS=rviz:=false rtabmap_viz:=false
```

After changing `.env`, run `docker compose up` again; Compose recreates the container.

### Develop

`src/` is mounted live into the container; `build/`, `install/` and `log/` live in
the `thaqhiri_workspace` Docker volume, not in the checkout.

```bash
docker compose restart          # after editing src/: rebuild and relaunch
docker compose exec sim bash    # shell in the running container, workspace sourced
```

Commands in that shell:

| Command | Does |
|---|---|
| `build` | Incremental `colcon build --symlink-install` of `~/ros_ws`, then re-sources it. Extra arguments go to colcon: `build --packages-select thaqhiri_sim_webots` |
| `sim` | Launches the stack with the `.env` settings; extra launch arguments override them: `sim world:=cerro_rico.wbt rviz:=false`. Use it with `SIM_AUTOSTART=false`, otherwise a stack is already running. |
| `ros2 run thaqhiri_navigation teleop_drone` | Fly (keys below) |
| `cd ~/ros_ws && colcon test --packages-select thaqhiri_sim_webots && colcon test-result --verbose` | Tests |

With `start_windows.cmd`, `docker compose restart` reconnects to the Webots that
is still open without resetting the world; run `start_windows.cmd` again for a
fresh one.

### Fly

```bash
docker compose exec sim bash -ic "ros2 run thaqhiri_navigation teleop_drone"
```

| Key | Command on `/cmd_pos` |
|---|---|
| `t` / `b` | climb / descend |
| `i` / `,` | forward / backward |
| `j` / `l` | left / right |
| `u` `o` `m` `.` | diagonals |
| `y` / `n` | yaw left / right |
| any other key | stop |

### Without Docker

Ubuntu 24.04 with ROS 2 Jazzy and Webots R2025a, using the pinned Python requirements:

```bash
source /opt/ros/jazzy/setup.bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r tools/env/requirements.txt
python -m colcon build --symlink-install --packages-up-to thaqhiri_bringup
source install/setup.bash
ros2 launch thaqhiri_bringup thaqhiri_sim.launch.py
```

### Parameters

#### Launch arguments (`thaqhiri_bringup thaqhiri_sim.launch.py`)

| Argument | Default | Effect | Example |
|---|---|---|---|
| `world` | `mine_test_arena.wbt` | World from `thaqhiri_sim_webots/worlds`. Ignored when `webots_host` is set. | `world:=cerro_rico.wbt` |
| `gui` | `true` | Webots window. `false` runs Webots without rendering, minimized (a display is still needed). Ignored when `webots_host` is set. | `gui:=false` |
| `rviz` | `true` | RViz2 with [rviz/thaqhiri_sim.rviz](src/thaqhiri_bringup/rviz/thaqhiri_sim.rviz): drone model, LiDAR scan, RTAB-Map cloud, ICP odometry and the rectified left image. The fixed frame is `map`, or `base_footprint` with `rtabmap:=false`. | `rviz:=false` |
| `rtabmap` | `true` | RTAB-Map with ICP odometry, started once the drone controller connects. | `rtabmap:=false` |
| `rtabmap_viz` | `true` | RTAB-Map's own viewer. | `rtabmap_viz:=false` |
| `camera_rate` | `12.5` | Stereo camera rate in Hz. Webots rounds the period to a multiple of the 8 ms step: `25` = 40 ms, `12.5` = 80 ms, `10` = 96 ms (10.4 Hz). More frames for stereo/RTAB-Map cost simulation speed. | `camera_rate:=25` |
| `webots_host` | `$THAQHIRI_WEBOTS_HOST` (empty) | Connect over TCP (port 1234) to a Webots already running on this host instead of starting one. | `webots_host:=192.168.1.20` |
| `database_path` | `~/.ros/rtabmap.db` | RTAB-Map database; deleted at every start. | `database_path:=/tmp/trial1.db` |
| `imu_filter_gain` | `0.01` | Madgwick gain; `0.1` is the old tuning. | `imu_filter_gain:=0.1` |
| `icp_max_translation` | `0.2` | Largest ICP correction accepted (m). | `icp_max_translation:=0.3` |
| `icp_odom_args` | ICP tuning in `thaqhiri_sim.launch.py` | Replaces all RTAB-Map ICP odometry arguments (including `icp_max_translation`). | `icp_odom_args:="--Icp/VoxelSize 0.05 --Icp/MaxTranslation 0.2"` |

Common combinations, as `SIM_ARGS` in `.env` or as arguments of `sim` in the container:

```ini
# fastest: no Webots rendering and no viewers
SIM_ARGS=gui:=false rviz:=false rtabmap_viz:=false
# watch Webots only
SIM_ARGS=rviz:=false rtabmap_viz:=false
# sensors and flight control only, no SLAM
SIM_ARGS=rtabmap:=false
# 25 Hz cameras, separate database
SIM_ARGS=camera_rate:=25 database_path:=/tmp/cerro.db
```

Values containing spaces (`icp_odom_args`) only work as `sim` arguments:
`sim icp_odom_args:="--Icp/VoxelSize 0.05"`.

Each package launch file also runs on its own:

| Launch file | Arguments |
|---|---|
| `thaqhiri_sim_webots sim_webots.launch.py` | `world`, `gui`, `webots_host`, `camera_rate` |
| `thaqhiri_description description.launch.py` | `use_sim_time` |
| `thaqhiri_perception perception.launch.py` | `use_sim_time`, `imu_filter_gain` |
| `thaqhiri_perception slam.launch.py` | `use_sim_time`, `database_path`, `rtabmap_viz`, `icp_max_translation`, `icp_odom_args` |

#### Environment variables (inside the container)

| Variable | Default | Effect | Example |
|---|---|---|---|
| `THAQHIRI_WEBOTS_HOST` | empty; `host.docker.internal` with `start_windows.cmd` | Default for `webots_host`. | `THAQHIRI_WEBOTS_HOST= sim` (start Webots in the container instead) |
| `DISPLAY`, `WAYLAND_DISPLAY` | host value (linux); `:0`, `wayland-0` (Windows) | Where GUI windows open. | |
| `ROS_DOMAIN_ID` | `0` | DDS domain. | `ROS_DOMAIN_ID=5 sim` |
| `WEBOTS_HOME` | `/usr/local/webots` | Webots installation. On Windows, `start_webots.cmd` otherwise reads it from the registry. | `set WEBOTS_HOME=D:\Webots` |

#### Webots on Windows (`tools\webots_host\start_webots.cmd`)

`start_windows.cmd` runs this script; call it directly to pass Webots options.
`start_webots.cmd [world] [Webots options]`: `world` defaults to
`mine_test_arena.wbt`; any further options are passed to Webots unchanged.
The port is always 1234. Then start the container with
`set HOST_PLATFORM=windows` and `docker compose up` (cmd).

```bat
tools\webots_host\start_webots.cmd cerro_rico.wbt
:: run as fast as possible instead of real time
tools\webots_host\start_webots.cmd cerro_rico.wbt --mode=fast
:: no 3D view (Windows-side equivalent of gui:=false)
tools\webots_host\start_webots.cmd cerro_rico.wbt --no-rendering --minimize
```

#### Simulation model settings (files)

| Setting | File | Value |
|---|---|---|
| Physics/control step | `worlds/*.wbt` (`basicTimeStep`) | 8 ms: controller and Cube IMU at 125 Hz |
| IMU and altimeter rates | `resource/webots_plugins.urdf.xacro` | Cube IMU 125 Hz, Livox IMU 10 Hz, altimeter 10 Hz |
| Camera rate | `resource/webots_plugins.urdf.xacro` (`camera_rate` xacro argument) | 12.5 Hz, set by the launch argument |
| LiDAR | `protos/ThaqhiriDrone.proto` (`lidar_livox`) | `fixed`, 360° × 59°, 1000 × 40, 10 Hz |

#### Other nodes and tools

| Command | Parameters / options |
|---|---|
| `ros2 run thaqhiri_navigation odom_to_ardupilot` (experimental) | `odom_topic` (`/drone/odom`), `tf_topic` (`/ap/tf`), `parent_frame` (`odom`), `child_frame` (`base_footprint`), e.g. `--ros-args -p parent_frame:=map` |
| `ros2 run thaqhiri_sim_webots sil_observer` (started by the SIL runner) | `lights_on` (`true`), `headlight_on` (`true`) |
| `tools/evaluation/run_sil.sh` (builds, then runs Cerro Rico headless) | `--scenario nominal\|low_light`, `--headlight on\|off`, `--control-mode odometry\|ground_truth\|hover` (the last two are diagnostic), `--output DIR` (default `experiment_data/sil/<UTC time>`), `--wall-timeout 900`, `--domain-id 73`, `--desired-speed-limit 0.2`, `--icp-max-translation 0.2`, `--imu-filter-gain 0.01` |
| `python3 tools/evaluation/summarize_sil.py RUN...` | `--output` (default `docs/simulation/validation/cerro_rico`) |
| `python3 tools/evaluation/replay_attitude.py RUN...` | `--output DIR` (required) |

```bash
# inside the container (the checkout is at ~/thaqhiri); with SIM_AUTOSTART=false
~/thaqhiri/tools/evaluation/run_sil.sh --scenario low_light --headlight off --output experiment_data/sil/low_light_1
```

See [docs/simulation/cerro_rico_sil.md](docs/simulation/cerro_rico_sil.md) for the SIL procedure.

### Performance

Webots physics takes about 0.2 ms per 8 ms step; the cost is sensor rendering,
the Webots window and, in `windows` mode, streaming images over Docker's TCP link.
Real-time factor (simulated s per wall s) with the full stack and RTAB-Map on,
measured on the development machine (Windows 11, NVIDIA GPU, Docker Desktop):

| Mode, world | Viewers | Before: cameras every step (125 Hz), rotating LiDAR | Now: 12.5 Hz cameras, fixed LiDAR |
|---|---|---|---|
| `wsl`, arena | Webots, RViz, rtabmap_viz (defaults) | – | 0.078 |
| `wsl`, arena | Webots only | 0.013 | 0.079 |
| `wsl`, arena | none (`gui:=false rviz:=false rtabmap_viz:=false`) | 0.026 | 0.260 |
| `wsl`, Cerro Rico | defaults | – | 0.221 |
| `wsl`, Cerro Rico | none | 0.028 | 0.277 |
| `windows`, arena | RViz, rtabmap_viz | – | 0.387 |
| `windows`, arena | none (Webots minimized) | 0.050 | 0.382 |
| `windows`, Cerro Rico | none | – | 0.417 |

- In `wsl` mode the Webots window is the main cost; RViz2 and rtabmap_viz are not.
- `camera_rate:=25` lowers the headless `wsl` arena from 0.260 to 0.230.
- `windows` mode is fastest because Webots renders natively on the GPU.

### Tests

In the container (`docker compose exec sim bash`):

```bash
cd ~/ros_ws && colcon test --packages-select thaqhiri_sim_webots thaqhiri_perception thaqhiri_navigation && colcon test-result --verbose
```

## License

Apache-2.0 (see `LICENSE`), except `src/third_party/ardupilot_msgs` (GPL-3.0) and
`thaqhiri_sim_webots/webots_vehicle.py`, which appears to be copied from ArduPilot's
GPL-3.0 Webots example and has no license header.
