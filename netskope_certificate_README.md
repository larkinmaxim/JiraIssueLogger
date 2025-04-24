# Netskope SSL Certificate Utility Library

## Overview
This library provides utility functions for working with Netskope SSL certificates, including certificate validation, discovery, and SSL connection configuration.

## Features
- Find Netskope SSL certificates in common installation locations
- Validate certificate details using pyOpenSSL
- Support for SSL verification in network requests
- Diagnostic tools for SSL configuration

## Installation
```bash
pip install requests pyopenssl
```

## Usage Examples

### Finding Netskope Certificate
```python
from netskope_certificate import find_netskope_certificate

cert_path = find_netskope_certificate()
if cert_path:
    print(f"Netskope Certificate found at: {cert_path}")
```

### Validating Certificate
```python
from netskope_certificate import validate_certificate

cert_path = find_netskope_certificate()
if cert_path:
    cert_details = validate_certificate(cert_path)
    print(cert_details)
```

### Configuring SSL Verification
```python
from netskope_certificate import configure_ssl_verification
import requests

# Automatically find and use Netskope certificate
verify, ca_bundle = configure_ssl_verification()

# Make a request using the certificate
response = requests.get('https://your-secured-endpoint.com', verify=verify)
```

### SSL Debugging
```python
from netskope_certificate import print_ssl_debug_info

# Print detailed SSL configuration information
print_ssl_debug_info()
```

### Checking pyOpenSSL Availability
```python
from netskope_certificate import is_pyopenssl_available

if is_pyopenssl_available():
    print("Advanced certificate validation is available")
else:
    print("Install pyOpenSSL for advanced features")
```

## Configuration Options

### SSL Verification
- `configure_ssl_verification(cert_path=None, bypass_verify=False)`:
  - `cert_path`: Optional path to a specific certificate
  - `bypass_verify`: Set to `True` to disable SSL verification (use with caution)

## Troubleshooting
- Ensure `pyopenssl` is installed for advanced certificate validation
- Check that the Netskope certificate path is correct
- Use `print_ssl_debug_info()` to diagnose SSL configuration issues

## License
[Specify your license here]

## Contributing
Contributions are welcome! Please submit pull requests or open issues on the project repository.
