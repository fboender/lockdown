#!/bin/sh

# Strict mode
set -e           # fail when any command files


help ()
{
    echo "Usage: $0 [-g|--global]" >&2
    echo
    echo "Install lockdown"
    echo
    exit 1
}

#
# Parse arguments
#
FLAG_GLOBAL=0

while true; do
    case "$1" in
        -h|--help)
            help
            ;;
        -g|--global)
            FLAG_GLOBAL=1
            shift
            ;;
        *)
            break
            ;;
    esac
done

#
# Check if root for global install
#
if [ "$FLAG_GLOBAL" -eq 1 ]; then
    if [ "$(id -u)" -ne 0 ]; then
        echo "Trying to install globally, but you are not root. Please try:" >&2
        echo >&2
        echo "   sudo $0" >&2
        echo >&2
        exit 1
    fi
fi

#
# Get some user feedback
#
echo "Please answer some questions before we begin installation:"
echo
read -p "  Do you want to generate default keys? [Y/n]" GENERATE_KEY
read -p "  Do you want to install and run the daemon? [Y/n]" INSTALL_DAEMON
echo

#
# Set all the correct flags and environment variables
#
FLAG_GENERATE_KEY=0
FLAG_INSTALL_DAEMON=0
if [ "$GENERATE_KEY" = "" ] || [ "$GENERATE_KEY" = "y" ] || [ "$GENERATE_KEY" = "Y" ]; then
    FLAG_GENERATE_KEY=1
fi
if [ "$INSTALL_DAEMON" = "" ] || [ "$INSTALL_DAEMON" = "y" ] || [ "$INSTALL_DAEMON" = "Y" ]; then
    FLAG_INSTALL_DAEMON=1
fi

if [ "$FLAG_GLOBAL" -eq 1 ]; then
    BASE_BIN_DIR="/usr/local"
    BASE_CONF_DIR="/etc/"
    SYSTEMD_DIR="$BASE_CONF_DIR/systemd/system"
else
    BASE_BIN_DIR="$HOME/.local"
    BASE_CONF_DIR="${XDG_CONFIG_HOME:=$HOME/.config}"
    SYSTEMD_DIR="$BASE_CONF_DIR/systemd/user"
fi

BIN_DIR="$BASE_BIN_DIR/bin"
BIN_PATH="$BIN_DIR/lockdown"
CONF_DIR="$BASE_CONF_DIR/lockdown"
SYSTEMD_SERVICE_NAME="lockdown.service"
SYSTEMD_SERVICE_PATH="$SYSTEMD_DIR/$SYSTEMD_SERVICE_NAME"

#
# Show results of above and ask user if that's okay
#
echo "I'll be using the following locations:"
echo
echo "  Binary will be installed in: $BIN_PATH"
echo "  Configuration directory will be: $CONF_DIR"
if [ "$FLAG_INSTALL_DAEMON" -eq 1 ]; then
    echo "  Systemd service will be installed in: $SYSTEMD_SERVICE_PATH"
    echo "  Lockdown daemon configuration will be: $CONF_DIR/daemon.conf"
else
    echo "  Systemd service will not be installed"
fi
echo

read -p "Does this look okay? [Y/n]" LOOKS_OKAY
FLAG_LOOKS_OKAY=0
if [ "$LOOKS_OKAY" = "" ] || [ "$LOOKS_OKAY" = "y" ] || [ "$LOOKS_OKAY" = "Y" ]; then
    FLAG_LOOKS_OKAY=1
fi

if [ "$FLAG_LOOKS_OKAY" -eq 0 ]; then
    echo "Aborting..."
    exit 1
fi

#
# Installation
#
echo "Installing 'lockdown' binary in $BIN_DIR"
install -m 755 lockdown "$BIN_DIR"

echo "Creating configuration directory $CONF_DIR"
mkdir -p "$CONF_DIR"

if [ "$FLAG_GENERATE_KEY" -eq 1 ]; then
    echo "Generating keys in '$CONF_DIR'"
    CUR_DIR="$(pwd)"
    cd "$CONF_DIR"
    $BIN_DIR/lockdown genkey
    cd "$CUR_DIR"
fi

if [ "$(which systemctl)" = "" ]; then
    echo "systemctl not found. Daemon support not available." >&2
else
    if [ "$FLAG_INSTALL_DAEMON" -eq 1 ]; then
        echo "Installing lockdown daemon configuration in: $CONF_DIR/daemon.conf"
        install -D -m 644 contrib/lockdown-daemon.conf $CONF_DIR/daemon.conf

        echo "Installing lockdown daemon systemd service: $SYSTEMD_SERVICE_PATH"
        install -Dm644 "contrib/$SYSTEMD_SERVICE_NAME" $SYSTEMD_DIR

        echo "Enabling lockdown service"
        if [ "$FLAG_GLOBAL" -eq 1 ]; then
            systemctl daemon-reload
            systemctl enable --now "$SYSTEMD_SERVICE_NAME"
            systemctl start "$SYSTEMD_SERVICE_NAME"
        else
            systemctl --user daemon-reload
            systemctl --user enable --now "$SYSTEMD_SERVICE_NAME"
            systemctl --user start "$SYSTEMD_SERVICE_NAME"
            loginctl enable-linger $USER
        fi

        echo "Daemon installed. Check the README.md for how to interact with it"
    fi
fi

echo "Installation complete"
