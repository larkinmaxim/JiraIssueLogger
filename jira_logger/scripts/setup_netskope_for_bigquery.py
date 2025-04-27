"""
Setup Netskope for BigQuery Script

This script sets up the environment variables and configuration files
for using BigQuery with Netskope SSL Interception.
"""

import os
import sys
import shutil
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


def setup_netskope_for_bigquery():
    """Set up Netskope for BigQuery."""
    print_header("Setup Netskope for BigQuery")

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

    # Update .env file
    print_step(2, "Updating .env file")
    env_path = Path(".env")
    if not env_path.exists():
        print(f"❌ .env file not found at: {env_path}")
        return False

    # Read .env file
    with open(env_path, "r") as f:
        env_content = f.read()

    # Update or add environment variables
    env_vars = {
        "REQUESTS_CA_BUNDLE": netskope_cert_path,
        "SSL_CERT_FILE": netskope_cert_path,
        "CURL_CA_BUNDLE": netskope_cert_path,
        "NODE_EXTRA_CA_CERTS": netskope_cert_path,
        "PYTHONHTTPSVERIFY": "1",
        "GOOGLE_API_USE_CLIENT_CERTIFICATE": "true",
    }

    # Check if the Netskope section already exists
    if "# Netskope SSL Interception Configuration" in env_content:
        print("ℹ️ Netskope section already exists in .env file, updating...")
        # Update existing variables
        for var_name, var_value in env_vars.items():
            import re

            pattern = rf"{var_name}=.*"
            replacement = f"{var_name}={var_value.replace('\\', '\\\\')}"
            if re.search(pattern, env_content):
                env_content = re.sub(pattern, replacement, env_content)
            else:
                env_content += f"\n{var_name}={var_value.replace('\\', '\\\\')}"
    else:
        print("ℹ️ Adding Netskope section to .env file...")
        # Add new section
        env_content += "\n\n# Netskope SSL Interception Configuration\n"
        for var_name, var_value in env_vars.items():
            env_content += f"{var_name}={var_value.replace('\\', '\\\\')}\n"

    # Write updated content
    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"✅ .env file updated with Netskope SSL Interception Configuration")

    # Create a script to set environment variables
    print_step(3, "Creating script to set environment variables")

    # Create batch script for Windows
    batch_script_path = Path("set_netskope_env.bat")
    with open(batch_script_path, "w") as f:
        f.write("@echo off\n")
        f.write(
            "echo Setting up environment variables for Netskope SSL Interception...\n"
        )
        for var_name, var_value in env_vars.items():
            f.write(f"set {var_name}={var_value}\n")
        f.write("echo Environment variables set successfully.\n")
        f.write("echo For Google Cloud SDK, run:\n")
        f.write(
            f'echo gcloud config set core/custom_ca_certs_file "{netskope_cert_path}"\n'
        )

    print(f"✅ Batch script created at: {batch_script_path}")

    # Create shell script for Linux/Mac
    shell_script_path = Path("set_netskope_env.sh")
    with open(shell_script_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(
            "echo Setting up environment variables for Netskope SSL Interception...\n"
        )
        for var_name, var_value in env_vars.items():
            f.write(f"export {var_name}='{var_value}'\n")
        f.write("echo Environment variables set successfully.\n")
        f.write("echo For Google Cloud SDK, run:\n")
        f.write(
            f"echo gcloud config set core/custom_ca_certs_file '{netskope_cert_path}'\n"
        )

    print(f"✅ Shell script created at: {shell_script_path}")

    # Update README.md with instructions
    print_step(4, "Updating README.md with instructions")
    readme_path = Path("README.md")
    if not readme_path.exists():
        print(f"ℹ️ README.md file not found, creating...")
        with open(readme_path, "w") as f:
            f.write("# Jira Logger\n\n")

    # Read README.md file
    with open(readme_path, "r") as f:
        readme_content = f.read()

    # Check if the Netskope section already exists
    if "## Netskope SSL Interception Configuration" in readme_content:
        print("ℹ️ Netskope section already exists in README.md, skipping...")
    else:
        print("ℹ️ Adding Netskope section to README.md...")
        # Add new section
        readme_content += "\n\n## Netskope SSL Interception Configuration\n\n"
        readme_content += "If you are using Netskope for SSL Interception, you need to configure the application to use the Netskope certificate.\n\n"
        readme_content += "### Windows\n\n"
        readme_content += "1. Run the `set_netskope_env.bat` script to set the environment variables:\n\n"
        readme_content += "```batch\n"
        readme_content += "set_netskope_env.bat\n"
        readme_content += "```\n\n"
        readme_content += "2. For Google Cloud SDK, run:\n\n"
        readme_content += "```batch\n"
        readme_content += (
            f'gcloud config set core/custom_ca_certs_file "{netskope_cert_path}"\n'
        )
        readme_content += "```\n\n"
        readme_content += "### Linux/Mac\n\n"
        readme_content += "1. Run the `set_netskope_env.sh` script to set the environment variables:\n\n"
        readme_content += "```bash\n"
        readme_content += "source set_netskope_env.sh\n"
        readme_content += "```\n\n"
        readme_content += "2. For Google Cloud SDK, run:\n\n"
        readme_content += "```bash\n"
        readme_content += (
            f"gcloud config set core/custom_ca_certs_file '{netskope_cert_path}'\n"
        )
        readme_content += "```\n\n"
        readme_content += "### Environment Variables\n\n"
        readme_content += (
            "The following environment variables are set by the scripts:\n\n"
        )
        readme_content += "- `REQUESTS_CA_BUNDLE`: Path to the Netskope certificate\n"
        readme_content += "- `SSL_CERT_FILE`: Path to the Netskope certificate\n"
        readme_content += "- `CURL_CA_BUNDLE`: Path to the Netskope certificate\n"
        readme_content += "- `NODE_EXTRA_CA_CERTS`: Path to the Netskope certificate\n"
        readme_content += "- `PYTHONHTTPSVERIFY`: Set to 1 to enable SSL verification\n"
        readme_content += "- `GOOGLE_API_USE_CLIENT_CERTIFICATE`: Set to true to use client certificate\n\n"
        readme_content += "These environment variables are required for the application to work with Netskope SSL Interception.\n"

        # Write updated content
        with open(readme_path, "w") as f:
            f.write(readme_content)

        print(f"✅ README.md updated with Netskope SSL Interception Configuration")

    print_header("Setup Complete")
    print("The Netskope SSL Interception Configuration has been set up successfully.")
    print("You can now run the application with Netskope SSL Interception.")
    print("\nTo set the environment variables:")
    print("- Windows: Run set_netskope_env.bat")
    print("- Linux/Mac: Run source set_netskope_env.sh")
    print("\nFor Google Cloud SDK, run:")
    print(f'gcloud config set core/custom_ca_certs_file "{netskope_cert_path}"')

    return True


if __name__ == "__main__":
    setup_netskope_for_bigquery()
