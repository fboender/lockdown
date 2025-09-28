#!/bin/sh

# Strict mode
set -e           # fail when any command files
set -u           # fail on unset variables


PREFIX=${PREFIX:-/usr/local}
BINDIR="$PREFIX/bin"

if [ "$PREFIX" = "/usr/local" ] && [ "$(id -u)" -ne 0 ]; then
    echo "Trying to install globally, but you are not root. Please try:" >&2
    echo >&2
    echo "   sudo $0" >&2
    echo >&2
    echo "or if you want to only install for your own user:" >&2
    echo >&2
    echo "   PREFIX=$HOME/.local $0" 2>&1
    echo
    exit 1
fi

echo "Installing 'lockdown' binary in $BINDIR"
install -m 755 lockdown "$BINDIR"

if [ "$(which systemctl)" = "" ]; then
    echo "systemctl not found. Daemon support not available." >&2
else
    read -p "Do you want to install and run the daemon? [y/N]" INSTALL_DAEMON
    if [ "$INSTALL_DAEMON" = "y" ] || [ "$INSTALL_DAEMON" = "Y" ]; then
        echo "Installing lockdown daemon configuration in: ~/.config/lockdown/daemon.conf"
        install -D -m 644 contrib/lockdown-daemon.conf ~/.config/lockdown/daemon.conf

        echo "Installing lockdown daemon systemd service: ~/.config/systemd/user/lockdown-daemon.service"
        install -Dm644 contrib/lockdown-daemon.service ~/.config/systemd/user

        echo "Enabling lockdown-daemon service"
        systemctl --user daemon-reload
        systemctl --user enable --now lockdown-daemon.service
        systemctl --user start lockdown-daemon.service
        loginctl enable-linger $USER

        echo "Daemon installed. Configuration file:"
        echo
        echo "  ~/.config/lockdown/daemon.conf"
        echo
        echo "Check the README.md for how to interact with it"
    fi
fi
