"""Run RTAB-Map with stereo + LiDAR ICP odometry for the Thaqhiri drone."""

# The ICP tuning stays a launch argument string because rtabmap.launch.py only
# accepts core parameters through `odom_args`; moving it to YAML would mean
# replacing rtabmap.launch.py with explicit rtabmap_odom/rtabmap_slam nodes.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Create the RTAB-Map include with the project's topic and frame wiring."""
    rtabmap = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('rtabmap_launch'), 'launch', 'rtabmap.launch.py'])
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'namespace': 'drone',
            'rtabmap_args': '--delete_db_on_start --Reg/Strategy 1 --Grid/3D true',
            'database_path': LaunchConfiguration('database_path'),
            'rtabmap_viz': LaunchConfiguration('rtabmap_viz'),

            'stereo': 'true',
            # The direct stereo callback does not carry scan clouds. Packaging
            # stereo as RGBDImage enables RTAB-Map's RGBD + scan synchronizer.
            'rgbd_sync': 'true',
            'subscribe_rgbd': 'true',
            'approx_rgbd_sync': 'false',
            'left_image_topic': '/drone/left/image_rect_color',
            'right_image_topic': '/drone/right/image_rect',
            'left_camera_info_topic': '/drone/left/camera_info',
            'right_camera_info_topic': '/drone/right/camera_info',

            'subscribe_scan_cloud': 'true',
            'scan_cloud_topic': '/drone/lidar_livox/point_cloud',

            'qos': '2',
            'qos_scan': '2',

            'visual_odometry': 'false',
            'icp_odometry': 'true',
            'odom_args': LaunchConfiguration('icp_odom_args'),
            # OdometryROS only subscribes to the IMU when this is enabled.
            'imu_topic': '/imu/data',
            'wait_imu_to_init': 'true',
            'qos_imu': '2',

            'frame_id': 'base_footprint',
            'vo_frame_id': 'odom',
            # Consume Odometry messages, including tracking-loss covariance.
            # vo_frame_id above still publishes odom -> base_footprint TF.
            'odom_frame_id': '',
            'map_frame_id': 'map',

            'approx_sync': 'True',
            'approx_sync_max_interval': '0.05',
            'rviz': 'False',

            'queue_size': '20',
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('database_path', default_value='~/.ros/rtabmap.db'),
        DeclareLaunchArgument('rtabmap_viz', default_value='true'),
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
        rtabmap,
    ])
