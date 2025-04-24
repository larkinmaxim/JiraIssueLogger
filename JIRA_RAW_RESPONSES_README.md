# Jira Raw Response Saver

This tool allows you to fetch and save raw JSON responses from the Jira API for later analysis or debugging.

## Features

- Fetch data for one or multiple Jira issues
- Save raw JSON responses to files with timestamps
- Display basic issue information
- Support for SSL certificate configuration
- Batch processing of multiple issues

## Prerequisites

- Python 3.6 or higher
- Jira API credentials configured in `.env` file
- Required Python packages (see `requirements.txt`)

## Installation

No special installation is required. Just make sure you have the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Script

#### Windows

1. Double-click on `save_jira_responses.bat`
2. Enter the Jira issue keys when prompted

Or run from command line:

```batch
save_jira_responses.bat EI-1234 EI-5678
```

#### Linux/Mac

1. Make the script executable:
   ```bash
   chmod +x save_jira_responses.sh
   ```

2. Run the script:
   ```bash
   ./save_jira_responses.sh EI-1234 EI-5678
   ```

#### Direct Python Execution

```bash
python save_jira_responses.py EI-1234 EI-5678
```

### Command Line Options

```
usage: save_jira_responses.py [-h] [--dir DIR] [--no-ssl-verify] [--file FILE] [issues ...]

Fetch and save raw JSON responses from Jira API

positional arguments:
  issues                Jira issue keys to fetch (e.g., EI-1234 EI-5678)

optional arguments:
  -h, --help            show this help message and exit
  --dir DIR, -d DIR     Directory to save raw responses
  --no-ssl-verify       Bypass SSL verification
  --file FILE, -f FILE  File containing issue keys, one per line
```

### Examples

1. Fetch a single issue:
   ```bash
   python save_jira_responses.py EI-1234
   ```

2. Fetch multiple issues:
   ```bash
   python save_jira_responses.py EI-1234 EI-5678 EI-9012
   ```

3. Specify a custom directory for saving responses:
   ```bash
   python save_jira_responses.py EI-1234 --dir my_jira_data
   ```

4. Disable SSL verification (useful in some corporate environments):
   ```bash
   python save_jira_responses.py EI-1234 --no-ssl-verify
   ```

5. Read issue keys from a file:
   ```bash
   python save_jira_responses.py --file issue_list.txt
   ```
   Where `issue_list.txt` contains one issue key per line.

## Output

The script will:

1. Create a directory for raw responses (default: `jira_raw_responses`)
2. Save each response as a JSON file with the format: `{issue_key}_{timestamp}.json`
3. Display basic information about each issue
4. Show a summary of processed issues

## Troubleshooting

### SSL Certificate Issues

If you encounter SSL certificate issues, try:

1. Using the `--no-ssl-verify` option to bypass SSL verification
2. Setting up the Netskope certificate correctly (see `netskope_certificate_README.md`)
3. Checking your network proxy settings

### API Authentication Issues

If you have problems authenticating with the Jira API:

1. Check that your `.env` file contains valid `JIRA_BASE_URL` and `JIRA_API_TOKEN` values
2. Verify that your API token has not expired
3. Ensure you have the necessary permissions to access the issues

## License

[Specify your license here]
