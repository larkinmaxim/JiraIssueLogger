"""
Google Cloud Setup Helper Script

This script helps users set up their Google Cloud credentials for BigQuery.
It provides guidance on creating a service account and downloading credentials.
"""

import os
import sys
import webbrowser
import json
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


def check_credentials_file():
    """Check if credentials file exists and is valid."""
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if not creds_path:
        print("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        return False

    if not os.path.exists(creds_path):
        print(f"Credentials file not found at: {creds_path}")
        return False

    try:
        with open(creds_path, "r") as f:
            creds = json.load(f)

        required_keys = [
            "type",
            "project_id",
            "private_key_id",
            "private_key",
            "client_email",
        ]
        missing_keys = [key for key in required_keys if key not in creds]

        if missing_keys:
            print(
                f"Credentials file is missing required keys: {', '.join(missing_keys)}"
            )
            return False

        print(f"✅ Valid credentials file found at: {creds_path}")
        print(f"   Project ID: {creds.get('project_id')}")
        print(f"   Client Email: {creds.get('client_email')}")
        return True

    except json.JSONDecodeError:
        print(f"Credentials file is not valid JSON: {creds_path}")
        return False
    except Exception as e:
        print(f"Error checking credentials file: {str(e)}")
        return False


def guide_setup():
    """Guide the user through setting up Google Cloud credentials."""
    print_header("Google Cloud Credentials Setup Guide")

    print(
        "This guide will help you set up Google Cloud credentials for BigQuery access."
    )
    print("You'll need to create a service account and download a credentials file.")

    print_step(1, "Create a Google Cloud Project (if you don't have one already)")
    print("1. Go to the Google Cloud Console: https://console.cloud.google.com/")
    print("2. Click on the project dropdown at the top of the page")
    print("3. Click 'NEW PROJECT' and follow the prompts to create a new project")
    print("4. Make note of your project ID, you'll need it later")

    input("\nPress Enter when you're ready to continue...")

    print_step(2, "Enable the BigQuery API")
    print(
        "1. Go to: https://console.cloud.google.com/apis/library/bigquery.googleapis.com"
    )
    print("2. Make sure your project is selected")
    print("3. Click 'ENABLE' to enable the BigQuery API for your project")

    # Try to open the BigQuery API page
    try:
        webbrowser.open(
            "https://console.cloud.google.com/apis/library/bigquery.googleapis.com"
        )
    except:
        pass

    input("\nPress Enter when you're ready to continue...")

    print_step(3, "Create a Service Account")
    print("1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts")
    print("2. Make sure your project is selected")
    print("3. Click 'CREATE SERVICE ACCOUNT'")
    print("4. Enter a name for your service account (e.g., 'jira-logger')")
    print("5. Click 'CREATE AND CONTINUE'")
    print("6. For the role, select 'BigQuery > BigQuery Admin'")
    print("7. Click 'CONTINUE' and then 'DONE'")

    # Try to open the service accounts page
    try:
        webbrowser.open("https://console.cloud.google.com/iam-admin/serviceaccounts")
    except:
        pass

    input("\nPress Enter when you're ready to continue...")

    print_step(4, "Create and Download a Key")
    print("1. On the Service Accounts page, find the service account you just created")
    print("2. Click the three dots menu on the right and select 'Manage keys'")
    print("3. Click 'ADD KEY' and select 'Create new key'")
    print("4. Choose 'JSON' as the key type and click 'CREATE'")
    print("5. The key file will be downloaded to your computer")
    print("6. Move the key file to a secure location on your computer")

    input("\nPress Enter when you've downloaded the key file...")

    print_step(5, "Set the GOOGLE_APPLICATION_CREDENTIALS Environment Variable")

    # Ask for the path to the credentials file
    default_path = os.path.join(os.path.expanduser("~"), "google-credentials.json")
    creds_path = input(
        f"Enter the path to your credentials file [default: {default_path}]: "
    )

    if not creds_path:
        creds_path = default_path

    creds_path = os.path.abspath(os.path.expanduser(creds_path))

    # Check if the file exists
    if not os.path.exists(creds_path):
        print(f"\n❌ Credentials file not found at: {creds_path}")
        print("Please make sure the file exists and try again.")
        return

    # Set the environment variable
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

    print(f"\n✅ GOOGLE_APPLICATION_CREDENTIALS set to: {creds_path}")

    # Add to .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r") as f:
            env_content = f.read()

        # Check if the variable is already in the file
        if "GOOGLE_APPLICATION_CREDENTIALS" in env_content:
            print(
                "\nThe GOOGLE_APPLICATION_CREDENTIALS variable is already in your .env file."
            )
            print("You may want to update it with the new path.")
        else:
            # Add the variable to the file
            with open(env_file, "a") as f:
                f.write(
                    f"\n# Google Cloud Credentials\nGOOGLE_APPLICATION_CREDENTIALS={creds_path}\n"
                )
            print("\n✅ Added GOOGLE_APPLICATION_CREDENTIALS to your .env file.")

    print("\nTo set this environment variable permanently:")

    if sys.platform == "win32":
        print(f'  setx GOOGLE_APPLICATION_CREDENTIALS "{creds_path}"')
    else:
        print(
            f"  echo 'export GOOGLE_APPLICATION_CREDENTIALS=\"{creds_path}\"' >> ~/.bashrc"
        )
        print(
            f"  echo 'export GOOGLE_APPLICATION_CREDENTIALS=\"{creds_path}\"' >> ~/.zshrc"
        )

    print_step(6, "Verify Your Setup")

    # Check if the credentials file is valid
    if check_credentials_file():
        print("\n🎉 Your Google Cloud credentials are set up correctly!")
        print("You're ready to use BigQuery with the Jira Logger API.")
    else:
        print("\n❌ There was an issue with your credentials setup.")
        print("Please check the error messages above and try again.")


if __name__ == "__main__":
    # Check if credentials are already set up
    if check_credentials_file():
        print("\nYour Google Cloud credentials are already set up.")
        print(
            "If you want to set up new credentials, run this script with the --force flag:"
        )
        print("  python setup_google_cloud.py --force")

        if len(sys.argv) > 1 and sys.argv[1] == "--force":
            guide_setup()
    else:
        guide_setup()
