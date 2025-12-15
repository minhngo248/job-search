#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { RegulatoryJobsStack } from './lib/regulatory-jobs-stack';

const app = new cdk.App();

new RegulatoryJobsStack(app, 'RegulatoryJobsStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});