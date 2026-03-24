import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from app.config import get_settings


class EncryptionService:
    def __init__(self):
        settings = get_settings()
        key = settings.encryption_key.encode('utf-8')
        if len(key) < 16:
            key = key.ljust(16, b'\0')
        elif len(key) > 16:
            key = key[:16]
        self._key = key
    
    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return plaintext
        
        backend = default_backend()
        cipher = Cipher(algorithms.AES(self._key), modes.ECB(), backend=backend)
        encryptor = cipher.encryptor()
        
        padded = self._pad(plaintext.encode('utf-8'))
        encrypted = encryptor.update(padded) + encryptor.finalize()
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ciphertext
        
        backend = default_backend()
        cipher = Cipher(algorithms.AES(self._key), modes.ECB(), backend=backend)
        decryptor = cipher.decryptor()
        
        encrypted = base64.b64decode(ciphertext.encode('utf-8'))
        decrypted = decryptor.update(encrypted) + decryptor.finalize()
        
        return self._unpad(decrypted).decode('utf-8')
    
    def _pad(self, data: bytes) -> bytes:
        block_size = 16
        padding_len = block_size - (len(data) % block_size)
        return data + bytes([padding_len] * padding_len)
    
    def _unpad(self, data: bytes) -> bytes:
        padding_len = data[-1]
        return data[:-padding_len]


encryption_service = EncryptionService()
