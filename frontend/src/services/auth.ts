import { COGNITO_LOGOUT_DOMAIN, COGNITO_LOGOUT_URI } from '../config/auth.config';

const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID;

export const signOutRedirect = () => {
  if (!clientId || !COGNITO_LOGOUT_DOMAIN || !COGNITO_LOGOUT_URI) {
    console.error('Missing Cognito logout configuration');
    return;
  }

  const logoutUrl = new URL(`${COGNITO_LOGOUT_DOMAIN}/logout`);
  logoutUrl.searchParams.set('client_id', clientId);
  logoutUrl.searchParams.set('logout_uri', COGNITO_LOGOUT_URI);

  window.location.assign(logoutUrl.toString());
};
