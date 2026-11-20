"""Publish the Thaqhiri URDF and its static TF tree."""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node, SetParameter
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Create robot_state_publisher for the drone model."""
    urdf_path = os.path.join(
        get_package_share_directory('thaqhiri_description'), 'urdf', 'thaqhiri.urdf')
    with open(urdf_path, 'r') as urdf_file:
        robot_description = urdf_file.read()

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        SetParameter(name='use_sim_time', value=ParameterValue(
            LaunchConfiguration('use_sim_time'), value_type=bool)),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description}],
        ),
    ])
