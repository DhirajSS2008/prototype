import { createContext, useContext, useState, useEffect } from 'react';
import { signIn, signUp, getMe } from '../api/client';

const AuthContext = createContext(null);

const ACCOUNTS_KEY = 'liqui_sense_accounts';
const ACTIVE_KEY = 'liqui_sense_active_account';

function getSavedAccounts() {
  try {
    return JSON.parse(localStorage.getItem(ACCOUNTS_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveAccounts(accounts) {
  localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
}

function getActiveAccount() {
  return localStorage.getItem(ACTIVE_KEY) || null;
}

function setActiveAccount(email) {
  if (email) {
    localStorage.setItem(ACTIVE_KEY, email);
  } else {
    localStorage.removeItem(ACTIVE_KEY);
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accounts, setAccounts] = useState(getSavedAccounts());

  // Restore session on mount
  useEffect(() => {
    const activeEmail = getActiveAccount();
    if (activeEmail) {
      const acct = accounts.find((a) => a.email === activeEmail);
      if (acct && acct.token) {
        setToken(acct.token);
        // Verify token
        getMe(acct.token)
          .then((res) => {
            setUser(res.data);
            setLoading(false);
          })
          .catch(() => {
            // Token expired, remove
            removeAccount(activeEmail);
            setLoading(false);
          });
        return;
      }
    }
    setLoading(false);
  }, []);

  const addAccount = (email, tokenStr, userData) => {
    const existing = accounts.filter((a) => a.email !== email);
    const newAccounts = [...existing, { email, token: tokenStr }];
    saveAccounts(newAccounts);
    setAccounts(newAccounts);
    setActiveAccount(email);
    setToken(tokenStr);
    setUser(userData);
  };

  const removeAccount = (email) => {
    const filtered = accounts.filter((a) => a.email !== email);
    saveAccounts(filtered);
    setAccounts(filtered);
    if (getActiveAccount() === email) {
      if (filtered.length > 0) {
        switchToAccount(filtered[0].email);
      } else {
        setActiveAccount(null);
        setToken(null);
        setUser(null);
      }
    }
  };

  const switchToAccount = async (email) => {
    const acct = accounts.find((a) => a.email === email);
    if (!acct) return;
    try {
      const res = await getMe(acct.token);
      setToken(acct.token);
      setUser(res.data);
      setActiveAccount(email);
    } catch {
      // Token expired
      removeAccount(email);
    }
  };

  const login = async (email, password) => {
    const res = await signIn({ email, password });
    addAccount(email, res.data.access_token, res.data.user);
    return res.data;
  };

  const register = async (email, password, confirmPassword) => {
    const res = await signUp({ email, password, confirm_password: confirmPassword });
    addAccount(email, res.data.access_token, res.data.user);
    return res.data;
  };

  const logout = () => {
    const activeEmail = getActiveAccount();
    if (activeEmail) {
      removeAccount(activeEmail);
    } else {
      setToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        accounts,
        login,
        register,
        logout,
        switchToAccount,
        addAccount,
        removeAccount,
        isAuthenticated: !!token && !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
