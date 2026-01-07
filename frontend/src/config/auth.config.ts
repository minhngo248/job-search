import type { UserManagerSettings } from 'oidc-client-ts';

function getRequiredEnvVar(name: string): string {
  const value = import.meta.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export const cognitoAuthConfig: UserManagerSettings = {
  authority: getRequiredEnvVar('VITE_COGNITO_AUTHORITY'),
  client_id: getRequiredEnvVar('VITE_COGNITO_CLIENT_ID'),
  redirect_uri: getRequiredEnvVar('VITE_COGNITO_REDIRECT_URI'),
  response_type: 'code',
  scope: import.meta.env.VITE_COGNITO_SCOPE ?? 'openid email profile',
  automaticSilentRenew: true,
  loadUserInfo: true,
};

export const COGNITO_LOGOUT_DOMAIN = getRequiredEnvVar('VITE_COGNITO_DOMAIN');
export const COGNITO_LOGOUT_URI = getRequiredEnvVar('VITE_COGNITO_LOGOUT_URI');
