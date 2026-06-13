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
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b pb-5">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Your Workspaces</h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-xl">
            Select a workspace to manage tickets and AI settings.
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2 shrink-0">
          <Plus size={18} />
          New Workspace
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workspaces.map((ws) => (
          <div 
            key={ws.id}
            onClick={() => handleSelectWorkspace(ws)}
            className="group relative bg-card border border-border/80 dark:border-border/30 rounded-2xl p-6 shadow-sm hover:shadow-xl hover:-translate-y-1 hover:border-primary/40 dark:hover:border-primary/50 transition-all duration-300 cursor-pointer overflow-hidden backdrop-blur-sm"
          >
            {/* Top decorative gradient glow */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary/30 via-primary to-primary/30 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            <div className="flex items-start justify-between mb-5">
              <div className="p-3 bg-primary/10 dark:bg-primary/20 rounded-xl text-primary group-hover:bg-primary group-hover:text-primary-foreground group-hover:shadow-[0_0_15px_rgba(59,130,246,0.4)] transition-all duration-300">
                <Building2 size={24} className="group-hover:scale-105 transition-transform" />
              </div>
              <ArrowRight className="text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" size={20} />
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
