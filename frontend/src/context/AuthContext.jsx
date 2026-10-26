import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI, setAccessToken, setRefreshToken, getRefreshToken } from '../services/api';
import { firebaseAuthService, isCustomFirebaseConfigured, getActiveFirebaseConfig } from '../services/firebase';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [firebaseConfig, setFirebaseConfig] = useState(getActiveFirebaseConfig());
  const [isFirebaseLive, setIsFirebaseLive] = useState(isCustomFirebaseConfigured());

  // Listen to Firebase auth state
  useEffect(() => {
    const unsubscribe = firebaseAuthService.onAuthStateChange((fbUser) => {
      setFirebaseUser(fbUser);
    });
    return () => unsubscribe();
  }, []);

  // Initialize session via httpOnly refresh token cookie on startup with localStorage fallback
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedRefreshToken = getRefreshToken();
        const res = await authAPI.refreshToken(storedRefreshToken);
        const { access_token, user: userData, refresh_token: newRToken } = res.data;
        setAccessToken(access_token);
        if (newRToken) setRefreshToken(newRToken);
        setToken(access_token);
        setUser(userData);
      } catch (err) {
        // No active session or refresh expired
        setAccessToken(null);
        setRefreshToken(null);
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, []);

  // Standard Login
  const login = async (email, password) => {
    const res = await authAPI.login(email, password);
    const { access_token, user: userData, refresh_token: rToken } = res.data;
    setAccessToken(access_token);
    if (rToken) setRefreshToken(rToken);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  // Standard Registration (role is assigned by server)
  const register = async (userData) => {
    const res = await authAPI.register(userData);
    const { access_token, user: newUser, refresh_token: rToken } = res.data;
    setAccessToken(access_token);
    if (rToken) setRefreshToken(rToken);
    setToken(access_token);
    setUser(newUser);
    return newUser;
  };

  // Firebase Google OAuth Sign In
  const loginWithGoogle = async () => {
    try {
      const { user: fbUser, idToken } = await firebaseAuthService.signInWithGoogle();
      
      const payload = {
        id_token: idToken,
        organization: 'Sri Murugan Bakery'
      };

      const res = await authAPI.firebaseLogin(payload);
      const { access_token, user: userData, refresh_token: rToken } = res.data;
      setAccessToken(access_token);
      if (rToken) setRefreshToken(rToken);
      setToken(access_token);
      setUser(userData);
      return userData;
    } catch (error) {
      console.error("Firebase Google Auth error:", error);
      throw error;
    }
  };

  // Firebase Email/Password Sign In
  const loginWithFirebaseEmail = async (email, password) => {
    try {
      const { user: fbUser, idToken } = await firebaseAuthService.signInWithEmail(email, password);
      
      const payload = {
        id_token: idToken,
        organization: 'Sri Murugan Bakery'
      };

      const res = await authAPI.firebaseLogin(payload);
      const { access_token, user: userData, refresh_token: rToken } = res.data;
      setAccessToken(access_token);
      if (rToken) setRefreshToken(rToken);
      setToken(access_token);
      setUser(userData);
      return userData;
    } catch (error) {
      console.error("Firebase Email Login error:", error);
      throw error;
    }
  };

  // Firebase Email/Password Sign Up
  const registerWithFirebaseEmail = async ({ email, password, fullName, organization }) => {
    try {
      const { user: fbUser, idToken } = await firebaseAuthService.signUpWithEmail(email, password, fullName);
      
      const payload = {
        id_token: idToken,
        organization: organization || 'Sri Murugan Bakery'
      };

      const res = await authAPI.firebaseLogin(payload);
      const { access_token, user: userData, refresh_token: rToken } = res.data;
      setAccessToken(access_token);
      if (rToken) setRefreshToken(rToken);
      setToken(access_token);
      setUser(userData);
      return userData;
    } catch (error) {
      console.error("Firebase Email Register error:", error);
      throw error;
    }
  };

  // Firebase Password Reset
  const resetPassword = async (email) => {
    return await firebaseAuthService.sendPasswordReset(email);
  };

  // Demo 1-Click Fast Login
  const demoLogin = async (persona = 'brand_manager') => {
    const res = await authAPI.demoLogin(persona);
    const { access_token, user: userData, refresh_token: rToken } = res.data;
    setAccessToken(access_token);
    if (rToken) setRefreshToken(rToken);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  // Logout from backend (clearing refresh cookie), Firebase, and in-memory state
  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (e) {
      // ignore
    }
    try {
      await firebaseAuthService.signOut();
    } catch (e) {
      // ignore
    }
    setAccessToken(null);
    setRefreshToken(null);
    setToken(null);
    setUser(null);
    setFirebaseUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      loading, 
      login, 
      register, 
      demoLogin, 
      loginWithGoogle,
      loginWithFirebaseEmail,
      registerWithFirebaseEmail,
      resetPassword,
      logout, 
      isAuthenticated: !!token,
      firebaseUser,
      firebaseConfig,
      isFirebaseLive
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
