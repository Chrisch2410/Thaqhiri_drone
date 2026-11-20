"""Start Webots, the drone driver plugin and the Webots camera adapters."""

import os

from ament_index_python.packages import get_package_share_directory

import launch
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node, SetParameter

from webots_ros2_driver.webots_controller import WebotsController
from webots_ros2_driver.webots_launcher import WebotsLauncher


def _shutdown_if_running(event, context):
    # Ctrl-C already initiated shutdown; do not shut the ROS adapter down twice.
    if context.is_shutdown:
        return []
    return [launch.actions.EmitEvent(event=launch.events.Shutdown())]


def generate_launch_description():
    """Create the simulator, its clock supervisor and the drone controller."""
    package_dir = get_package_share_directory('thaqhiri_sim_webots')

    webots = WebotsLauncher(
        world=PathJoinSubstitution([
            package_dir, 'worlds', LaunchConfiguration('world')]),
        ros2_supervisor=True,
        gui=LaunchConfiguration('gui'),
    )

    drone_driver = WebotsController(
        robot_name='drone',
        parameters=[
            {'robot_description': os.path.join(
                package_dir, 'resource', 'webots_plugins.urdf')},
            {'use_sim_time': True},
        ]
    )

    fix_camera_info = Node(
        package='thaqhiri_sim_webots',
        executable='fix_camera_info',
        name='fix_camera_info',
        output='screen',
        namespace='drone',
    )

    bgra_to_bgr_node = Node(
        package='thaqhiri_sim_webots',
        executable='bgra_to_bgr',
        name='bgra_to_bgr_node',
        output='screen',
        namespace='drone',
    )

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('world', default_value='mine_test_arena.wbt',
                              description='World filename, e.g. cerro_rico.wbt'),
        webots,
        # The clock producer must use wall time for its stepping timer, so it
        # is declared before use_sim_time is forced for everything after it.
        webots._supervisor,
        SetParameter(name='use_sim_time', value=True),
        drone_driver,
        fix_camera_info,
        bgra_to_bgr_node,
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=webots,
                on_exit=_shutdown_if_running,
            )
        )
    ])
