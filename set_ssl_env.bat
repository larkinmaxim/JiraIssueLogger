@echo off
echo Setting up environment variables for SSL certificates...
set REQUESTS_CA_BUNDLE=E:\AI progects\NewJiraLogger\jira_logger\data\certs\ca-bundle.pem
set SSL_CERT_FILE=E:\AI progects\NewJiraLogger\jira_logger\data\certs\ca-bundle.pem
set CURL_CA_BUNDLE=E:\AI progects\NewJiraLogger\jira_logger\data\certs\ca-bundle.pem
set NODE_EXTRA_CA_CERTS=E:\AI progects\NewJiraLogger\jira_logger\data\certs\ca-bundle.pem
set PYTHONHTTPSVERIFY=1
set GOOGLE_API_USE_CLIENT_CERTIFICATE=true
echo Environment variables set successfully.
echo For Google Cloud SDK, run:
echo gcloud config set core/custom_ca_certs_file "E:\AI progects\NewJiraLogger\jira_logger\data\certs\ca-bundle.pem"
