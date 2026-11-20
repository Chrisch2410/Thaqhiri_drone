# Frames and TF (current state)

This documents the frames **as implemented**, including known deviations from
[REP-103](https://www.ros.org/reps/rep-0103.html) /
[REP-105](https://www.ros.org/reps/rep-0105.html). Nothing here was changed by
the package restructure; fix the deviations deliberately, with the tests in
`thaqhiri_sim_webots/test/test_drone_driver.py` updated alongside.

## TF tree

```text
map ──(RTAB-Map)──> odom ──(RTAB-Map ICP odometry)──> base_footprint
base_footprint ──(URDF, static)──> base_link ──> lidar_livox, ZED_X_Mini_camera,
                                                 cube_orange ──> imu_link, ...
```

| Transform | Publisher | Notes |
| --- | --- | --- |
| `map -> odom` | rtabmap (`slam.launch.py`) | `map_frame_id: map` |
| `odom -> base_footprint` | rtabmap ICP odometry | `frame_id: base_footprint`, `vo_frame_id: odom` |
| `base_footprint -> base_link -> sensors` | robot_state_publisher (`description.launch.py`) | from `thaqhiri_description/urdf/thaqhiri.urdf` |

`base_footprint` is the REP-105 body frame (FLU: x forward, y left, z up).

## Known deviations

- **`base_link` keeps Webots/Blender native axes.** The joint
  `base_footprint_to_base_link` uses `rpy="1.5708 0 1.5708"`, so `base_link` is
  x = left, y = up, z = forward. Every child link (motors, LiDAR, cameras,
  Cube) is expressed in these axes. REP-105 expects `base_link` itself to be FLU.
- **`imu_link` is FLU.** `imu_merger_node` rotates the Cube's native
  (left, up, forward) accelerometer/gyro axes and covariances into FLU and stamps
  the result as `imu_link`; `cube_orange_imu_joint` undoes the `base_link`
  rotation so `imu_link` is aligned with `base_footprint`.
- **Camera frames are not optical frames.** `camera_left` / `camera_right`
  inherit `base_link` axes; there are no `*_optical_frame` links with
  REP-103 optical axes (x right, y down, z forward).
- **Stereo naming to verify.** In `base_link` axes (x = left), `camera_right` is
  at x = +0.025 and `camera_left` at x = −0.025, i.e. "right" is on the
  vehicle's left side. The unused `perception/config/stereo_disparity.yaml`
  tuning has `min_disparity: -350`, which is consistent with a swapped pair.
  Confirm against the PROTO before relying on stereo depth.

## Frames outside the default launch

- `sil_observer` publishes ground-truth poses with `header.frame_id: world`,
  `child_frame_id: base_footprint` (messages, not TF).
- `odom_to_ardupilot` republishes odometry as an `odom -> base_link` transform on
  ArduPilot's `/ap/tf` topic (not `/tf`), with the `base_link` rotation undone
  and a 180° roll pre-flip for the ArduPilot DDS bridge.
- `gps_pose_publisher` stamps poses in `base_link`.
