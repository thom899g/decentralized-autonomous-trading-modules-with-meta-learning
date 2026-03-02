"""
Firebase configuration and initialization.
Handles Firestore connection for decentralized state management.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FirebaseConfig:
    """Configuration for Firebase connection"""
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    token_uri: str = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url: str = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url: str = "https://www.googleapis.com/robot/v1/metadata/x509/"


class FirebaseManager:
    """Singleton manager for Firebase Firestore connections"""
    
    _instance = None
    _db: Optional[Client] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, config_path: Optional[str] = None, config_dict: Optional[Dict[str, Any]] = None) -> Client:
        """
        Initialize Firebase connection with multiple fallback strategies
        
        Args:
            config_path: Path to service account JSON file
            config_dict: Dictionary containing Firebase configuration
            
        Returns:
            Firestore client instance
            
        Raises:
            ValueError: If no valid configuration is provided
            RuntimeError: If Firebase initialization fails
        """
        if cls._initialized and cls._db:
            logger.info("Firebase already initialized")
            return cls._db
        
        creds = None
        
        # Strategy 1: Check environment variable for service account
        if not creds and "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            try:
                creds = credentials.Certificate(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
                logger.info("Loaded credentials from environment variable")
            except Exception as e:
                logger.warning(f"Failed to load credentials from env: {e}")
        
        # Strategy 2: Load from provided config path
        if not creds and config_path and os.path.exists(config_path):
            try:
                creds = credentials.Certificate(config_path)
                logger.info(f"Loaded credentials from file: {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load credentials from file: {e}")
        
        # Strategy 3: Load from config dictionary
        if not creds and config_dict:
            try:
                creds = credentials.Certificate(config_dict)
                logger.info("Loaded credentials from dictionary")
            except Exception as e:
                logger.warning(f"Failed to load credentials from dict: {e}")
        
        # Strategy 4: Attempt application default credentials
        if not creds:
            try:
                creds = credentials.ApplicationDefault()
                logger.info("Using application default credentials")
            except Exception as e:
                logger.warning(f"Failed to use default credentials: {e}")
        
        if not creds:
            raise ValueError(
                "No valid Firebase configuration found. Please provide one of: "
                "1. GOOGLE_APPLICATION_CREDENTIALS environment variable\n"
                "2. config_path to service account JSON\n"
                "3. config_dict with service account data"
            )
        
        try:
            # Initialize Firebase app if not already initialized
            if not firebase_admin._apps:
                firebase_admin.initialize_app(creds)
            
            # Get Firestore client
            cls._db = firestore.client()
            cls._initialized = True
            
            logger.info("Firebase Firestore initialized successfully")
            return cls._db
            
        except Exception as e:
            error_msg = f"Failed to initialize Firebase: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    @classmethod
    def get_db(cls) -> Client:
        """Get Firestore database client"""
        if not cls._initialized or cls._db is None:
            logger.warning("Firebase not initialized. Attempting to initialize with defaults...")
            cls.initialize()
        return cls._db
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if Firebase is initialized"""
        return cls._initialized and cls._db is not None


# Global Firestore client accessor
def get_firestore_client() -> Client:
    """Get the Firestore client instance"""
    return FirebaseManager.get_db()