import json
import logging
import os
from typing import Any, Dict
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from pydantic import ValidationError

from src.shared.models import UserModel

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create DynamoDB client outside handler for connection reuse
# Check if we're running locally with DynamoDB Local
dynamodb_endpoint = os.environ.get('DYNAMODB_ENDPOINT')
if dynamodb_endpoint:
    # Use local DynamoDB endpoint
    dynamodb = boto3.resource('dynamodb', endpoint_url=dynamodb_endpoint)
else:
    # Use AWS DynamoDB
    dynamodb = boto3.resource('dynamodb')

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Triggered after Cognito user confirmation.
    Automatically creates user record in DynamoDB.
    """
    table_name = os.environ.get('DYNAMODB_USER_TABLE')
    if not table_name:
        raise ValueError("DYNAMODB_USER_TABLE environment variable is required")
    table = dynamodb.Table(table_name)
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        user_attributes = event['request']['userAttributes']
        user_data = UserModel(
            id=user_attributes['sub'],
            email=user_attributes.get('email', ''),
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        table.put_item(Item=user_data.dict())
        logger.info(f"User {user_data.email} created successfully in DynamoDB.")
    except (KeyError, ValidationError) as e:
        logger.error(f"Error processing user data: {e}")
        # Re-raise the original error to signal failure
        raise e
    except ClientError as e:
        logger.error(f"AWS ClientError: {e.response['Error']['Message']}")
        raise e
    return event