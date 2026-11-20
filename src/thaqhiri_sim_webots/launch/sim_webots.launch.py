"""Start Webots, the drone driver plugin and the Webots camera adapters.

``webots_host`` selects where Webots runs:

- empty (default): this launch starts Webots locally; webots_ros2 picks the
  controller transport for the platform.
- a host name or IP: Webots is already running there with the same world
  (e.g. natively on Windows via tools/webots_host/start_webots.cmd) and the
  controllers connect to it over TCP.
"""

import os

from ament_index_python.packages import get_package_prefix, get_package_share_directory

import launch
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, RegisterEventHandler)
from launch.event_handlers import OnProcessExit
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node, SetParameter

from webots_ros2_driver.webots_controller import WebotsController
from webots_ros2_driver.webots_launcher import Ros2SupervisorLauncher, WebotsLauncher

# Webots' default extern-controller port; start_webots.cmd uses the same one.
WEBOTS_PORT = '1234'


def _shutdown_if_running(event, context):
    # Ctrl-C already initiated shutdown; do not shut the ROS adapter down twice.
    if context.is_shutdown:
        return []
    return [launch.actions.EmitEvent(event=launch.events.Shutdown())]


def _local_webots(package_dir, robot_description):
    """Start Webots here; upstream helpers choose IPC or WSL transport."""
    webots = WebotsLauncher(
        world=PathJoinSubstitution([
            package_dir, 'worlds', LaunchConfiguration('world')]),
        # The worlds already contain the Ros2Supervisor robot.
        ros2_supervisor=False,
        gui=LaunchConfiguration('gui'),
    )
    supervisor = Ros2SupervisorLauncher(port=WEBOTS_PORT)
    drone = WebotsController(
        robot_name='drone',
        port=WEBOTS_PORT,
        parameters=[
            {'robot_description': robot_description},
            {'use_sim_time': True},
        ],
    )
    owned = [
        webots,
        RegisterEventHandler(OnProcessExit(
            target_action=webots, on_exit=_shutdown_if_running)),
    ]
    return owned, supervisor, drone


def _remote_webots(host, robot_description):
    """Connect to a Webots that is already running on ``host`` over TCP.

    Mirrors Ros2SupervisorLauncher and WebotsController, which only use TCP
    for WSL or WEBOTS_SHARED_FOLDER setups, with the controller URL explicit.
    """
    driver_prefix = get_package_prefix('webots_ros2_driver')
    supervisor = Node(
        package='webots_ros2_driver',
        executable='ros2_supervisor.py',
        namespace='Ros2Supervisor',
        remappings=[('/Ros2Supervisor/clock', '/clock')],
        output='screen',
        respawn=True,
        additional_env={
            'WEBOTS_CONTROLLER_URL': f'tcp://{host}:{WEBOTS_PORT}/Ros2Supervisor',
            'WEBOTS_HOME': driver_prefix,
        },
    )
    drone = ExecuteProcess(
        cmd=[
            os.path.join(get_package_share_directory('webots_ros2_driver'),
                         'scripts', 'webots-controller'),
            '--robot-name=drone', '--protocol=tcp', f'--ip-address={host}',
            f'--port={WEBOTS_PORT}',
            'ros2', '--ros-args',
            '-p', f'robot_description:={robot_description}',
            '-p', 'use_sim_time:=true',
        ],
        name='webots_controller_drone',
        output='screen',
        additional_env={'WEBOTS_HOME': driver_prefix},
    )
    return [], supervisor, drone


def _webots_and_controllers(context):
    package_dir = get_package_share_directory('thaqhiri_sim_webots')
    robot_description = os.path.join(package_dir, 'resource', 'webots_plugins.urdf')
    host = LaunchConfiguration('webots_host').perform(context).strip()
    if host:
        owned, supervisor, drone = _remote_webots(host, robot_description)
    else:
        owned, supervisor, drone = _local_webots(package_dir, robot_description)

    adapters = [
        Node(
            package='thaqhiri_sim_webots',
            executable='fix_camera_info',
            name='fix_camera_info',
            output='screen',
            namespace='drone',
        ),
        Node(
            package='thaqhiri_sim_webots',
            executable='bgra_to_bgr',
            name='bgra_to_bgr_node',
            output='screen',
            namespace='drone',
        ),
    ]
    return [
        *owned,
        # The clock producer must use wall time for its stepping timer, so it
        # is declared before use_sim_time is forced for everything after it.
        supervisor,
        SetParameter(name='use_sim_time', value=True),
        drone,
        *adapters,
    ]


def generate_launch_description():
    """Create the simulator (or its connection), clock supervisor and drone controller."""
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('world', default_value='mine_test_arena.wbt',
                              description='World filename, e.g. cerro_rico.wbt'),
        DeclareLaunchArgument(
            'webots_host',
            default_value=EnvironmentVariable('THAQHIRI_WEBOTS_HOST', default_value=''),
            description='Host of an already running Webots (e.g. host.docker.internal); '
                        'empty starts Webots locally. world/gui then do not apply.'),
        OpaqueFunction(function=_webots_and_controllers),
    ])
