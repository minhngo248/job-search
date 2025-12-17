// Create clients and set shared const values outside of the handler.

// Create a DocumentClient that represents the query to add an item
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand } from '@aws-sdk/lib-dynamodb';
import { Temporal } from '@js-temporal/polyfill';

// Get current time in a specific timezone (Paris for your Île-de-France jobs)
const now = Temporal.Now.zonedDateTimeISO('Europe/Paris');
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

    // Creates a new item, or replaces an old item with a new item
    // https://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/DynamoDB/DocumentClient.html#put-property
    var params = {
        TableName : tableName,
        Item: { job_title: job_title, company_name: company_name,
            link: link, source: source, year_of_experience: year_of_experience,
            published_date: published_date, description: description,
            salary_range: salary_range, created_at: now, updated_date: now }
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
