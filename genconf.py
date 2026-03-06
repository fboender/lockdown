import os
import sys


def gen_conf(files):
    if os.path.exists(".lockdown.conf"):
        sys.stderr.write(".lockdown.conf file already present in current dir. Aborting...\n")
        sys.exit(1)

    for file in files:
        if not os.path.exists(file):
            sys.stderr.write(f"File '{file}' not found. Aborting...\n")
            sys.exit(1)

    with open(".lockdown.conf", "w") as fh:
        fh.write(f"""{{
    # Optional path to private key.
    #
    # If not specified, Lockdown looks (in order) in other places for the key:
    #
    #  - Same directory as the .lockdown.conf (.lockdown.key)
    #  - The config directory in the home of the user that owns the
    #    .lockdown.conf file (~/.config/lockdown/lockdown.key). This is used
    #    when running in daemon mode as root.
    #  - The XDG_CONFIG_DIR of the current user
    #    (~/.config/lockdown/lockdown.key)
    #  - /etc/lockdown/lockdown.key

    #"priv_key_path": "/path/to/lockdown.key",


    # Optional path to public key.
    #
    # If not specified, Lockdown looks (in order) in other places for the key.
    # This works the same as the private key section above.

    #"pub_key_path": "/path/to/lockdown.pub",


    # List of files to lock/unlock

    "lock_files": [
""")
        for file in files:
            fh.write(f"        \"{file}\",\n")

        fh.write(f"""    ],
}}
""")

    sys.stdout.write("Generated '.lockdown.conf' in current dir\n")
