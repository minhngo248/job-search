#!/usr/bin/env ts-node
/**
 * Script to set up CloudWatch Log Insights queries for monitoring.
 * 
 * This script creates predefined queries for common monitoring scenarios
 * in the Regulatory Jobs application.
 */

import * as AWS from 'aws-sdk';
import { CloudWatchLogs } from 'aws-sdk';

interface QueryDefinition {
  name: string;
  queryString: string;
  logGroups: string[];
}

class LogInsightsSetup {
  private logsClient: CloudWatchLogs;
  private region: string;

  constructor(region: string = 'eu-west-3') {
    this.region = region;
    AWS.config.update({ region });
    this.logsClient = new AWS.CloudWatchLogs();
  }

  /**
   * Create a CloudWatch Log Insights query.
   */
  async createQuery(name: string, queryString: string, logGroups: string[]): Promise<string> {
    try {
      const response = await this.logsClient.putQueryDefinition({
        name,
        queryString,
        logGroupNames: logGroups,
      }).promise();

      console.log(`✅ Created query: ${name} (ID: ${response.queryDefinitionId})`);
      return response.queryDefinitionId || '';
    } catch (error: any) {
      console.error(`❌ Failed to create query ${name}: ${error.message}`);
      return '';
    }
  }

  /**
   * Set up queries for API Lambda monitoring.
   */
  async setupApiQueries(apiLogGroup: string): Promise<void> {
    console.log('🔍 Setting up API Lambda monitoring queries...');

    const queries: QueryDefinition[] = [
      {
        name: 'API Errors - Last 24 Hours',
        queryString: `
fields @timestamp, @message, request_id, error_type, error_message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
        `.trim(),
        logGroups: [apiLogGroup],
      },
      {
        name: 'API Performance - Slow Requests',
        queryString: `
fields @timestamp, @message, request_id, duration_ms, status_code
| filter @message like /API request completed/
| filter duration_ms > 5000
| sort duration_ms desc
| limit 50
        `.trim(),
        logGroups: [apiLogGroup],
      },
      {
        name: 'API Request Volume by Hour',
        queryString: `
fields @timestamp, http_method, resource_path, status_code
| filter @message like /API request started/
| stats count() by bin(5m)
        `.trim(),
        logGroups: [apiLogGroup],
      },
      {
        name: 'API Error Rate Analysis',
        queryString: `
fields @timestamp, status_code
| filter @message like /API request completed/
| stats count() as total_requests, 
        count(status_code >= 400) as error_requests
| eval error_rate = (error_requests / total_requests) * 100
        `.trim(),
        logGroups: [apiLogGroup],
      },
    ];

    for (const query of queries) {
      await this.createQuery(query.name, query.queryString, query.logGroups);
    }
  }

  /**
   * Set up queries for Scraper Lambda monitoring.
   */
  async setupScraperQueries(scraperLogGroup: string): Promise<void> {
    console.log('🔍 Setting up Scraper Lambda monitoring queries...');

    const queries: QueryDefinition[] = [
      {
        name: 'Scraper Execution Summary',
        queryString: `
fields @timestamp, @message, jobs_scraped, jobs_processed, execution_duration_seconds
| filter @message like /Job scraper Lambda function completed/
| sort @timestamp desc
| limit 20
        `.trim(),
        logGroups: [scraperLogGroup],
      },
      {
        name: 'Scraper Errors by Source',
        queryString: `
fields @timestamp, @message
| filter @message like /Error in .* scraper/
| parse @message /Error in (?<source>\\w+) scraper: (?<error>.*)/
| stats count() by source
| sort count desc
        `.trim(),
        logGroups: [scraperLogGroup],
      },
      {
        name: 'Scraper Performance Trends',
        queryString: `
fields @timestamp, execution_duration_seconds, jobs_scraped, jobs_processed
| filter @message like /Job scraper Lambda function completed/
| stats avg(execution_duration_seconds) as avg_duration,
        avg(jobs_scraped) as avg_scraped,
        avg(jobs_processed) as avg_processed
by bin(1d)
        `.trim(),
        logGroups: [scraperLogGroup],
      },
      {
        name: 'Critical Scraper Errors',
        queryString: `
fields @timestamp, @message, error_type, request_id
| filter @message like /Critical error in/
| sort @timestamp desc
| limit 50
        `.trim(),
        logGroups: [scraperLogGroup],
      },
    ];

    for (const query of queries) {
      await this.createQuery(query.name, query.queryString, query.logGroups);
    }
  }

