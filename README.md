# Jira Logger with BigQuery Integration

A comprehensive solution for tracking Jira issues and storing their details in BigQuery, with automatic duplicate prevention.

## Overview

This project provides a FastAPI application with three main endpoints:

1. **Update Status Endpoint**: Fetches all Jira issues with specified statuses and updates BigQuery
2. **Collect Closed/Deployed PD Details**: Collects details for issues in "closed" or "deployed pd" status with empty details
3. **Collect Deployed AC Details**: Collects/updates details for issues in "deployed ac" status

The application prevents duplicates in the BigQuery table by using MERGE operations and selective updates.

## Features

- **Jira Integration**: Connects to Jira API to fetch issue data and status updates
- **BigQuery Storage**: Stores issue data in BigQuery with a well-defined schema
- **Duplicate Prevention**: Uses BigQuery MERGE operations to prevent duplicates
- **Netskope SSL Support**: Includes robust SSL certificate handling for corporate environments
- **Scheduling Options**: Multiple ways to schedule periodic data collection
- **Docker Support**: Containerized deployment with Docker and Docker Compose
- **Comprehensive Documentation**: Detailed guides for deployment and usage

## Documentation

- [API Documentation](API_README.md): Detailed information about the API endpoints and usage
- [Implementation Plan](documentation/implementation_plan.md): Overview of the system architecture and components
- [Deployment Guide](documentation/deployment_guide.md): Instructions for deploying in different environments

## Components

### FastAPI Application
The core of the system, providing RESTful endpoints for Jira data collection and BigQuery integration.

### Jira API Client
Reuses and extends the existing Jira API integration code with SSL certificate management.

### BigQuery Integration
Uses Google Cloud Python client library to store and update Jira issue data.

### Scheduler
Optional component to trigger the endpoints on a daily basis.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env
# Edit .env with your Jira credentials

# Run the API server
python run_api.py
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Testing

```bash
# Test the API endpoints
python test_api.py
```

## Original Components

This project builds upon and extends the following original components:

### Netskope Certificate Library
A standalone utility library for managing Netskope SSL certificates, located in `netskope_certificate.py`.

### Jira Issue Parser
The original parser for Jira issues with SSL certificate support, now integrated into the FastAPI application.

## License
[Specify your license here]

## Contributing
Contributions are welcome! Please submit pull requests or open issues on the project repository.
