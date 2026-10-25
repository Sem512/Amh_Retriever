import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { api, setToken, setUnauthorizedHandler } from './api';

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const nav = useNavigate();
  const loc = useLocation();
  const locRef = useRef(loc);
  locRef.current = loc;

  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem('user')) || null;
    } catch {
      return null;
    }
  });

  const login = useCallback(async (username, password) => {
    const data = await api.login(username, password); // { access_token, role, username }
    setToken(data.access_token);
    const u = { username: data.username ?? username, role: data.role };
    sessionStorage.setItem('user', JSON.stringify(u));
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    sessionStorage.removeItem('user');
    setUser(null);
  }, []);

  // Expired or invalid token (401/403 on an authenticated call): clear the
  // session and go to the login page, remembering where the user was.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout();
      nav('/login', { replace: true, state: { from: locRef.current.pathname, expired: true } });
    });
    return () => setUnauthorizedHandler(null);
  }, [logout, nav]);

  const value = useMemo(
    () => ({ user, isAdmin: user?.role === 'admin', login, logout }),
    [user, login, logout]
  );
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