  /**
   * Set up general monitoring queries.
   */
  async setupGeneralQueries(logGroups: string[]): Promise<void> {
    console.log('🔍 Setting up general monitoring queries...');

    const queries: QueryDefinition[] = [
      {
        name: 'Overall Error Summary - Last 24 Hours',
        queryString: `
fields @timestamp, @message, @logStream
| filter @message like /ERROR/
| stats count() by @logStream
| sort count desc
        `.trim(),
        logGroups,
      },
      {
        name: 'Memory Usage Analysis',
        queryString: `
fields @timestamp, @message, @maxMemoryUsed, @memorySize
| filter @type = "REPORT"
| stats avg(@maxMemoryUsed), max(@maxMemoryUsed), avg(@memorySize) by bin(1h)
        `.trim(),
        logGroups,
      },
      {
        name: 'Cold Start Analysis',
        queryString: `
fields @timestamp, @message, @duration, @initDuration
| filter @type = "REPORT"
| filter ispresent(@initDuration)
| stats count() as cold_starts, avg(@initDuration) as avg_init_duration by bin(1h)
        `.trim(),
        logGroups,
      },
    ];

    for (const query of queries) {
      await this.createQuery(query.name, query.queryString, query.logGroups);
    }
  }

  /**
   * Main setup function.
   */
  async setup(apiLogGroup: string, scraperLogGroup: string): Promise<void> {
    console.log('🚀 Setting up CloudWatch Log Insights queries...');

    try {
      // Set up API queries
      await this.setupApiQueries(apiLogGroup);

      // Set up Scraper queries
      await this.setupScraperQueries(scraperLogGroup);

      // Set up general queries
      await this.setupGeneralQueries([apiLogGroup, scraperLogGroup]);

      console.log('\n✅ CloudWatch Log Insights queries setup completed!');
      console.log(`\nYou can access the queries in the AWS Console:`);
      console.log(`https://${this.region}.console.aws.amazon.com/cloudwatch/home?region=${this.region}#logsV2:logs-insights`);
    } catch (error: any) {
      console.error(`❌ Setup failed: ${error.message}`);
      throw error;
    }
  }
}

/**
 * Main entry point.
 */
async function main(): Promise<number> {
  const args = process.argv.slice(2);

  // Parse command line arguments
  let region = 'eu-west-3';
  let apiLogGroup = '/aws/lambda/RegulatoryJobsStack-ApiLambda';
  let scraperLogGroup = '/aws/lambda/RegulatoryJobsStack-ScraperLambda';

  for (let i = 0; i < args.length; i += 2) {
    const flag = args[i];
    const value = args[i + 1];

    switch (flag) {
      case '--region':
        region = value;
        break;
      case '--api-log-group':
        apiLogGroup = value;
        break;
      case '--scraper-log-group':
        scraperLogGroup = value;
        break;
      case '--help':
        console.log(`
Usage: ts-node setup-log-insights.ts [options]

Options:
  --region <region>              AWS region (default: eu-west-3)
  --api-log-group <name>         API Lambda log group name (default: /aws/lambda/RegulatoryJobsStack-ApiLambda)
  --scraper-log-group <name>     Scraper Lambda log group name (default: /aws/lambda/RegulatoryJobsStack-ScraperLambda)
  --help                         Show this help message
        `);
        process.exit(0);
    }
  }

  try {
    const setup = new LogInsightsSetup(region);
    await setup.setup(apiLogGroup, scraperLogGroup);
    return 0;
  } catch (error: any) {
    console.error(`❌ Setup failed: ${error.message}`);
    return 1;
  }
}

if (require.main === module) {
  main()
    .then(process.exit)
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}