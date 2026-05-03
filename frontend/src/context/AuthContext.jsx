import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // In a real app, you might fetch the current user profile here
      // For now, we'll just assume the token is valid if it exists
      setUser({ email: localStorage.getItem('userEmail') });
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await api.post('/auth/login', formData);
    const { access_token } = response.data;
    
    localStorage.setItem('token', access_token);
    localStorage.setItem('userEmail', email);
    setUser({ email });
    return response.data;
  };

  const register = async (email, password, fullName) => {
    const response = await api.post('/auth/register', { email, password, full_name: fullName });
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userEmail');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
