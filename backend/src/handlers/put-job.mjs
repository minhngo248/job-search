// Create clients and set shared const values outside of the handler.

// Create a DocumentClient that represents the query to add an item
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand } from '@aws-sdk/lib-dynamodb';
import { Temporal } from '@js-temporal/polyfill';

const client = new DynamoDBClient({});
const ddbDocClient = DynamoDBDocumentClient.from(client);

// Get the DynamoDB table name from environment variables
const tableName = process.env.DYNAMODB_TABLE;

/**
 * A simple example includes a HTTP post method to add one item to a DynamoDB table.
 */
export const handler = async (event) => {
    if (event.httpMethod !== 'PUT') {
        throw new Error(`putJob only accepts PUT method, you tried: ${event.httpMethod} method.`);
    }
    // All log statements are written to CloudWatch
    console.info('received:', event);

    // Get id and name from the body of the request
    const body = JSON.parse(event.body);

    const job_title = body.job_title;
    const company_name = body.company_name;
    const link = body.link;
    const source = body.source;
    const year_of_experience = body.year_of_experience;
    const published_date = body.published_date;
    const description = body.description;
    const salary_range = body.salary_range;

    // Get current time in Paris timezone and convert to ISO string for DynamoDB
    const now = Temporal.Now.zonedDateTimeISO('Europe/Paris');
    const nowString = now.toInstant().toString(); // Converts to ISO 8601 string

    // Generate UUID for the job (DynamoDB requires explicit ID generation)
    const job_id = crypto.randomUUID();

    // Creates a new item, or replaces an old item with a new item
    // https://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/DynamoDB/DocumentClient.html#put-property
    var params = {
        TableName : tableName,
        Item: {
            id: job_id,
            job_title: job_title, 
            company_name: company_name,
            link: link, 
            source: source, 
            year_of_experience: year_of_experience,
            published_date: published_date, 
            description: description,
            salary_range: salary_range, 
            created_at: nowString, 
            updated_at: nowString 
        }
    };

    try {
        const data = await ddbDocClient.send(new PutCommand(params));
        console.log("Success - item added or updated", data);
    } catch (err) {
        console.log("Error", err.stack);
    }

    const response = {
        statusCode: 200,
        body: JSON.stringify(body)
    };

    // All log statements are written to CloudWatch
    console.info(`response from: ${event.path} statusCode: ${response.statusCode} body: ${response.body}`);
    return response;
};
