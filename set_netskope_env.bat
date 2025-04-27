@echo off
echo Setting up environment variables for Netskope SSL Interception...
set REQUESTS_CA_BUNDLE=C:\ProgramData\Netskope\STAgent\data\nscacert.pem
set SSL_CERT_FILE=C:\ProgramData\Netskope\STAgent\data\nscacert.pem
set CURL_CA_BUNDLE=C:\ProgramData\Netskope\STAgent\data\nscacert.pem
set NODE_EXTRA_CA_CERTS=C:\ProgramData\Netskope\STAgent\data\nscacert.pem
set PYTHONHTTPSVERIFY=1
set GOOGLE_API_USE_CLIENT_CERTIFICATE=true
echo Environment variables set successfully.
echo For Google Cloud SDK, run:
echo gcloud config set core/custom_ca_certs_file "C:\ProgramData\Netskope\STAgent\data\nscacert.pem"
