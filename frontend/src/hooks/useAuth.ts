import { useAuth as useOidcAuth } from 'react-oidc-context';

export const useAuth = () => {
  return useOidcAuth();
};
