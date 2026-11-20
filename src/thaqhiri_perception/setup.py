from setuptools import find_packages, setup

package_name = 'thaqhiri_perception'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
         ['launch/perception.launch.py', 'launch/slam.launch.py']),
        ('share/' + package_name + '/config', ['config/stereo_disparity.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@todo.todo',
    description='IMU fusion, stereo processing and RTAB-Map SLAM for Thaqhiri',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'imu_merger_node = thaqhiri_perception.imu_merger_node:main',
        ],
    },
)
