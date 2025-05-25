from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096,
)

key_name = "my-gcp-key"
private_key_path = os.path.expanduser(f"~/.ssh/{key_name}")
public_key_path = private_key_path + ".pub"

# serializing and writing to OpenSSH-format
with open(private_key_path, "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

# getting public key in OpenSSH-format
public_key = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.OpenSSH,
    format=serialization.PublicFormat.OpenSSH
).decode('utf-8')

# saving public key
with open(public_key_path, "w") as f:
    f.write(public_key + " your-username")

os.chmod(private_key_path, 0o600)

print(f"SSH key pair created:\n  Private: {private_key_path}\n  Public: {public_key_path}")
