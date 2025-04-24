# Configuring Python Requests with Netskope SSL Certificates

This guide focuses on configuring Python applications using the **requests** library to work with Netskope SSL interception.

## Using REQUESTS_CA_BUNDLE Environment Variable

Python-based tools that use the **requests** library can leverage the CA bundle referenced by the system variable **REQUESTS_CA_BUNDLE**.

### Step 1: Locate the Netskope Root CA Certificate

On Windows systems with Netskope client installed, the certificate is typically located at:
- `C:\ProgramData\Netskope\STAgent\data\nscacert_combined.pem`

### Step 2: Create a CA Bundle with Netskope Root CA

You have two options for creating your CA bundle:

#### Option A: Use the Netskope certificate directly
If the Netskope certificate file is already in PEM format and contains all necessary certificates, you can use it directly.

#### Option B: Create a custom bundle by combining certificates
If you need to combine the Netskope certificate with other trusted certificates:

```python
import certifi
import os

# Path to your Netskope certificate
netskope_cert_path = 'C:\\ProgramData\\Netskope\\STAgent\\data\\nscacert_combined.pem'

# Path for your new combined CA bundle
custom_ca_bundle_path = 'C:\\path\\to\\custom_ca_bundle.pem'

# Combine the default certificates with the Netskope certificate
with open(certifi.where(), 'rb') as default_ca_file:
    default_ca_content = default_ca_file.read()

with open(netskope_cert_path, 'rb') as netskope_ca_file:
    netskope_ca_content = netskope_ca_file.read()

with open(custom_ca_bundle_path, 'wb') as custom_ca_file:
    custom_ca_file.write(default_ca_content)
    custom_ca_file.write(b'\n')
    custom_ca_file.write(netskope_ca_content)

print(f"Custom CA bundle created at: {custom_ca_bundle_path}")
```

### Step 3: Set the REQUESTS_CA_BUNDLE Environment Variable

#### Setting the environment variable in Windows

In CMD:
```
set REQUESTS_CA_BUNDLE=C:\ProgramData\Netskope\STAgent\data\nscacert_combined.pem
```

In PowerShell:
```powershell
$env:REQUESTS_CA_BUNDLE = "C:\ProgramData\Netskope\STAgent\data\nscacert_combined.pem"
```

To set this permanently in Windows:
1. Open System Properties
2. Go to Advanced > Environment Variables
3. Add a new System variable named `REQUESTS_CA_BUNDLE` with the path to your CA bundle

#### Setting the environment variable in macOS/Linux:
```bash
export REQUESTS_CA_BUNDLE=/path/to/nscacert_combined.pem
```

To set this permanently, add the export command to your `.bashrc`, `.zshrc`, or equivalent shell configuration file.

### Step 4: Verify the Configuration

Create a test script to verify that your configuration is working:

```python
import requests
import os

print(f"REQUESTS_CA_BUNDLE is set to: {os.environ.get('REQUESTS_CA_BUNDLE', 'Not set')}")

try:
    response = requests.get('https://example.com')
    print(f"Connection successful: {response.status_code}")
except requests.exceptions.SSLError as e:
    print(f"SSL Error: {e}")
```

## For pip and Other Python Tools

Since pip also uses the requests library, setting the REQUESTS_CA_BUNDLE environment variable will apply to pip as well:

```bash
# Set environment variable before using pip
# Windows CMD:
set REQUESTS_CA_BUNDLE=C:\ProgramData\Netskope\STAgent\data\nscacert_combined.pem
pip install package-name

# Windows PowerShell:
$env:REQUESTS_CA_BUNDLE="C:\ProgramData\Netskope\STAgent\data\nscacert_combined.pem"
pip install package-name
```

## Troubleshooting

If you're still experiencing SSL certificate issues:

1. Verify the certificate path is correct and accessible to the Python process
2. Check if the certificate is in valid PEM format
3. Ensure no trailing whitespace in the environment variable value
4. Try listing the certificates in your bundle:

```python
import ssl
import os

bundle_path = os.environ.get('REQUESTS_CA_BUNDLE')
context = ssl.create_default_context(cafile=bundle_path)
print(f"Certificate store contains {len(context.get_ca_certs())} certificates")
```