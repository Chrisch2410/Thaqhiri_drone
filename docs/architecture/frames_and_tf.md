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

## Conventions and known deviations

- **`base_link` keeps Webots/Blender native axes.** The joint
  `base_footprint_to_base_link` uses `rpy="1.5708 0 1.5708"`, so `base_link` is
  x = left, y = up, z = forward. Every child link (motors, LiDAR, cameras,
  Cube) is expressed in these axes. REP-105 expects `base_link` itself to be FLU.
- **`imu_link` is FLU.** `imu_merger_node` rotates the Cube's native
  (left, up, forward) accelerometer/gyro axes and covariances into FLU and stamps
  the result as `imu_link`; `cube_orange_imu_joint` undoes the `base_link`
  rotation so `imu_link` is aligned with `base_footprint`.
- **Stereo cameras are upright optical frames.** `camera_left` / `camera_right`
  are REP-103 optical frames (x right, y down, z forward), obtained from the
  `ZED_X_Mini_camera` (left, up, forward) axes with `rpy="0 0 pi"`.
  `camera_left` is on the vehicle's left; `fix_camera_info` sets the right
  projection `Tx = -fx * 0.05`, so disparities are positive. Until this fix the
  PROTO mounted the pair rolled 180° (upside-down images, "right" camera on the
  vehicle's left); `test_sensor_frames_match_model_geometry` now guards the
  PROTO/URDF agreement and the upright orientation.

## Frames outside the default launch

- `sil_observer` publishes ground-truth poses with `header.frame_id: world`,
  `child_frame_id: base_footprint` (messages, not TF).
- `odom_to_ardupilot` republishes odometry as an `odom -> base_link` transform on
  ArduPilot's `/ap/tf` topic (not `/tf`), with the `base_link` rotation undone
  and a 180° roll pre-flip for the ArduPilot DDS bridge.
- `gps_pose_publisher` stamps poses in `base_link`.
