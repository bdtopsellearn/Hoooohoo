import { initializeApp } from "firebase/app";
import { getAnalytics, isSupported } from "firebase/analytics";
import { getDatabase } from "firebase/database";

// Your web app's Firebase configuration
export const firebaseConfig = {
  apiKey: "AIzaSyAIw4w6nMR440pZh-zw4GBsd0o0fUllgSo",
  authDomain: "bot-host-website-9f118.firebaseapp.com",
  databaseURL: "https://bot-host-website-9f118-default-rtdb.firebaseio.com",
  projectId: "bot-host-website-9f118",
  storageBucket: "bot-host-website-9f118.firebasestorage.app",
  messagingSenderId: "11293173080",
  appId: "1:11293173080:web:2a6dbf296e61378b03b12d",
  measurementId: "G-ZZGT8KMYWG"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);

// Initialize optional browser Analytics safely
let analyticsInstance: ReturnType<typeof getAnalytics> | null = null;
if (typeof window !== "undefined") {
  isSupported().then((supported) => {
    if (supported) {
      analyticsInstance = getAnalytics(app);
    }
  }).catch(() => {});
}

export const analytics = analyticsInstance;
export const rtdb = getDatabase(app);
