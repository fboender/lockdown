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
    # If not specified, Lockdown looks in the same directory as the
    # .lockdown.conf file for a '.lockdown.key'.  Otherwise, it uses
    # '~/.config/lockdown/lockdown.key'

    # "priv_key_path": "/path/to/lockdown.key",


    # Optional path to public key.
    #
    # If not specified, Lockdown looks in the same directory as the
    # .lockdown.conf file for a '.lockdown.pub'. Otherwise, it uses
    # '~/.config/lockdown/lockdown.pub'

    # "pub_key_path": "/path/to/lockdown.pub",


    # Optionally you can define the pub key inline in the configuration. This
    # will always take precedence of any other configuration option or path.

    # "pub_key": "age1rtnnps27z8wf79fnftlm5qjyt4rd4hsdhvhuy85d94zykpzhzf7s24sdx9",


    # List of files to lock/unlock
    "lock_files": [
""")
        for file in files:
            fh.write(f"        \"{file}\",\n")

        fh.write(f"""    ],
}}
""")

    sys.stdout.write("Generated '.lockdown.conf' in current dir\n")
