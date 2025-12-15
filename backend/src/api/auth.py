"""
Authentication and authorization utilities for the API.

This module provides Cognito JWT token validation and user authentication
for protecting API endpoints.
"""
import json
import logging
import os
from typing import Dict, Any, Optional
import base64
import hmac
import hashlib
from urllib.request import urlopen
from urllib.error import URLError

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)


class CognitoAuthValidator:
    """
    Validates Cognito JWT tokens for API authentication.
    
    Handles token validation, user extraction, and authorization
    for protected API endpoints.
    """
    
    def __init__(self):
        """Initialize the auth validator with Cognito configuration."""
        self.user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        self.client_id = os.environ.get('COGNITO_CLIENT_ID')
        self.region = os.environ.get('AWS_REGION', 'eu-west-3')
        
        # Cache for JWKs (JSON Web Keys)
        self._jwks_cache = None
        
        if not self.user_pool_id or not self.client_id:
            logger.warning("Cognito configuration not found in environment variables")
    
    def get_jwks(self) -> Dict[str, Any]:
        """
        Get JSON Web Keys from Cognito for token verification.
        
        Returns:
            Dictionary containing JWKs
            
        Raises:
            Exception: If JWKs cannot be retrieved
        """
        if self._jwks_cache:
            return self._jwks_cache
        
        try:
            jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
            with urlopen(jwks_url) as response:
                jwks = json.loads(response.read().decode('utf-8'))
                self._jwks_cache = jwks
                return jwks
        except URLError as e:
            logger.error(f"Failed to retrieve JWKs: {str(e)}")
            raise Exception("Unable to retrieve authentication keys")
    
    def extract_token_from_event(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Extract JWT token from API Gateway event.
        
        Args:
            event: API Gateway event dictionary
            
        Returns:
            JWT token string or None if not found
        """
        # Check Authorization header
        headers = event.get('headers', {})
        
        # Handle case-insensitive headers
        auth_header = None
        for key, value in headers.items():
            if key.lower() == 'authorization':
                auth_header = value
                break
        
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Check query parameters as fallback
        query_params = event.get('queryStringParameters') or {}
        if 'token' in query_params:
            return query_params['token']
        
        return None
    
    def decode_jwt_payload(self, token: str) -> Dict[str, Any]:
        """
        Decode JWT payload without verification (for inspection).
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dictionary
            
        Raises:
            ValueError: If token format is invalid
        """
        try:
            # Split token into parts
            parts = token.split('.')
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")
            
            # Decode payload (second part)
            payload_part = parts[1]
            
            # Add padding if needed for base64 decoding
            padding = 4 - (len(payload_part) % 4)
            if padding != 4:
                payload_part += '=' * padding
            
            payload_bytes = base64.urlsafe_b64decode(payload_part)
            payload = json.loads(payload_bytes.decode('utf-8'))
            
            return payload
            
        except Exception as e:
            raise ValueError(f"Failed to decode JWT payload: {str(e)}")
    
    def validate_token_basic(self, token: str) -> Dict[str, Any]:
        """
        Perform basic token validation without full cryptographic verification.
        
        This is a simplified validation for development/testing purposes.
        In production, full JWT signature verification should be implemented.
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary with validation result and user info
        """
        try:
            # Decode payload
            payload = self.decode_jwt_payload(token)
            
            # Check basic token structure
            required_fields = ['sub', 'aud', 'exp', 'iat']
            for field in required_fields:
                if field not in payload:
                    return {
                        'valid': False,
                        'error': f"Missing required field: {field}",
                        'user': None
                    }
            
            # Check if token is expired
            import time
            current_time = int(time.time())
            if payload['exp'] < current_time:
                return {
                    'valid': False,
                    'error': "Token has expired",
                    'user': None
                }
            
            # Check audience (client ID)
            if self.client_id and payload['aud'] != self.client_id:
                return {
                    'valid': False,
                    'error': "Invalid token audience",
                    'user': None
                }
            
            # Extract user information
            user_info = {
                'user_id': payload['sub'],
                'username': payload.get('cognito:username', payload['sub']),
                'email': payload.get('email'),
                'email_verified': payload.get('email_verified', False),
                'groups': payload.get('cognito:groups', [])
            }
            
            return {
                'valid': True,
                'error': None,
                'user': user_info
            }
            
        except ValueError as e:
            return {
                'valid': False,
                'error': str(e),
                'user': None
            }
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return {
                'valid': False,
                'error': "Token validation failed",
                'user': None
            }
    
    def validate_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate authentication for an API Gateway request.
        
        Args:
            event: API Gateway event dictionary
            
        Returns:
            Dictionary with validation result and user info
            
        Requirements: 6.2 - Cognito token validation
        """
        # Extract token from request
        token = self.extract_token_from_event(event)
        
        if not token:
            return {
                'valid': False,
                'error': "No authentication token provided",
                'user': None
            }
        
        # Validate token
        return self.validate_token_basic(token)
    
    def check_user_permissions(self, user_info: Dict[str, Any], required_permissions: list = None) -> bool:
        """
        Check if user has required permissions for the operation.
        
        Args:
            user_info: User information from validated token
            required_permissions: List of required permissions/groups
            
        Returns:
            True if user has required permissions, False otherwise
        """
        if not required_permissions:
            return True  # No specific permissions required
        
        user_groups = user_info.get('groups', [])
        
        # Check if user is in any of the required groups
        for permission in required_permissions:
            if permission in user_groups:
                return True
        
        return False


class MockAuthValidator(CognitoAuthValidator):
    """
    Mock authentication validator for development and testing.
    
    This validator bypasses actual Cognito validation and returns
    a mock user for development purposes.
    """
    
    def validate_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock validation that always returns a valid test user.
        
        Args:
            event: API Gateway event dictionary
            
        Returns:
            Dictionary with mock validation result
        """
        # Check if we're in development mode
        if os.environ.get('ENVIRONMENT') == 'development':
            return {
                'valid': True,
                'error': None,
                'user': {
                    'user_id': 'test-user-123',
                    'username': 'testuser',
                    'email': 'test@example.com',
                    'email_verified': True,
                    'groups': ['users']
                }
            }
        
        # Fall back to real validation in non-development environments
        return super().validate_request(event)