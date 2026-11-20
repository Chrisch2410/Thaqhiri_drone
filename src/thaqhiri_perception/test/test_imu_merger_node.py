"""Regression checks for Cube IMU merging, axis rotation, and startup gating."""

import math
from types import SimpleNamespace
from unittest.mock import Mock

try:
    import rclpy  # noqa: F401
except ModuleNotFoundError:
    from _ros_stubs import install
    install()

import pytest

from sensor_msgs.msg import Imu

from thaqhiri_perception.imu_merger_node import ImuMergerNode


def test_imu_rotation_covariance_and_source_header():
    """Rotate Cube's native axes/covariances into FLU without mutating input."""
    merger = SimpleNamespace(_initialized=True, _last_stamp_ns=None, imu_pub=Mock())
    accel, gyro = Imu(), Imu()
    accel.header.frame_id = 'accelerometer_cube'
    accel.header.stamp.sec = 7
    gyro.header.stamp.sec = 7
    accel.linear_acceleration.y = 9.81
    gyro.angular_velocity.z = 0.2
    accel.linear_acceleration_covariance = [1., 0., 0., 0., 2., 0., 0., 0., 3.]
    ImuMergerNode.sync_callback(merger, accel, gyro)
    result = merger.imu_pub.publish.call_args.args[0]
    assert result.header.frame_id == 'imu_link'
    assert result.header.stamp.sec == 7
    assert accel.header.frame_id == 'accelerometer_cube'
    assert result.linear_acceleration.z == pytest.approx(9.81)
    assert result.angular_velocity.x == pytest.approx(0.2)
    assert list(result.linear_acceleration_covariance)[::4] == [3., 1., 2.]
    assert result.orientation_covariance[0] == -1


def test_imu_waits_for_settled_initialization():
    """Do not initialize the filter from free fall or a contact impulse."""
    merger = SimpleNamespace(_initialized=False, _settled_since=None,
                             _last_stamp_ns=None, imu_pub=Mock())
    accel, gyro = Imu(), Imu()
    ImuMergerNode.sync_callback(merger, accel, gyro)
    assert not merger.imu_pub.publish.called
    accel.linear_acceleration.y = 9.81
    for stamp in (1.0, 1.1, 1.3):
        accel.header.stamp.sec = int(stamp)
        accel.header.stamp.nanosec = int((stamp % 1) * 1e9)
        gyro.header.stamp.sec = accel.header.stamp.sec
        gyro.header.stamp.nanosec = accel.header.stamp.nanosec
        ImuMergerNode.sync_callback(merger, accel, gyro)
    assert merger._initialized
    merger.imu_pub.publish.assert_called_once()


def test_imu_does_not_mis_stamp_old_gyro_or_duplicate_samples():
    merger = SimpleNamespace(_initialized=True, _last_stamp_ns=None, imu_pub=Mock())
    accel, gyro = Imu(), Imu()
    accel.header.stamp.sec = 4
    gyro.header.stamp.sec = 4
    gyro.header.stamp.nanosec = 8000000
    ImuMergerNode.sync_callback(merger, accel, gyro)
    assert not merger.imu_pub.publish.called
    gyro.header.stamp.nanosec = 0
    ImuMergerNode.sync_callback(merger, accel, gyro)
    ImuMergerNode.sync_callback(merger, accel, gyro)
    merger.imu_pub.publish.assert_called_once()


def test_imu_drops_nonfinite_measurements_without_poisoning_filter():
    merger = SimpleNamespace(_initialized=True, _last_stamp_ns=None, imu_pub=Mock())
    accel, gyro = Imu(), Imu()
    accel.linear_acceleration.x = math.nan
    ImuMergerNode.sync_callback(merger, accel, gyro)
    assert not merger.imu_pub.publish.called
