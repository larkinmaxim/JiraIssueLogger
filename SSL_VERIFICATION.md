# SSL Verification in Jira Logger

This document explains the SSL certificate verification settings in the Jira Logger application.

## Overview

SSL certificate verification has been disabled by default in this application to handle environments with corporate proxies (like Netskope) that perform SSL inspection.

## Changes Made

The following changes were implemented to disable SSL verification:

1. **Default Setting**: Changed `use_ssl_verification` default to `False` in `jira_logger/config/settings.py`

2. **Jira API Client**: Updated `fetch_jira_issue_data()` in `jira_logger/core/jira/client.py` to respect the global SSL settings

3. **Scheduler**: Modified the scheduler's API calls in `jira_logger/core/scheduler.py` to use the SSL settings

4. **Docker**: Added environment variables in `docker-compose.yml` to disable SSL verification in containers

## Usage

### How to Enable SSL Verification

If you want to enable SSL verification (recommended for production):

1. Set the environment variable:
   ```
   USE_SSL_VERIFICATION=true
   ```

2. Or modify `.env` file:
   ```
   USE_SSL_VERIFICATION=true
   ```

### Providing Custom Certificates

If you need to use custom certificates:

1. Set the certificate path:
   ```
   SSL_CERT_PATH=/path/to/your/certificate.pem
   ```

2. Enable verification:
   ```
   USE_SSL_VERIFICATION=true
   ```

## Security Considerations

- Disabling SSL verification bypasses important security checks
- Only use this approach in controlled environments where security implications are understood
- In production, use proper certificates or a secure certificate chain

## Troubleshooting

If you encounter SSL issues:

1. Check if the Netskope certificate exists at `C:\Netskope Certs\nscacert_combined.pem`
2. Verify certificate format is valid using `jira_logger/utils/ssl_utils.py`
3. Set appropriate environment variables for your environment 