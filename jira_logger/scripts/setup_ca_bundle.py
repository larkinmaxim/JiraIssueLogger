"""
Setup CA Bundle Script

This script creates a CA bundle file that includes the Netskope root CA certificate
and sets the environment variable REQUESTS_CA_BUNDLE to point to that file.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80 + "\n")


def print_step(step_num, text):
    """Print a formatted step."""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 80)


def create_ca_bundle():
    """Create a CA bundle file that includes the Netskope root CA certificate."""
    print_header("Setup CA Bundle")

    # Define paths
    netskope_cert_path = r"C:\Netskope Certs\rootcaCert.pem"
    ca_bundle_dir = Path("jira_logger/data/certs")
    ca_bundle_path = ca_bundle_dir / "ca-bundle.pem"

    # Create directory if it doesn't exist
    print_step(1, "Creating directory for CA bundle")
    os.makedirs(ca_bundle_dir, exist_ok=True)
    print(f"✅ Directory created: {ca_bundle_dir}")

    # Check if Netskope certificate exists
    print_step(2, "Checking for Netskope certificate")
    if not os.path.exists(netskope_cert_path):
        print(f"❌ Netskope certificate not found at: {netskope_cert_path}")
        print("Please provide the correct path to the Netskope certificate.")
        return False

    print(f"✅ Found Netskope certificate at: {netskope_cert_path}")

    # Create CA bundle
    print_step(3, "Creating CA bundle")
    try:
        # Copy the Netskope certificate to the CA bundle
        shutil.copy2(netskope_cert_path, ca_bundle_path)
        print(f"✅ CA bundle created at: {ca_bundle_path}")
    except Exception as e:
        print(f"❌ Error creating CA bundle: {str(e)}")
        return False

    # Set environment variable
    print_step(4, "Setting environment variable")
    os.environ["REQUESTS_CA_BUNDLE"] = str(ca_bundle_path.absolute())
    print(
        f"✅ Environment variable REQUESTS_CA_BUNDLE set to: {os.environ['REQUESTS_CA_BUNDLE']}"
    )

    # Update .env file
    print_step(5, "Updating .env file")
    try:
        env_path = Path(".env")
        if not env_path.exists():
            print(f"❌ .env file not found at: {env_path}")
            return False

        # Read .env file
        with open(env_path, "r") as f:
            env_content = f.read()

        # Update or add REQUESTS_CA_BUNDLE
        if "REQUESTS_CA_BUNDLE" in env_content:
            # Replace existing value
            import re

            env_content = re.sub(
                r"REQUESTS_CA_BUNDLE=.*",
                f"REQUESTS_CA_BUNDLE={str(ca_bundle_path.absolute()).replace('\\', '\\\\')}",
                env_content,
            )
        else:
            # Add new variable
            env_content += f"\n# CA Bundle Configuration\nREQUESTS_CA_BUNDLE={str(ca_bundle_path.absolute()).replace('\\', '\\\\')}\n"

        # Write updated content
        with open(env_path, "w") as f:
            f.write(env_content)

        print(f"✅ .env file updated with REQUESTS_CA_BUNDLE")
    except Exception as e:
        print(f"❌ Error updating .env file: {str(e)}")
        return False

    print_header("CA Bundle Setup Complete")
    print("The CA bundle has been created and the environment variable has been set.")
    print("You can now run the BigQuery connection test again.")
    print(f"\nCA Bundle Path: {ca_bundle_path.absolute()}")
    print(
        f"Environment Variable: REQUESTS_CA_BUNDLE={os.environ['REQUESTS_CA_BUNDLE']}"
    )

    return True


if __name__ == "__main__":
    create_ca_bundle()
