import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';
import { Plus, Building2, Ticket, Users, ArrowRight } from 'lucide-react';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';

const Dashboard = () => {
  const { workspaces, selectWorkspace, createWorkspace, loading } = useWorkspace();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const navigate = useNavigate();

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      const ws = await createWorkspace(newWorkspaceName);
      setIsModalOpen(false);
      setNewWorkspaceName('');
      handleSelectWorkspace(ws);
    } catch (err) {
      alert('Failed to create workspace');
    } finally {
      setIsCreating(false);
    }
  };

  const handleSelectWorkspace = (ws) => {
    selectWorkspace(ws);
    navigate('/tickets');
  };

  if (loading) return <div className="p-8">Loading workspaces...</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Your Workspaces</h1>
          <p className="text-muted-foreground mt-1">Select a workspace to manage tickets and AI settings.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2">
          <Plus size={18} />
          New Workspace
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workspaces.map((ws) => (
          <div 
            key={ws.id}
            onClick={() => handleSelectWorkspace(ws)}
            className="group relative bg-card border rounded-xl p-6 shadow-sm hover:shadow-md transition-all cursor-pointer border-transparent hover:border-primary/50"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-primary/10 rounded-lg text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                <Building2 size={24} />
              </div>
              <ArrowRight className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" size={20} />
            </div>
            
            <h3 className="text-xl font-bold mb-1">{ws.name}</h3>
            <p className="text-sm text-muted-foreground mb-6">ID: {ws.id}</p>
            
            <div className="flex gap-4 border-t pt-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Ticket size={14} />
                <span>Active</span>
              </div>
              <div className="flex items-center gap-1">
                <Users size={14} />
                <span>Members</span>
              </div>
            </div>
          </div>
        ))}

        {workspaces.length === 0 && (
          <div className="col-span-full py-20 text-center border-2 border-dashed rounded-xl">
            <Building2 className="mx-auto text-muted-foreground mb-4" size={48} />
            <h3 className="text-lg font-medium">No workspaces found</h3>
            <p className="text-muted-foreground mb-6">Create your first workspace to get started.</p>
            <Button onClick={() => setIsModalOpen(true)} variant="secondary">
              Create Workspace
            </Button>
          </div>
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New Workspace"
        footer={(
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateWorkspace} loading={isCreating} disabled={!newWorkspaceName}>
              Create
            </Button>
          </>
        )}
      >
        <form onSubmit={handleCreateWorkspace}>
          <Input
            label="Workspace Name"
            placeholder="Acme Corp Support"
            value={newWorkspaceName}
            onChange={(e) => setNewWorkspaceName(e.target.value)}
            required
            autoFocus
          />
          <p className="mt-4 text-xs text-muted-foreground">
            As the creator, you will automatically be assigned the Admin role for this workspace.
          </p>
        </form>
      </Modal>
    </div>
  );
};

export default Dashboard;
