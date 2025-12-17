import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, DeleteCommand } from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({endpoint: process.env.DYNAMODB_ENDPOINT || undefined});
const ddbDocClient = DynamoDBDocumentClient.from(client);
const tableName = process.env.DYNAMODB_TABLE;

export const handler = async (event) => {
  if (event.httpMethod !== 'DELETE') {
    throw new Error(`deleteId only accept DELETE method, you tried: ${event.httpMethod}`);
  }
  
  console.info('received:', event);
  const id = event.pathParameters.id;
  
  const params = {
    TableName: tableName,
    Key: { id: id }
  };

  try {
    await ddbDocClient.send(new DeleteCommand(params));
  } catch (err) {
    console.log("Error", err);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Failed to delete item' })
    };
  }
 
  const response = {
    statusCode: 200,
    body: JSON.stringify({ message: 'Item deleted successfully' })
  };
 
  console.info(`response from: ${event.path} statusCode: ${response.statusCode} body: ${response.body}`);
  return response;
};