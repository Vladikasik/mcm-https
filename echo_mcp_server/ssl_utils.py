"""
SSL utilities for generating self-signed certificates for development.
"""

import ipaddress
import os
import socket
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_self_signed_cert(
    cert_dir: Path, 
    hostname: str = "127.0.0.1",
    days_valid: int = 365
) -> Tuple[Path, Path]:
    """
    Generate a self-signed certificate for development use.
    
    Args:
        cert_dir: Directory to store the certificate files
        hostname: Hostname/IP for the certificate (default: 127.0.0.1)
        days_valid: Number of days the certificate is valid
        
    Returns:
        Tuple of (cert_file_path, key_file_path)
    """
    cert_dir.mkdir(parents=True, exist_ok=True)
    
    cert_file = cert_dir / "cert.pem"
    key_file = cert_dir / "key.pem"
    
    # If certificates already exist and are valid, return them
    if cert_file.exists() and key_file.exists():
        if _is_cert_valid(cert_file, days_valid // 2):  # Renew if less than half time left
            print(f"Using existing certificate: {cert_file}")
            return cert_file, key_file
    
    print(f"Generating self-signed certificate for {hostname}...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MCP Development"),
        x509.NameAttribute(NameOID.COMMON_NAME, hostname),
    ])
    
    # Build certificate
    cert_builder = x509.CertificateBuilder()
    cert_builder = cert_builder.subject_name(subject)
    cert_builder = cert_builder.issuer_name(issuer)
    cert_builder = cert_builder.public_key(private_key.public_key())
    cert_builder = cert_builder.serial_number(x509.random_serial_number())
    cert_builder = cert_builder.not_valid_before(datetime.utcnow())
    cert_builder = cert_builder.not_valid_after(datetime.utcnow() + timedelta(days=days_valid))
    
    # Add Subject Alternative Names for localhost, 127.0.0.1, etc.
    san_list = [
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]
    
    # Add the hostname if it's different
    if hostname not in ["localhost", "127.0.0.1"]:
        try:
            # Try to parse as IP address first
            ip_addr = ipaddress.ip_address(hostname)
            san_list.append(x509.IPAddress(ip_addr))
        except ValueError:
            # If not an IP, treat as DNS name
            san_list.append(x509.DNSName(hostname))
    
    cert_builder = cert_builder.add_extension(
        x509.SubjectAlternativeName(san_list),
        critical=False,
    )
    
    # Sign the certificate
    certificate = cert_builder.sign(private_key, hashes.SHA256())
    
    # Write certificate to file
    with open(cert_file, "wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))
    
    # Write private key to file
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    print(f"Certificate generated successfully:")
    print(f"  Certificate: {cert_file}")
    print(f"  Private Key: {key_file}")
    print(f"  Valid for: {days_valid} days")
    print()
    
    # Provide instructions for MCP Inspector
    _print_mcp_inspector_instructions(cert_file)
    
    return cert_file, key_file


def _print_mcp_inspector_instructions(cert_file: Path):
    """Print instructions for using the certificate with MCP Inspector."""
    print("🔍 MCP Inspector HTTPS Setup Instructions:")
    print("=" * 50)
    print("To use this HTTPS server with MCP Inspector, you have several options:")
    print()
    print("Option 1: Trust the certificate (Recommended)")
    if sys.platform == "darwin":  # macOS
        print(f"  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain {cert_file}")
        print("  Then restart your browser and MCP Inspector")
    elif sys.platform == "linux":  # Linux
        print(f"  # Copy certificate to system trust store")
        print(f"  sudo cp {cert_file} /usr/local/share/ca-certificates/mcp-dev.crt")
        print(f"  sudo update-ca-certificates")
        print("  Then restart your browser and MCP Inspector")
    elif sys.platform == "win32":  # Windows
        print(f"  # Import certificate to Windows Certificate Store")
        print(f"  certlm.msc -> Trusted Root Certification Authorities -> Import -> {cert_file}")
        print("  Then restart your browser and MCP Inspector")
    
    print()
    print("Option 2: Browser bypass (Temporary)")
    print("  1. Open https://127.0.0.1:8443/mcp in your browser")
    print("  2. Click 'Advanced' and 'Proceed to 127.0.0.1'")
    print("  3. Now try connecting with MCP Inspector")
    print()
    print("Option 3: Use HTTP mode for testing")
    print("  python main.py --no-ssl --port 8080")
    print("  Then connect MCP Inspector to: http://127.0.0.1:8080/mcp")
    print("=" * 50)
    print()


def install_certificate_to_system(cert_file: Path) -> bool:
    """
    Attempt to install the certificate to the system trust store.
    
    Args:
        cert_file: Path to the certificate file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if sys.platform == "darwin":  # macOS
            cmd = [
                "sudo", "security", "add-trusted-cert", 
                "-d", "-r", "trustRoot", 
                "-k", "/Library/Keychains/System.keychain", 
                str(cert_file)
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✓ Certificate installed to macOS system keychain")
            return True
            
        elif sys.platform == "linux":  # Linux
            # Copy to ca-certificates directory
            dest_file = f"/usr/local/share/ca-certificates/mcp-dev-{cert_file.stem}.crt"
            subprocess.run(["sudo", "cp", str(cert_file), dest_file], check=True)
            subprocess.run(["sudo", "update-ca-certificates"], check=True)
            print(f"✓ Certificate installed to Linux CA certificates")
            return True
            
        else:
            print(f"⚠ Automatic certificate installation not supported on {sys.platform}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install certificate: {e}")
        return False
    except Exception as e:
        print(f"✗ Error installing certificate: {e}")
        return False


def _is_cert_valid(cert_file: Path, min_days_left: int = 30) -> bool:
    """
    Check if a certificate exists and is valid for at least min_days_left days.
    """
    try:
        with open(cert_file, "rb") as f:
            cert_data = f.read()
        
        certificate = x509.load_pem_x509_certificate(cert_data)
        
        # Check if certificate expires within min_days_left
        expires_soon = datetime.utcnow() + timedelta(days=min_days_left)
        
        return certificate.not_valid_after > expires_soon
    except Exception:
        return False


def get_cert_info(cert_file: Path) -> dict:
    """
    Get information about a certificate file.
    """
    try:
        with open(cert_file, "rb") as f:
            cert_data = f.read()
        
        certificate = x509.load_pem_x509_certificate(cert_data)
        
        return {
            "subject": certificate.subject,
            "issuer": certificate.issuer,
            "not_valid_before": certificate.not_valid_before,
            "not_valid_after": certificate.not_valid_after,
            "serial_number": certificate.serial_number,
        }
    except Exception as e:
        return {"error": str(e)} 