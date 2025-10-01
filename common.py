import sys
import ast
import os

import psutil


def read_config(path):
    """
    Read a configuration file in python literals format. You can use comments,
    [], (), tripple-quotes strings, etc.
    """
    with open(path, 'r') as fh:
        try:
            conf = ast.literal_eval(fh.read())
            return conf
        except Exception as err:
            try:
                msg, rest = err.args
                src, line_no, char_no, line = rest
                sys.stderr.write(f"Invalid configuration file: {msg} on line {line_no}:\n\n")
                sys.stderr.write(f"    {line.strip()}\n")
                sys.stderr.write(f"    {" " * (char_no - 9)}^\n\n")
                sys.stderr.write("The actual error may be higher up.\n")
            except ValueError:
                sys.stderr.write(f"Invalid configuration file: {err}\n")
                pass
            sys.exit(1)


def find_up(start_path, filename):
    """
    Traverse up directories and try to find 'filename' file.
    """
    try_path = start_path.rstrip("/")
    while try_path != "/":
        try_conf = os.path.join(try_path, filename)
        if os.path.exists(try_conf):
            return try_conf

        try_path = os.path.dirname(try_path)

    return None


def user_session_in_dir(path):
    """
    Go through all the user's processes and check if any of their current
    working directories is under `path`.
    """
    for p in psutil.process_iter(["pid", "cwd", "name", "username"]):
        try:
            if p.info["username"] == psutil.Process().username():
                if p.info["cwd"] and p.info["cwd"].startswith(path):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return False

def xdg_config_home(path):
    xdg_config_home = None

    if "XDG_CONFIG_HOME" in os.environ:
        xdg_config_home = os.environ["XDG_CONFIG_HOME"]
    else:
        xdg_config_home = "~/.config"

    return os.path.expanduser(os.path.join(xdg_config_home, path))
