/**
 * Application configuration with validation
 */

interface AppConfig {
  apiGatewayUrl: string;
  apiKey: string;
  appName: string;
  appVersion: string;
}

/**
 * Validates that a required environment variable is present
 */
function getRequiredEnvVar(name: string): string {
  const value = import.meta.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

/**
 * Validates that a URL is properly formatted
 */
function validateUrl(url: string, name: string): string {
  try {
    new URL(url);
    return url;
  } catch {
    throw new Error(`Invalid URL format for ${name}: ${url}`);
  }
}

/**
 * Validates and loads application configuration
 */
function loadConfig(): AppConfig {
  try {
    const apiGatewayUrl = getRequiredEnvVar('VITE_API_GATEWAY_URL');
    const apiKey = getRequiredEnvVar('VITE_API_KEY');
    const appName = getRequiredEnvVar('VITE_APP_NAME');
    const appVersion = getRequiredEnvVar('VITE_APP_VERSION');

    return {
      apiGatewayUrl: validateUrl(apiGatewayUrl, 'VITE_API_GATEWAY_URL'),
      apiKey: apiKey.trim(),
      appName: appName.trim(),
      appVersion: appVersion.trim(),
    };
  } catch (error) {
    console.error('Configuration validation failed:', error);
    throw new Error(
      `Application configuration error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

// Load and validate configuration on module import
export const config = loadConfig();

// Export individual config values for convenience
export const { apiGatewayUrl, apiKey, appName, appVersion } = config;

// Export validation functions for testing
export { validateUrl, getRequiredEnvVar };