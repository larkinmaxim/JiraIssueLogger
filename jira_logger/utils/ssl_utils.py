"""
Netskope SSL Certificate Utility Library

This library provides utility functions for working with Netskope SSL certificates,
including certificate validation, discovery, and SSL connection configuration.

Key Features:
- Find Netskope SSL certificates in common installation locations
- Validate certificate details using pyOpenSSL
- Support for SSL verification in network requests

Dependencies:
- pyOpenSSL (optional, but recommended for advanced certificate validation)
- requests (for SSL connection support)

Installation:
pip install pyopenssl requests

Usage Example:
```python
from jira_logger.utils.ssl_utils import find_netskope_certificate, validate_certificate

# Find Netskope certificate
cert_path = find_netskope_certificate()

# Validate certificate
if cert_path:
    cert_details = validate_certificate(cert_path)
    print(cert_details)
```
"""

import os
import warnings


def validate_certificate(cert_path):
    """
    Validate and extract information from a certificate file

    Args:
        cert_path (str): Path to the certificate file

    Returns:
        dict: Certificate validation details
    """
    try:
        import OpenSSL
    except ImportError:
        print(
            "Optional dependency pyOpenSSL not installed. Basic certificate validation unavailable."
        )
        print("Install with: pip install pyopenssl")
        return {
            "valid": None,
            "error": "pyOpenSSL not installed",
            "details": "Install pyOpenSSL for advanced certificate validation",
        }

    try:
        with open(cert_path, "rb") as cert_file:
            cert_data = cert_file.read()

        # Try to load the certificate
        try:
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cert_data
            )
        except OpenSSL.crypto.Error:
            try:
                x509 = OpenSSL.crypto.load_certificate(
                    OpenSSL.crypto.FILETYPE_ASN1, cert_data
                )
            except OpenSSL.crypto.Error:
                return {"valid": False, "error": "Unable to parse certificate file"}

        # Extract certificate details
        subject = x509.get_subject()
        issuer = x509.get_issuer()
        not_before = x509.get_notBefore().decode("ascii")
        not_after = x509.get_notAfter().decode("ascii")

        return {
            "valid": True,
            "subject": f"/CN={subject.CN}",
            "issuer": f"/CN={issuer.CN}",
            "not_before": not_before,
            "not_after": not_after,
            "serial_number": x509.get_serial_number(),
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def find_netskope_certificate():
    """
    Find Netskope SSL certificate in multiple potential locations

    Returns:
        str or None: Path to the Netskope certificate if found
    """
    potential_paths = [
        r"C:\ProgramData\Netskope\STAgent\data\nscacert_combined.pem",
        r"C:\Netskope Certs\rootcaCert.pem",
        os.path.expanduser(r"~\Netskope\rootcaCert.pem"),
        r"C:\Program Files\Netskope\rootcaCert.pem",
    ]

    for path in potential_paths:
        if os.path.exists(path):
            return path

    return None


def configure_ssl_verification(cert_path=None, bypass_verify=False):
    """
    Configure SSL verification for network requests

    Args:
        cert_path (str, optional): Path to the CA bundle or certificate. Defaults to None.
        bypass_verify (bool, optional): Bypass SSL verification. Defaults to False.

    Returns:
        tuple: (verify, ca_bundle) configuration for requests library
    """
    # If bypass_verify is True, disable SSL verification
    if bypass_verify:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        return False, None

    # If no cert_path provided, try to find Netskope certificate
    if not cert_path:
        cert_path = find_netskope_certificate()

    # Return the certificate path for verification
    return cert_path or True, cert_path


def print_ssl_debug_info(cert_path=None):
    """
    Print diagnostic information about SSL configuration

    Args:
        cert_path (str, optional): Path to the certificate. Defaults to None.
    """
    import ssl
    import json

    print("SSL Certificate Debug Information:")
    print(f"Environment REQUESTS_CA_BUNDLE: {os.environ.get('REQUESTS_CA_BUNDLE')}")
    print(f"Detected Netskope Certificate Path: {cert_path}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"User Home Directory: {os.path.expanduser('~')}")

    # Validate certificate if exists
    if cert_path:
        cert_validation = validate_certificate(cert_path)
        print("\nCertificate Validation:")
        print(json.dumps(cert_validation, indent=2))

    # Additional SSL context diagnostic
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        print("\nSSL Context Diagnostic:")
        print(f"Default CA Certs: {ssl.get_default_verify_paths()}")
    except Exception as diag_err:
        print(f"Could not retrieve additional SSL diagnostic info: {diag_err}")


# Expose a simple way to check if pyOpenSSL is available
def is_pyopenssl_available():
    """
    Check if pyOpenSSL is available

    Returns:
        bool: True if pyOpenSSL is installed, False otherwise
    """
    try:
        import OpenSSL

        return True
    except ImportError:
        return False


# Example usage when script is run directly
if __name__ == "__main__":
    # Demonstrate library usage
    cert_path = find_netskope_certificate()

    if cert_path:
        print(f"Found Netskope Certificate: {cert_path}")

        # Validate certificate
        cert_details = validate_certificate(cert_path)
        print("\nCertificate Details:")
        print(cert_details)

        # Print debug information
        print_ssl_debug_info(cert_path)
    else:
        print("No Netskope certificate found.")
