import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const WorkspaceContext = createContext();

export const WorkspaceProvider = ({ children }) => {
  const [workspaces, setWorkspaces] = useState([]);
  const [currentWorkspace, setCurrentWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchWorkspaces = async () => {
    try {
      const response = await api.get('/workspaces/');
      setWorkspaces(response.data);
      if (response.data.length > 0 && !currentWorkspace) {
        // Default to first workspace or stored preference
        const storedId = localStorage.getItem('lastWorkspaceId');
        const found = response.data.find(w => w.id === parseInt(storedId));
        setCurrentWorkspace(found || response.data[0]);
      }
    } catch (err) {
      console.error('Failed to fetch workspaces', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const selectWorkspace = (workspace) => {
    setCurrentWorkspace(workspace);
    localStorage.setItem('lastWorkspaceId', workspace.id);
  };

  const createWorkspace = async (name) => {
    const response = await api.post('/workspaces/', { name });
    await fetchWorkspaces();
    return response.data;
  };

  return (
    <WorkspaceContext.Provider value={{ 
      workspaces, 
      currentWorkspace, 
      selectWorkspace, 
      createWorkspace, 
      loading,
      refreshWorkspaces: fetchWorkspaces
    }}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => useContext(WorkspaceContext);
