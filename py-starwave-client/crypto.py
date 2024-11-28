import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os

def hash(message):
    return hashlib.sha256(message.encode()).hexdigest()

def string2encryption_key(string):
    return hashlib.sha256(string.encode()).digest()

def encrypt_message(message, key):
    iv = os.urandom(16)
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return {'iv': iv.hex(), 'd': encrypted.hex()}

def decrypt_message(encrypted_data, iv, key):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(bytes.fromhex(iv)), backend=backend)
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(bytes.fromhex(encrypted_data)) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
    return decrypted.decode()

def random_bytes_string(length):
    return os.urandom(length).hex()
