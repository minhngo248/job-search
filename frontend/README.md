# Regulatory Jobs Frontend

A React TypeScript application for browsing medical device regulatory job postings in the Île-de-France region.

## Setup

### Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env.local
   ```

2. Update `.env.local` with your actual values:
   ```env
   VITE_API_GATEWAY_URL=https://your-api-gateway-url.amazonaws.com/prod
   VITE_API_KEY=your-api-key-here
   VITE_APP_NAME=Regulatory Jobs App
   VITE_APP_VERSION=1.0.0
   ```

### Required Environment Variables

- `VITE_API_GATEWAY_URL`: The API Gateway endpoint URL
- `VITE_API_KEY`: API key for authentication
- `VITE_APP_NAME`: Application name
- `VITE_APP_VERSION`: Application version

### Development

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:5173](http://localhost:5173) in your browser

### Build

Build for production:
```bash
npm run build
```

The built files will be in the `dist` directory.

### Configuration Validation

The application validates all required environment variables on startup. If any are missing or invalid, it will display an error message and prevent the application from starting.

### API Integration

The application uses a custom API client (`src/services/api.ts`) that:
- Authenticates requests using the X-Api-Key header
- Handles errors gracefully with custom error types
- Provides TypeScript interfaces for all API responses
- Supports job filtering by date, experience, and city

### Additional Scripts

```bash
# Type checking
npm run type-check

# Preview production build
npm run preview
```

### CORS Configuration

For local development, the Vite configuration includes a proxy setup to handle CORS issues when connecting to the API Gateway. The backend API Gateway is configured with CORS headers to allow frontend access.

### Deployment

The frontend is currently configured for local development only. Deployment strategy (S3 + CloudFront, Vercel, Netlify, etc.) will be determined later.