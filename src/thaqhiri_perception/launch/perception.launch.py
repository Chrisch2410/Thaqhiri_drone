"""Fuse the Cube IMU and rectify the stereo pair."""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node, SetParameter
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Create the IMU merger, Madgwick filter and stereo_image_proc pipeline."""
    imu_merger_node = Node(
        package='thaqhiri_perception',
        executable='imu_merger_node',
        name='imu_merger_node',
        output='screen',
        namespace='drone',
    )

    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter_madgwick',
        output='screen',
        parameters=[
                {'use_mag': False},  # Webots no suele tener magnetómetro por defecto
                # Si quieres que publique el frame transform
                {'publish_tf': False},
                {'gain': ParameterValue(LaunchConfiguration('imu_filter_gain'), value_type=float)},
                {'world_frame': 'enu'}  # East-North-Up, el estándar de ROS
        ],
        remappings=[
            # Se suscribe al tópico que genera nuestro merger
            ('/imu/data_raw', '/imu/data_raw'),
            ('/imu/data', '/imu/data'),
        ]
    )

    stereo_proc_share = get_package_share_directory('stereo_image_proc')
    stereo_proc = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            stereo_proc_share, 'launch', 'stereo_image_proc.launch.py')),
        launch_arguments={
            'namespace': 'drone',
            'approximate_sync': 'True',
        }.items()
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument(
            'imu_filter_gain', default_value='0.01',
            description='Madgwick gain for moving flight; 0.1 restores the old tuning'),
        SetParameter(name='use_sim_time', value=ParameterValue(
            LaunchConfiguration('use_sim_time'), value_type=bool)),
        imu_merger_node,
        imu_filter_node,
        GroupAction(actions=[stereo_proc]),
    ])
