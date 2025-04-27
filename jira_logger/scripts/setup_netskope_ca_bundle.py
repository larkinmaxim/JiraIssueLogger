"""
Setup Netskope CA Bundle Script

This script creates a CA bundle file that includes the Netskope root CA certificate
from the correct path and sets the environment variables for SSL verification.
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
    print_header("Setup Netskope CA Bundle")

    # Define paths for Netskope certificates
    netskope_cert_paths = [
        r"C:\ProgramData\Netskope\STAgent\data\nscacert.pem",  # Standard Netskope cert path
        r"C:\ProgramData\Netskope\STAgent\data\nscacert_combined.pem",  # Combined cert path
        r"C:\Netskope Certs\rootcaCert.pem",  # Custom cert path
    ]

    # Find the first certificate that exists
    print_step(1, "Finding Netskope certificate")
    netskope_cert_path = None
    for cert_path in netskope_cert_paths:
        if os.path.exists(cert_path):
            netskope_cert_path = cert_path
            break

    if not netskope_cert_path:
        print(f"❌ Netskope certificate not found at any of the expected locations:")
        for cert_path in netskope_cert_paths:
            print(f"   - {cert_path}")
        return False

    print(f"✅ Found Netskope certificate at: {netskope_cert_path}")

    # Define CA bundle path
    ca_bundle_dir = Path("jira_logger/data/certs")
    ca_bundle_path = ca_bundle_dir / "ca-bundle.pem"

    # Create directory if it doesn't exist
    print_step(2, "Creating directory for CA bundle")
    os.makedirs(ca_bundle_dir, exist_ok=True)
    print(f"✅ Directory created: {ca_bundle_dir}")

    # Create CA bundle
    print_step(3, "Creating CA bundle")
    try:
        # Copy the Netskope certificate to the CA bundle
        shutil.copy2(netskope_cert_path, ca_bundle_path)
        print(f"✅ CA bundle created at: {ca_bundle_path}")
    except Exception as e:
        print(f"❌ Error creating CA bundle: {str(e)}")
        return False

    # Set environment variables
    print_step(4, "Setting environment variables")
    os.environ["REQUESTS_CA_BUNDLE"] = str(ca_bundle_path.absolute())
    os.environ["SSL_CERT_FILE"] = str(ca_bundle_path.absolute())
    os.environ["CURL_CA_BUNDLE"] = str(ca_bundle_path.absolute())
    os.environ["NODE_EXTRA_CA_CERTS"] = str(ca_bundle_path.absolute())
    os.environ["PYTHONHTTPSVERIFY"] = "1"
    os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "true"

    print(f"✅ Environment variables set:")
    print(f"   REQUESTS_CA_BUNDLE={os.environ['REQUESTS_CA_BUNDLE']}")
    print(f"   SSL_CERT_FILE={os.environ['SSL_CERT_FILE']}")
    print(f"   CURL_CA_BUNDLE={os.environ['CURL_CA_BUNDLE']}")
    print(f"   NODE_EXTRA_CA_CERTS={os.environ['NODE_EXTRA_CA_CERTS']}")
    print(f"   PYTHONHTTPSVERIFY={os.environ['PYTHONHTTPSVERIFY']}")
    print(
        f"   GOOGLE_API_USE_CLIENT_CERTIFICATE={os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE']}"
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

        # Check if the SSL section already exists
        if "# SSL Certificate Configuration" in env_content:
            # Replace existing values
            import re

            for var_name in [
                "REQUESTS_CA_BUNDLE",
                "SSL_CERT_FILE",
                "CURL_CA_BUNDLE",
                "NODE_EXTRA_CA_CERTS",
                "PYTHONHTTPSVERIFY",
                "GOOGLE_API_USE_CLIENT_CERTIFICATE",
            ]:
                if var_name in env_content:
                    env_content = re.sub(
                        f"{var_name}=.*",
                        f"{var_name}={os.environ[var_name].replace('\\', '\\\\')}",
                        env_content,
                    )
                else:
                    env_content += (
                        f"{var_name}={os.environ[var_name].replace('\\', '\\\\')}\n"
                    )
        else:
            # Add new section
            env_content += "\n# SSL Certificate Configuration\n"
            env_content += f"REQUESTS_CA_BUNDLE={os.environ['REQUESTS_CA_BUNDLE'].replace('\\', '\\\\')}\n"
            env_content += (
                f"SSL_CERT_FILE={os.environ['SSL_CERT_FILE'].replace('\\', '\\\\')}\n"
            )
            env_content += (
                f"CURL_CA_BUNDLE={os.environ['CURL_CA_BUNDLE'].replace('\\', '\\\\')}\n"
            )
            env_content += f"NODE_EXTRA_CA_CERTS={os.environ['NODE_EXTRA_CA_CERTS'].replace('\\', '\\\\')}\n"
            env_content += f"PYTHONHTTPSVERIFY={os.environ['PYTHONHTTPSVERIFY']}\n"
            env_content += f"GOOGLE_API_USE_CLIENT_CERTIFICATE={os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE']}\n"

        # Write updated content
        with open(env_path, "w") as f:
            f.write(env_content)

        print(f"✅ .env file updated with SSL certificate configuration")
    except Exception as e:
        print(f"❌ Error updating .env file: {str(e)}")
        return False

    # Create batch script to set environment variables
    print_step(6, "Creating batch script to set environment variables")
    batch_script_path = Path("set_ssl_env.bat")
    with open(batch_script_path, "w") as f:
        f.write("@echo off\n")
        f.write("echo Setting up environment variables for SSL certificates...\n")
        f.write(f"set REQUESTS_CA_BUNDLE={os.environ['REQUESTS_CA_BUNDLE']}\n")
        f.write(f"set SSL_CERT_FILE={os.environ['SSL_CERT_FILE']}\n")
        f.write(f"set CURL_CA_BUNDLE={os.environ['CURL_CA_BUNDLE']}\n")
        f.write(f"set NODE_EXTRA_CA_CERTS={os.environ['NODE_EXTRA_CA_CERTS']}\n")
        f.write(f"set PYTHONHTTPSVERIFY={os.environ['PYTHONHTTPSVERIFY']}\n")
        f.write(
            f"set GOOGLE_API_USE_CLIENT_CERTIFICATE={os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE']}\n"
        )
        f.write("echo Environment variables set successfully.\n")
        f.write("echo For Google Cloud SDK, run:\n")
        f.write(
            f'echo gcloud config set core/custom_ca_certs_file "{ca_bundle_path.absolute()}"\n'
        )

    print(f"✅ Batch script created at: {batch_script_path}")

    # Create shell script for Linux/Mac
    shell_script_path = Path("set_ssl_env.sh")
    with open(shell_script_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo Setting up environment variables for SSL certificates...\n")
        f.write(f"export REQUESTS_CA_BUNDLE='{os.environ['REQUESTS_CA_BUNDLE']}'\n")
        f.write(f"export SSL_CERT_FILE='{os.environ['SSL_CERT_FILE']}'\n")
        f.write(f"export CURL_CA_BUNDLE='{os.environ['CURL_CA_BUNDLE']}'\n")
        f.write(f"export NODE_EXTRA_CA_CERTS='{os.environ['NODE_EXTRA_CA_CERTS']}'\n")
        f.write(f"export PYTHONHTTPSVERIFY='{os.environ['PYTHONHTTPSVERIFY']}'\n")
        f.write(
            f"export GOOGLE_API_USE_CLIENT_CERTIFICATE='{os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE']}'\n"
        )
        f.write("echo Environment variables set successfully.\n")
        f.write("echo For Google Cloud SDK, run:\n")
        f.write(
            f"echo gcloud config set core/custom_ca_certs_file '{ca_bundle_path.absolute()}'\n"
        )

    print(f"✅ Shell script created at: {shell_script_path}")

    print_header("Netskope CA Bundle Setup Complete")
    print("The CA bundle has been created and the environment variables have been set.")
    print("You can now run the BigQuery connection test again.")
    print(f"\nCA Bundle Path: {ca_bundle_path.absolute()}")
    print(f"Environment Variables:")
    print(f"   REQUESTS_CA_BUNDLE={os.environ['REQUESTS_CA_BUNDLE']}")
    print(f"   SSL_CERT_FILE={os.environ['SSL_CERT_FILE']}")
    print(f"   CURL_CA_BUNDLE={os.environ['CURL_CA_BUNDLE']}")
    print(f"   NODE_EXTRA_CA_CERTS={os.environ['NODE_EXTRA_CA_CERTS']}")
    print(f"   PYTHONHTTPSVERIFY={os.environ['PYTHONHTTPSVERIFY']}")
    print(
        f"   GOOGLE_API_USE_CLIENT_CERTIFICATE={os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE']}"
    )
    print("\nFor Google Cloud SDK, run:")
    print(f'gcloud config set core/custom_ca_certs_file "{ca_bundle_path.absolute()}"')

    return True


if __name__ == "__main__":
    create_ca_bundle()
