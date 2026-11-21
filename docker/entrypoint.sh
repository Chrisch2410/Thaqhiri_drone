#!/bin/bash
# Container start: set up the display, build the workspace, launch the simulation.
# With a command (docker compose run sim <cmd>) only the display setup runs first.

# Windows hosts mount WSLg twice (docker/platforms/wsl.yml); link whichever one
# has the sockets to the paths X11/Wayland clients use.
for wslg in /wslg/desktop /wslg/distro; do
    if [ -e "$wslg/.X11-unix/X0" ]; then
        ln -sfn "$wslg/.X11-unix" /tmp/.X11-unix
        ln -sfn "$wslg" /tmp/wslg
        break
    fi
done
# Instance files of a Webots from a previous start of this container.
rm -rf /tmp/webots

if [ "$#" -gt 0 ]; then
    source /opt/ros/jazzy/setup.bash
    exec "$@"
fi

if ! build; then
    echo "Build failed. Fix the code, then: docker compose restart" \
         "(or docker compose exec sim bash, and run build)."
    exec sleep infinity
fi
if [ "$SIM_AUTOSTART" = false ]; then
    echo "SIM_AUTOSTART=false: workspace built. Enter with" \
         "'docker compose exec sim bash' and run 'sim'."
    exec sleep infinity
fi
exec sim
