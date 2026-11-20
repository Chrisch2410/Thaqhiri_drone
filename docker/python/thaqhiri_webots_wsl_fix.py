"""Make webots_ros2_driver ignore the WSL2 kernel inside containers.

Docker Desktop on Windows runs Linux containers on a WSL2 kernel
(``*-microsoft-standard-WSL2``). ``webots_ros2_driver.utils.is_wsl()`` only
checks that kernel string, so inside such a container it tries to start
``webots.exe`` through ``wslpath`` and to reach controllers through the WSL
gateway; none of that exists in a container. A container is never a WSL
distro, so force the native-Linux code path.

Loaded at interpreter start-up by ``thaqhiri_webots_wsl_fix.pth``.
"""

import importlib.abc
import importlib.machinery
import sys

_TARGET = 'webots_ros2_driver.utils'


class _NotWsl(importlib.abc.MetaPathFinder):
    """Patch ``is_wsl`` right after the module executes, before any importer uses it."""

    def find_spec(self, fullname, path, target=None):
        if fullname != _TARGET:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or spec.loader is None:
            return spec
        exec_module = spec.loader.exec_module

        def exec_and_patch(module):
            exec_module(module)
            module.is_wsl = lambda: False

        spec.loader.exec_module = exec_and_patch
        return spec


sys.meta_path.insert(0, _NotWsl())
