import base64

from cryptography.fernet import Fernet

class TextEncryptor:
    def __init__(self, key):
        key_bytes = str(key).encode()
        key_bytes += b'\x00' * (32 - len(key_bytes))

        self.cipher_suite = Fernet(base64.urlsafe_b64encode(key_bytes))

    def encrypt(self, plaintext):
        plaintext_bytes = plaintext.encode('utf-8')
        encrypted_bytes = self.cipher_suite.encrypt(plaintext_bytes)
        return encrypted_bytes.decode('utf-8')

    def decrypt(self, ciphertext):
        ciphertext_bytes = ciphertext.encode('utf-8')
        decrypted_bytes = self.cipher_suite.decrypt(ciphertext_bytes)
        return decrypted_bytes.decode('utf-8')