import sys
import ast
import os

import psutil

CONSOLE_MSG_SHOW = True


def read_config(path):
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


def console_msg(msg):
    if CONSOLE_MSG_SHOW is True:
        sys.stdout.write(f"{msg}\n")


def user_session_in_dir(path):
    for p in psutil.process_iter(["pid", "cwd", "name", "username"]):
        try:
            if p.info["username"] == psutil.Process().username():
                if p.info["cwd"] and p.info["cwd"].startswith(path):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return False
