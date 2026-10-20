import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { api, setToken } from './api';

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
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

  const value = useMemo(
    () => ({ user, isAdmin: user?.role === 'admin', login, logout }),
    [user, login, logout]
  );
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
