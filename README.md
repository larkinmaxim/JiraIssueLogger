# Jira Logger

A Python application for logging and tracking Jira issues, with capabilities to store data in Google BigQuery for analytics and reporting.

## Features

- Automated Jira issue tracking and data collection
- Scheduled API calls to Jira for regular updates
- Data storage in Google BigQuery
- RESTful API for accessing and managing Jira data
- SSL certificate handling for secure connections

## Project Structure

```
jira_logger/
├── api/                  # API implementation
├── config/               # Configuration settings
├── core/                 # Core functionality
│   ├── bigquery/         # BigQuery integration
│   └── jira/             # Jira API integration
├── data/                 # Data storage
│   ├── jira_issues/      # Processed Jira issues
│   └── jira_raw_responses/ # Raw Jira API responses
├── docs/                 # Documentation
├── scripts/              # Utility scripts
│   └── test_scripts/     # Testing scripts
└── utils/                # Utility functions
```

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Configure environment variables in `.env` file (see `.env.example` for required variables)

## Usage

### Running the API Server

```bash
python jira_logger/run_api.py
```

### Saving Jira Responses

```bash
python jira_logger/scripts/save_jira_responses.py
```

### Setting up Google Cloud

```bash
python jira_logger/scripts/setup_google_cloud.py
```

## Documentation

For more detailed information, refer to the documentation in the `jira_logger/docs/` directory:

- [Product Requirements Document](jira_logger/docs/PRD.md)
- [Implementation Plan](jira_logger/docs/implementation_plan.md)
- [Deployment Guide](jira_logger/docs/deployment_guide.md)
- [API Documentation](jira_logger/docs/api_docs.md)

## License

[MIT License](LICENSE)


## Netskope SSL Interception Configuration

If you are using Netskope for SSL Interception, you need to configure the application to use the Netskope certificate.

### Windows

1. Run the `set_netskope_env.bat` script to set the environment variables:

```batch
set_netskope_env.bat
```

2. For Google Cloud SDK, run:

```batch
gcloud config set core/custom_ca_certs_file "C:\ProgramData\Netskope\STAgent\data\nscacert.pem"
```

### Linux/Mac

1. Run the `set_netskope_env.sh` script to set the environment variables:

```bash
source set_netskope_env.sh
```

2. For Google Cloud SDK, run:

```bash
gcloud config set core/custom_ca_certs_file 'C:\ProgramData\Netskope\STAgent\data\nscacert.pem'
```

### Environment Variables

The following environment variables are set by the scripts:

- `REQUESTS_CA_BUNDLE`: Path to the Netskope certificate
- `SSL_CERT_FILE`: Path to the Netskope certificate
- `CURL_CA_BUNDLE`: Path to the Netskope certificate
- `NODE_EXTRA_CA_CERTS`: Path to the Netskope certificate
- `PYTHONHTTPSVERIFY`: Set to 1 to enable SSL verification
- `GOOGLE_API_USE_CLIENT_CERTIFICATE`: Set to true to use client certificate

These environment variables are required for the application to work with Netskope SSL Interception.
