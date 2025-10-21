import getpass
import sys
import os

import pyrage


def gen_key(output_base_name):
    """
    Generate password protected (encrypted) age private and public key and
    output to stdout.
    """
    for ext in ["key", "pub"]:
        if os.path.exists(f"{output_base_name}.{ext}"):
            sys.stderr.write(f"{output_base_name}.{ext} already exists. Aborting...\n")
            sys.exit(1)

    passwd1 = getpass.getpass("Password for the new key?: ")
    passwd2 = getpass.getpass("Verify password?: ")

    if passwd1 != passwd2:
        sys.stderr.write("Passwords do not match. Aborting\n")
        sys.exit(1)

    identity = pyrage.x25519.Identity.generate()
    public_key = identity.to_public()
    private_key = str(identity).encode("ascii")
    encrypted_key = pyrage.passphrase.encrypt(private_key, passwd1)

    sys.stdout.write("\n")
    with open(f"{output_base_name}.key", "wb") as fh:
        fh.write(encrypted_key)
    os.chmod(f"{output_base_name}.key", 0o600)

    sys.stdout.write(f"Wrote encrypted key to '{output_base_name}.key'\n")

    with open(f"{output_base_name}.pub", "w") as fh:
        fh.write(str(public_key))
    os.chmod(f"{output_base_name}.pub", 0o644)
    sys.stdout.write(f"Wrote public key to '{output_base_name}.pub'\n")
