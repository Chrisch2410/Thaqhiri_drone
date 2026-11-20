import os
from setuptools import find_packages, setup

package_name = 'thaqhiri_sim_webots'


def package_files(source_dir, target_dir):
    """
    Recursively finds all files in a source directory and maps them
    to the target path in the installation share space.
    """
    paths = []
    for (path, directories, filenames) in os.walk(source_dir):
        for filename in filenames:
            # Source file full path
            source_file = os.path.join(path, filename)
            # Replicate the internal folder structure relative to the source_dir
            relative_path = os.path.relpath(path, source_dir)
            if relative_path == '.':
                dest_dir = target_dir
            else:
                dest_dir = os.path.join(target_dir, relative_path)

            paths.append((dest_dir, [source_file]))
    return paths


data_files = [
    ('share/ament_index/resource_index/packages',
     ['resource/' + package_name]),
    ('share/' + package_name + '/launch', ['launch/sim_webots.launch.py']),
    ('share/' + package_name + '/resource', ['resource/webots_plugins.urdf.xacro']),
    ('share/' + package_name, ['package.xml']),
]

# PROTO/world URLs are relative ("../protos/..."), so keep both trees side by side.
data_files.extend(package_files('worlds', 'share/' + package_name + '/worlds'))
data_files.extend(package_files('protos', 'share/' + package_name + '/protos'))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@todo.todo',
    description='Webots worlds, drone PROTO, driver plugin and camera adapters for Thaqhiri',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'bgra_to_bgr = thaqhiri_sim_webots.bgra_to_bgr:main',
            'fix_camera_info = thaqhiri_sim_webots.fix_camera_info:main',
            'sil_observer = thaqhiri_sim_webots.sil_observer:main',
        ],
    },
)
