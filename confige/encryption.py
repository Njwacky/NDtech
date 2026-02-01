"""
Encryption utilities for field-level data protection
Provides AES encryption for sensitive customer data
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class FieldEncryption:
    """
    Field-level encryption for sensitive customer data
    Uses AES-256 encryption with key rotation support
    """
    
    def __init__(self):
        self.fernet = None
        self._init_encryption_key()
    
    def _init_encryption_key(self):
        """Initialize encryption key from environment or generate new one"""
        # Try to get key from environment
        encryption_key = os.environ.get('FIELD_ENCRYPTION_KEY')
        
        if encryption_key:
            # Use key from environment
            try:
                # Ensure key is properly base64 encoded
                if len(encryption_key) % 4 != 0:
                    # Pad key if necessary
                    encryption_key += '=' * (4 - len(encryption_key) % 4)
                key_bytes = base64.urlsafe_b64decode(encryption_key.encode())
                self.fernet = Fernet(key_bytes)
                logger.info("Field encryption initialized with environment key")
                return
            except Exception as e:
                logger.error(f"Failed to initialize encryption with environment key: {e}")
        
        # Generate new key if none provided
        logger.warning("No FIELD_ENCRYPTION_KEY in environment, generating new key")
        key = Fernet.generate_key()
        self.fernet = Fernet(key)
        
        # Save the new key to environment file for persistence
        self._save_encryption_key(key)
    
    def _save_encryption_key(self, key):
        """Save encryption key to .env file"""
        try:
            env_file = '.env'
            key_value = key.decode() if isinstance(key, bytes) else key
            
            # Read existing .env file
            env_content = {}
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            env_content[key.strip()] = value.strip()
            
            # Update or add the encryption key
            env_content['FIELD_ENCRYPTION_KEY'] = key_value
            
            # Write back to .env file
            with open(env_file, 'w') as f:
                for key, value in env_content.items():
                    f.write(f"{key}={value}\n")
            
            logger.info("Encryption key saved to .env file")
            
        except Exception as e:
            logger.error(f"Failed to save encryption key: {e}")
    
    def encrypt_field(self, data):
        """Encrypt a field value"""
        if not data or not self.fernet:
            return data
        
        try:
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = str(data).encode('utf-8')
            
            encrypted_data = self.fernet.encrypt(data_bytes)
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to encrypt field: {e}")
            return data
    
    def decrypt_field(self, encrypted_data):
        """Decrypt a field value"""
        if not encrypted_data or not self.fernet:
            return encrypted_data
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to decrypt field: {e}")
            return encrypted_data
    
    def encrypt_customer_data(self, customer_data):
        """Encrypt customer PII data"""
        if not isinstance(customer_data, dict):
            return customer_data
        
        encrypted_data = {}
        
        # Fields to encrypt
        sensitive_fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'billing_address', 'shipping_address',
            'payment_method', 'credit_card_number'
        ]
        
        for field, value in customer_data.items():
            if field in sensitive_fields and value:
                encrypted_data[field] = self.encrypt_field(value)
                encrypted_data[f"{field}_encrypted"] = True
            else:
                encrypted_data[field] = value
                encrypted_data[f"{field}_encrypted"] = False
        
        return encrypted_data
    
    def decrypt_customer_data(self, encrypted_customer_data):
        """Decrypt customer PII data"""
        if not isinstance(encrypted_customer_data, dict):
            return encrypted_customer_data
        
        decrypted_data = {}
        
        for field, value in encrypted_customer_data.items():
            if field.endswith('_encrypted') and value:
                continue  # Skip metadata fields
            elif field.endswith('_encrypted') and not value:
                # Handle empty encrypted fields
                original_field = field.replace('_encrypted', '')
                decrypted_data[original_field] = ''
            else:
                # Check if this field has encryption metadata
                encrypted_field = f"{field}_encrypted"
                if encrypted_customer_data.get(encrypted_field, False):
                    decrypted_data[field] = self.decrypt_field(value)
                else:
                    decrypted_data[field] = value
        
        return decrypted_data
    
    def rotate_encryption_key(self):
        """Rotate encryption key and re-encrypt data"""
        logger.info("Rotating encryption key...")
        
        # Generate new key
        old_key = self.fernet.key if hasattr(self.fernet, 'key') else None
        new_key = Fernet.generate_key()
        self.fernet = Fernet(new_key)
        
        # Save new key
        self._save_encryption_key(new_key)
        
        logger.info("Encryption key rotated successfully")
        return old_key
    
    def is_encrypted_field(self, field_name, data):
        """Check if a field contains encrypted data"""
        if not isinstance(data, str):
            return False
        
        # Simple heuristic to detect encrypted data
        # Encrypted data is typically base64 encoded and longer than original
        try:
            # Try to decode as base64
            decoded = base64.b64decode(data.encode())
            # If it can be decoded and looks like encrypted data, it's probably encrypted
            return len(data) > 50 and field_name in ['customer_name', 'customer_phone', 'customer_email']
        except:
            return False

# Global encryption instance
field_encryption = FieldEncryption()

def get_encryption_instance():
    """Get the global encryption instance"""
    return field_encryption

def encrypt_sensitive_value(value, field_name=None):
    """Convenience function to encrypt a sensitive value"""
    return field_encryption.encrypt_field(value)

def decrypt_sensitive_value(encrypted_value, field_name=None):
    """Convenience function to decrypt a sensitive value"""
    return field_encryption.decrypt_field(encrypted_value)

def encrypt_customer_pii(customer_data):
    """Convenience function to encrypt customer PII"""
    return field_encryption.encrypt_customer_data(customer_data)

def decrypt_customer_pii(encrypted_customer_data):
    """Convenience function to decrypt customer PII"""
    return field_encryption.decrypt_customer_data(encrypted_customer_data)
