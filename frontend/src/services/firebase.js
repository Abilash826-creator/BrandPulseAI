import { initializeApp, getApps, getApp } from 'firebase/app';
import { 
  getAuth, 
  GoogleAuthProvider, 
  signInWithPopup, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut as firebaseSignOut,
  sendPasswordResetEmail,
  onAuthStateChanged,
  updateProfile
} from 'firebase/auth';

// Storage key for custom user-provided Firebase configuration
const FIREBASE_CONFIG_KEY = 'brandpulse_firebase_config';

// Default configuration with fallback to environment variables
const getDefaultFirebaseConfig = () => {
  return {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "",
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "",
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "",
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "",
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "",
    appId: import.meta.env.VITE_FIREBASE_APP_ID || "",
    measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || ""
  };
};

// Retrieve active Firebase config (checking localStorage first, then env defaults)
export const getActiveFirebaseConfig = () => {
  try {
    const saved = localStorage.getItem(FIREBASE_CONFIG_KEY);
    if (saved) {
      return { ...getDefaultFirebaseConfig(), ...JSON.parse(saved) };
    }
  } catch (e) {
    console.warn("Could not read custom Firebase config:", e);
  }
  return getDefaultFirebaseConfig();
};

// Save custom Firebase config and reinitialize
export const saveActiveFirebaseConfig = (config) => {
  try {
    localStorage.setItem(FIREBASE_CONFIG_KEY, JSON.stringify(config));
    window.location.reload();
  } catch (e) {
    console.error("Failed to save Firebase config:", e);
  }
};

// Check if user has provided real Firebase credentials
export const isCustomFirebaseConfigured = () => {
  const cfg = getActiveFirebaseConfig();
  return cfg.apiKey && !cfg.apiKey.includes("AIzaSyDemoKey");
};

// Initialize Firebase App instance safely
let app = null;
let auth = null;
let googleProvider = null;

try {
  const config = getActiveFirebaseConfig();
  app = !getApps().length ? initializeApp(config) : getApp();
  auth = getAuth(app);
  googleProvider = new GoogleAuthProvider();
  googleProvider.setCustomParameters({ prompt: 'select_account' });
} catch (error) {
  console.warn("[Firebase] Initialization notice:", error.message);
}

export { app, auth, googleProvider };

// Firebase Authentication Methods
export const firebaseAuthService = {
  /**
   * Sign in with Google Popup
   */
  signInWithGoogle: async () => {
    if (!auth || !googleProvider) {
      throw new Error("Firebase Auth is not initialized. Please verify configuration.");
    }
    const result = await signInWithPopup(auth, googleProvider);
    const idToken = await result.user.getIdToken();
    return {
      user: result.user,
      idToken,
      credential: GoogleAuthProvider.credentialFromResult(result)
    };
  },

  /**
   * Sign in with Email and Password
   */
  signInWithEmail: async (email, password) => {
    if (!auth) throw new Error("Firebase Auth is not initialized.");
    const result = await signInWithEmailAndPassword(auth, email, password);
    const idToken = await result.user.getIdToken();
    return {
      user: result.user,
      idToken
    };
  },

  /**
   * Register with Email and Password
   */
  signUpWithEmail: async (email, password, displayName = "") => {
    if (!auth) throw new Error("Firebase Auth is not initialized.");
    const result = await createUserWithEmailAndPassword(auth, email, password);
    if (displayName && result.user) {
      await updateProfile(result.user, { displayName });
    }
    const idToken = await result.user.getIdToken();
    return {
      user: result.user,
      idToken
    };
  },

  /**
   * Send Password Reset Email
   */
  sendPasswordReset: async (email) => {
    if (!auth) throw new Error("Firebase Auth is not initialized.");
    await sendPasswordResetEmail(auth, email);
    return true;
  },

  /**
   * Sign out of Firebase
   */
  signOut: async () => {
    if (auth) {
      await firebaseSignOut(auth);
    }
  },

  /**
   * Listen for Firebase Auth state changes
   */
  onAuthStateChange: (callback) => {
    if (!auth) return () => {};
    return onAuthStateChanged(auth, callback);
  }
};
