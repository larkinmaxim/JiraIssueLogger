"""
Script to fetch and save raw JSON responses from Jira API

This script uses the jira_logger.core.jira.parser module to fetch Jira issue data and save
the raw JSON responses to files. It can be used to collect data for
multiple issues at once.
"""

import os
import sys
import argparse
from jira_logger.core.jira.parser import connect_to_jira_api, extract_jira_data


def save_jira_issue(
    issue_key,
    raw_response_dir="jira_logger/data/jira_raw_responses",
    bypass_ssl_verify=None,
):
    """
    Fetch and save a Jira issue's raw JSON response

    Args:
        issue_key (str): The Jira issue key to retrieve
        raw_response_dir (str): Directory to save raw responses
        bypass_ssl_verify (bool): Whether to bypass SSL verification

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Fetching issue {issue_key}...")

    try:
        # Fetch Jira issue data and save raw response
        jira_data = connect_to_jira_api(
            issue_key=issue_key,
            bypass_ssl_verify=bypass_ssl_verify,
            save_raw_response=True,
            raw_response_dir=raw_response_dir,
        )

        if jira_data:
            print(f"✅ Successfully fetched and saved raw response for {issue_key}")

            # Extract and display some basic info
            details = extract_jira_data(jira_data)
            if details:
                print("\nIssue Details:")
                print(f"  Summary: {jira_data.get('fields', {}).get('summary', 'N/A')}")
                print(
                    f"  Status: {jira_data.get('fields', {}).get('status', {}).get('name', 'N/A')}"
                )
                print("\nPlanned Dates:")
                print(f"  Planned start: {details['Planned']['Planned start']}")
                print(f"  Planned finish: {details['Planned']['Planned finish']}")
                print(
                    f"  Planned duration: {details['Planned']['Planned duration']} days"
                )
                print("\nActual Dates:")
                print(f"  Actual start: {details['Actual']['Actual start']}")
                print(f"  Actual finish: {details['Actual']['Actual finish']}")
                print(f"  Actual duration: {details['Actual']['Actual duration']} days")

            return True
        else:
            print(f"❌ Failed to fetch data for issue {issue_key}")
            return False

    except Exception as e:
        print(f"❌ Error processing issue {issue_key}: {str(e)}")
        return False


def main():
    """Main function to parse arguments and run the script"""
    parser = argparse.ArgumentParser(
        description="Fetch and save raw JSON responses from Jira API"
    )

    # Add arguments
    parser.add_argument(
        "issues", nargs="*", help="Jira issue keys to fetch (e.g., EI-1234 EI-5678)"
    )
    parser.add_argument(
        "--dir",
        "-d",
        default="jira_logger/data/jira_raw_responses",
        help="Directory to save raw responses",
    )
    parser.add_argument(
        "--no-ssl-verify", action="store_true", help="Bypass SSL verification"
    )
    parser.add_argument("--file", "-f", help="File containing issue keys, one per line")

    # Parse arguments
    args = parser.parse_args()

    # Get issue keys from arguments or file
    issue_keys = []
    if args.issues:
        issue_keys.extend(args.issues)

    if args.file:
        try:
            with open(args.file, "r") as f:
                file_issues = [line.strip() for line in f if line.strip()]
                issue_keys.extend(file_issues)
        except Exception as e:
            print(f"Error reading issue keys from file: {str(e)}")

    # If no issue keys provided, prompt user
    if not issue_keys:
        print("No issue keys provided. Please enter issue keys separated by spaces:")
        user_input = input("> ")
        issue_keys = [key.strip() for key in user_input.split() if key.strip()]

    # Create output directory if it doesn't exist
    os.makedirs(args.dir, exist_ok=True)

    # Process each issue
    print(f"Will save raw responses to directory: {args.dir}")
    print(f"SSL verification: {'Disabled' if args.no_ssl_verify else 'Enabled'}")
    print(f"Processing {len(issue_keys)} issue(s)...")

    success_count = 0
    for issue_key in issue_keys:
        print("\n" + "=" * 50)
        if save_jira_issue(issue_key, args.dir, args.no_ssl_verify):
            success_count += 1

    # Print summary
    print("\n" + "=" * 50)
    print(
        f"Processed {len(issue_keys)} issue(s): {success_count} successful, {len(issue_keys) - success_count} failed"
    )
    print(f"Raw responses saved to: {os.path.abspath(args.dir)}")


if __name__ == "__main__":
    main()
