import { createContext, useState, useEffect, useContext } from 'react';
import { auth, signOut } from '../firebase';
import { onAuthStateChanged } from 'firebase/auth';

const AnalysisContext = createContext(null);

export const AnalysisProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionId, setSessionId] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);

  useEffect(() => {
    // Listen for authentication state changes and persist sessions
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const logout = async () => {
    try {
      await signOut(auth);
      // Reset state on signout
      setUser(null);
      setSessionId(null);
      setAnalysisResults(null);
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  return (
    <AnalysisContext.Provider
      value={{
        user,
        setUser,
        loading,
        sessionId,
        setSessionId,
        analysisResults,
        setAnalysisResults,
        logout
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = () => {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error("useAnalysis must be used within an AnalysisProvider");
  }
  return context;
};
