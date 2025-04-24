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
