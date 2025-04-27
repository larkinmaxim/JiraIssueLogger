"""
Script to fix null bytes in __init__.py files.

This script reads all __init__.py files in the jira_logger directory,
removes any null bytes, and writes the files back.
"""

import os
import glob


def fix_init_file(file_path):
    """
    Fix null bytes in a file.

    Args:
        file_path: Path to the file to fix
    """
    try:
        # Read the file content
        with open(file_path, "rb") as f:
            content = f.read()

        # Remove null bytes
        content = content.replace(b"\x00", b"")

        # Write the file back
        with open(file_path, "wb") as f:
            f.write(content)

        print(f"Fixed {file_path}")
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")


def main():
    """
    Main function to fix all __init__.py files.
    """
    # Find all __init__.py files
    init_files = glob.glob("jira_logger/**/__init__.py", recursive=True)
    init_files.append("jira_logger/__init__.py")

    # Fix each file
    for file_path in init_files:
        fix_init_file(file_path)


if __name__ == "__main__":
    main()
