import json

def cors_response(status_code, body, additional_headers=None):
    """
    Create a response with CORS headers
    
    Args:
        status_code: HTTP status code
        body: Response body (will be JSON encoded if not already a string)
        additional_headers: Optional dict of additional headers
    
    Returns:
        API Gateway response dict
    """
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key,x-api-key',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Merge additional headers if provided
    if additional_headers:
        headers.update(additional_headers)
    
    # Ensure body is a string
    if not isinstance(body, str):
        body = json.dumps(body)
    
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': body
    }