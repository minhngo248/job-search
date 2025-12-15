#!/bin/bash
# Deployment script for frontend configuration
# This script deploys the CDK stack and configures the frontend environment

set -e

# Default values
STACK_NAME="RegulatoryJobsStack"
REGION="eu-west-3"
FRONTEND_DIR="../frontend"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --frontend-dir)
            FRONTEND_DIR="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --stack-name NAME    CDK stack name (default: RegulatoryJobsStack)"
            echo "  --region REGION      AWS region (default: eu-west-3)"
            echo "  --frontend-dir DIR   Frontend directory path (default: ../frontend)"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🚀 Starting deployment process..."
echo "   Stack Name: $STACK_NAME"
echo "   Region: $REGION"
echo "   Frontend Dir: $FRONTEND_DIR"
echo ""

# Check if we're in the infrastructure directory
if [[ ! -f "app.ts" ]]; then
    echo "❌ Error: This script must be run from the infrastructure directory"
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ Error: AWS CDK is not installed"
    echo "   Please install CDK: npm install -g aws-cdk"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured"
    echo "   Please configure your AWS credentials"
    exit 1
fi

echo "📦 Deploying CDK stack..."
cdk deploy --require-approval never

if [[ $? -ne 0 ]]; then
    echo "❌ CDK deployment failed"
    exit 1
fi

echo ""
echo "⚙️  Configuring frontend environment..."
npm run deploy-frontend-config -- \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --frontend-dir "$FRONTEND_DIR"

if [[ $? -ne 0 ]]; then
    echo "❌ Frontend configuration failed"
    exit 1
fi

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Navigate to the frontend directory: cd $FRONTEND_DIR"
echo "2. Install dependencies: npm install"
echo "3. Start development server: npm run dev"
echo "4. Build for production: npm run build"