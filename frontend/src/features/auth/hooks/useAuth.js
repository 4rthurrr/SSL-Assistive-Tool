import { useState, useCallback } from 'react';
import { authAPI } from '../../../utils/api';

export const useAuth = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const login = useCallback(async (form) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await authAPI.login(form);
      if (data.token) localStorage.setItem('token', data.token);
      if (data.user)  localStorage.setItem('user', JSON.stringify(data.user));
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('gameUser');
  }, []);

  return { login, logout, isLoading, error };
};
