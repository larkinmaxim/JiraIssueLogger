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

# Jira Issue Logger - Cloud Run Deployment Guide

This repository contains a Jira Issue Logger application deployed to Google Cloud Run using GitHub Actions and Workload Identity Federation authentication.

## Project Configuration

- **Project ID**: tp-pmo-production
- **Project Number**: 924413780529
- **Region**: europe-west3
- **Service Name**: jira-logger
- **Service Account**: github-actions-sa@tp-pmo-production.iam.gserviceaccount.com

## Authentication Setup

The deployment uses Workload Identity Federation (WIF) for secure authentication between GitHub Actions and Google Cloud Platform.

### Workload Identity Configuration
- **Pool Name**: github-pool
- **Provider**: git
- **Provider Format**: `projects/924413780529/locations/global/workloadIdentityPools/github-pool/providers/git`

## GitHub Actions Workflow

The deployment workflow uses the following key actions:

1. `google-github-actions/auth@v2` for authentication
2. `google-github-actions/setup-gcloud@v2` for Cloud SDK setup
3. `google-github-actions/deploy-cloudrun@v2` for deployment

### Required Permissions

The GitHub workflow requires the following permissions:
```yaml
permissions:
  contents: 'read'
  id-token: 'write'
```

### Example Workflow Configuration

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

permissions:
  contents: 'read'
  id-token: 'write'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/924413780529/locations/global/workloadIdentityPools/github-pool/providers/git
          service_account: github-actions-sa@tp-pmo-production.iam.gserviceaccount.com

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Authorize Docker push
        run: gcloud auth configure-docker

      - name: Build and Push Container
        run: |
          docker build -t gcr.io/tp-pmo-production/jira-logger:${{ github.sha }} .
          docker push gcr.io/tp-pmo-production/jira-logger:${{ github.sha }}

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: jira-logger
          region: europe-west3
          image: gcr.io/tp-pmo-production/jira-logger:${{ github.sha }}
```

## Troubleshooting

Common issues and solutions:

1. **Authentication Errors**: 
   - Ensure the Workload Identity Provider format is correct
   - Verify the service account has necessary permissions
   - Check that GitHub workflow permissions are set correctly

2. **Deployment Failures**:
   - Verify Docker build succeeds locally
   - Check Cloud Run service account permissions
   - Ensure region and service names match configuration

## Important Notes

- Always use the latest versions of GitHub Actions (`@v2` or newer)
- Don't use the `audience` parameter in the Workload Identity Provider configuration
- Keep service account permissions minimal but sufficient for deployment
- Ensure Docker images are tagged appropriately

## References

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [GitHub Actions for Google Cloud](https://github.com/google-github-actions)
