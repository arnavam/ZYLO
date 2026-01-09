// frontend/src/context/AuthContext.js
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);
    const [pdfHistory, setPdfHistory] = useState([]);

    // Set axios default header when token changes
    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            localStorage.setItem('token', token);
        } else {
            delete axios.defaults.headers.common['Authorization'];
            localStorage.removeItem('token');
        }
    }, [token]);

    const logout = useCallback(() => {
        setToken(null);
        setUser(null);
        setPdfHistory([]);
        localStorage.removeItem('token');
    }, []);

    const fetchHistory = useCallback(async () => {
        try {
            const response = await axios.get('/api/history');
            if (response.data.success) {
                setPdfHistory(response.data.history);
            }
        } catch (error) {
            console.error('Failed to fetch history:', error);
        }
    }, []);

    // Verify token and get user on mount
    useEffect(() => {
        const verifyToken = async () => {
            if (token) {
                try {
                    const response = await axios.get('/api/auth/me');
                    if (response.data.success) {
                        setUser(response.data.user);
                        fetchHistory();
                    } else {
                        logout();
                    }
                } catch (error) {
                    console.error('Token verification failed:', error);
                    logout();
                }
            }
            setLoading(false);
        };

        verifyToken();
    }, [token, fetchHistory, logout]);

    const login = async (email, password) => {
        try {
            const response = await axios.post('/api/auth/login', { email, password });
            if (response.data.success) {
                setToken(response.data.access_token);
                setUser(response.data.user);
                return { success: true };
            }
            return { success: false, error: response.data.error };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Login failed'
            };
        }
    };

    const register = async (name, email, password) => {
        try {
            const response = await axios.post('/api/auth/register', { name, email, password });
            if (response.data.success) {
                setToken(response.data.access_token);
                setUser(response.data.user);
                return { success: true };
            }
            return { success: false, error: response.data.error };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Registration failed'
            };
        }
    };

    const addToHistory = async (pdfData) => {
        try {
            const response = await axios.post('/api/history', pdfData);
            if (response.data.success) {
                fetchHistory(); // Refresh history
                return response.data.history_id;
            }
        } catch (error) {
            console.error('Failed to add to history:', error);
        }
        return null;
    };

    const deleteFromHistory = async (historyId) => {
        try {
            const response = await axios.delete(`/api/history/${historyId}`);
            if (response.data.success) {
                setPdfHistory(prev => prev.filter(item => item.id !== historyId));
                return true;
            }
        } catch (error) {
            console.error('Failed to delete from history:', error);
        }
        return false;
    };

    const value = {
        user,
        token,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        pdfHistory,
        fetchHistory,
        addToHistory,
        deleteFromHistory
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;