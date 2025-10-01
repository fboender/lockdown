#!/bin/sh

# Strict mode
set -e           # fail when any command files


help ()
{
    echo "Usage: $0 [-g|--global]" >&2
    echo
    echo "Uninstall lockdown"
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
read -p "  Do you want to remove the configuration? [y/N]" REMOVE_CONF
echo

#
# Set all the correct flags and environment variables
#
FLAG_REMOVE_CONF=0
if [ "$REMOVE_CONF" = "y" ] || [ "$REMOVE_CONF" = "Y" ]; then
    FLAG_REMOVE_CONF=1
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
echo "  Binary will be uninstalled from: $BIN_PATH"
if [ "$FLAG_REMOVE_CONF" -eq 1 ]; then
    echo "  Configuration will be removed from: $CONF_DIR"
else
    echo "  Configuration will be kept in: $CONF_DIR"
fi
echo "  Systemd service (if installed) will be removed from: $SYSTEMD_SERVICE_PATH"
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
# Uninstall
#
echo "Removing binary $BIN_PATH"
rm -f "$BIN_PATH"

# Remove configuration (ask first)
if [ "$FLAG_REMOVE_CONF" -eq 1 ]; then
    echo "Removing $CONF_DIR/lockdown"
    rm -rf "$CONF_DIR"
fi

# Stop and remove systemd service
echo "Checking for systemd service in $SYSTEMD_SERVICE_PATH"
if [ -f "$SYSTEMD_SERVICE_PATH" ]; then
    echo "Stopping and removing systemd service $SYSTEMD_SERVICE_PATH"
    if [ "$FLAG_GLOBAL" -eq 1 ]; then
        systemctl stop "$SYSTEMD_SERVICE_NAME"
        systemctl disable "$SYSTEMD_SERVICE_NAME"
        rm -f "$SYSTEMD_SERVICE_PATH"
        systemctl daemon-reload
    else
        systemctl --user stop "$SYSTEMD_SERVICE_NAME"
        systemctl --user disable "$SYSTEMD_SERVICE_NAME"
        rm -f "$SYSTEMD_SERVICE_PATH"
        systemctl --user daemon-reload
    fi
else
    echo "Systemd service not found, skipping.."
fi

echo "Uninstallation complete"
