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

install -m 755 lockdown "$BINDIR"
echo "'lockdown' installed in $BINDIR"
install -m 755 lockdownd "$BINDIR"
echo "'lockdownd' installed in $BINDIR"
