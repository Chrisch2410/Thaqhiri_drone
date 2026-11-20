"""Launch the full Thaqhiri simulation with a shared simulation clock."""

import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, ExecuteProcess, GroupAction, IncludeLaunchDescription,
    RegisterEventHandler)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessIO
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution, PythonExpression)

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

# Same marker webots_ros2_driver's WaitForControllerConnection waits for. That
# helper needs the controller action, which lives in sim_webots.launch.py.
CONTROLLER_CONNECTED = 'Controller successfully connected to robot in Webots simulation.'


def _include(package, launch_file, arguments):
    """Include a package launch file in its own scope (args/params do not leak)."""
    return GroupAction(actions=[IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare(package), 'launch', launch_file])),
        launch_arguments=arguments.items(),
    )])


def _is_webots_controller(action):
    # Matches both the upstream WebotsController (local Webots) and the TCP
    # controller process sim_webots.launch.py starts for a remote Webots.
    details = getattr(action, 'process_details', None)
    return (isinstance(action, ExecuteProcess) and details is not None
            and os.path.basename(details['cmd'][0]) == 'webots-controller')


def _start_when_controller_connects(actions):
    def on_stderr(event):
        if CONTROLLER_CONNECTED in event.text.decode():
            return actions
        return None

    return RegisterEventHandler(OnProcessIO(
        target_action=_is_webots_controller,
        on_stderr=on_stderr,
    ))


def generate_launch_description():
    """Compose simulator, robot model, perception, gated SLAM and viewers."""
    rtabmap = LaunchConfiguration('rtabmap')
    slam = GroupAction(
        condition=IfCondition(rtabmap),
        actions=[_include('thaqhiri_perception', 'slam.launch.py', {
            'use_sim_time': 'true',
            'database_path': LaunchConfiguration('database_path'),
            'rtabmap_viz': LaunchConfiguration('rtabmap_viz'),
            'icp_odom_args': LaunchConfiguration('icp_odom_args'),
        })],
    )
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        condition=IfCondition(LaunchConfiguration('rviz')),
        arguments=[
            '-d', PathJoinSubstitution([
                FindPackageShare('thaqhiri_bringup'), 'rviz', 'thaqhiri_sim.rviz']),
            # Without RTAB-Map nothing publishes map/odom; the URDF root still exists.
            '-f', PythonExpression([
                "'map' if '", rtabmap, "'.lower() == 'true' else 'base_footprint'"]),
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('rtabmap', default_value='true'),
        DeclareLaunchArgument('gui', default_value='true',
                              description='Webots window; false runs it without rendering'),
        DeclareLaunchArgument('rviz', default_value='true', description='Start RViz2'),
        DeclareLaunchArgument(
            'camera_rate', default_value='12.5',
            description='Stereo camera rate in Hz; the period is rounded to a multiple '
                        'of the 8 ms Webots step (12.5 = 80 ms, 25 = 40 ms)'),
        DeclareLaunchArgument('world', default_value='mine_test_arena.wbt',
                              description='World filename, e.g. cerro_rico.wbt'),
        DeclareLaunchArgument(
            'webots_host',
            default_value=EnvironmentVariable('THAQHIRI_WEBOTS_HOST', default_value=''),
            description='Host of an already running Webots; empty starts it locally'),
        DeclareLaunchArgument('database_path', default_value='~/.ros/rtabmap.db'),
        DeclareLaunchArgument('rtabmap_viz', default_value='true',
                              description="Start RTAB-Map's own viewer"),
        DeclareLaunchArgument(
            'imu_filter_gain', default_value='0.01',
            description='Madgwick gain for moving flight; 0.1 restores the old tuning'),
        DeclareLaunchArgument(
            'icp_max_translation', default_value='0.2',
            description='Maximum accepted ICP correction (m); vary for diagnosis'),
        DeclareLaunchArgument(
            'icp_odom_args',
            # The 40-layer LiDAR needs more than the default 2,000-point
            # local map. Keep sampling and map subtraction at the same scale;
            # allow correspondence search beyond the default 5-10 cm.
            default_value=[
                '--Icp/PointToPlane true --Icp/PointToPlaneK 20 '
                '--Icp/PointToPlaneRadius 0 --Icp/VoxelSize 0.1 '
                '--Icp/MaxCorrespondenceDistance 0.5 '
                '--Icp/MaxTranslation ', LaunchConfiguration('icp_max_translation'),
                ' '
                '--Icp/Iterations 20 --Icp/Epsilon 0.001 '
                '--Icp/CorrespondenceRatio 0.01 '
                '--Odom/ScanKeyFrameThr 0.4 '
                '--OdomF2M/ScanSubtractRadius 0.1 '
                '--OdomF2M/ScanMaxSize 15000'],
            description='RTAB-Map core arguments applied only to ICP odometry'),
        _include('thaqhiri_sim_webots', 'sim_webots.launch.py', {
            'world': LaunchConfiguration('world'),
            'gui': LaunchConfiguration('gui'),
            'webots_host': LaunchConfiguration('webots_host'),
            'camera_rate': LaunchConfiguration('camera_rate'),
        }),
        _include('thaqhiri_description', 'description.launch.py', {
            'use_sim_time': 'true',
        }),
        _include('thaqhiri_perception', 'perception.launch.py', {
            'use_sim_time': 'true',
            'imu_filter_gain': LaunchConfiguration('imu_filter_gain'),
        }),
        _start_when_controller_connects([slam]),
        rviz,
    ])
