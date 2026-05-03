import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import api from '../api';
import { 
  Users, 
  UserPlus, 
  Shield, 
  Trash2, 
  Mail,
  MoreVertical,
  CheckCircle2
} from 'lucide-react';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';

const WorkspaceSettings = () => {
  const { currentWorkspace } = useWorkspace();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [inviteData, setInviteData] = useState({ user_id: '', role: 'agent' });
  const [isInviting, setIsInviting] = useState(false);

  useEffect(() => {
    if (currentWorkspace) {
      fetchMembers();
    }
  }, [currentWorkspace]);

  const fetchMembers = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/workspaces/${currentWorkspace.id}/members`);
      setMembers(response.data);
    } catch (err) {
      console.error('Failed to fetch members', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    setIsInviting(true);
    try {
      await api.post(`/workspaces/${currentWorkspace.id}/members`, {
        user_id: parseInt(inviteData.user_id),
        role: inviteData.role
      });
      setIsModalOpen(false);
      setInviteData({ user_id: '', role: 'agent' });
      fetchMembers();
    } catch (err) {
      alert('Failed to invite member. Make sure the User ID is valid.');
    } finally {
      setIsInviting(false);
    }
  };

  const handleRemove = async (userId) => {
    if (!confirm('Are you sure you want to remove this member?')) return;
    try {
      await api.delete(`/workspaces/${currentWorkspace.id}/members/${userId}`);
      fetchMembers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to remove member');
    }
  };

  if (!currentWorkspace) return <div className="p-8">Please select a workspace first.</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-end border-b pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Workspace Settings</h1>
          <p className="text-muted-foreground mt-1">Manage members and roles for {currentWorkspace.name}.</p>
        </div>
        <div className="flex gap-2 text-xs font-mono bg-muted px-3 py-1 rounded-md text-muted-foreground">
          <span>WS_ID:</span>
          <span className="text-foreground">{currentWorkspace.id}</span>
        </div>
      </div>

      <section className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Users size={20} className="text-primary" />
            Members
          </h2>
          <Button onClick={() => setIsModalOpen(true)} className="gap-2" variant="outline">
            <UserPlus size={18} />
            Add Member
          </Button>
        </div>

        <div className="bg-card border rounded-xl overflow-hidden divide-y backdrop-blur-sm">
          {loading ? (
            [...Array(3)].map((_, i) => (
              <div key={i} className="p-6 animate-pulse flex justify-between">
                <div className="h-4 bg-muted rounded w-1/3"></div>
                <div className="h-4 bg-muted rounded w-20"></div>
              </div>
            ))
          ) : members.map((member) => (
            <div key={member.user_id} className="p-6 flex items-center justify-between hover:bg-muted/30 transition-colors">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-secondary-foreground font-bold">
                  U{member.user_id}
                </div>
                <div>
                  <div className="font-semibold flex items-center gap-2">
                    User #{member.user_id}
                    {member.user_id === currentWorkspace.owner_id && (
                       <Badge variant="outline" className="text-[10px] py-0 border-primary/30 text-primary">Owner</Badge>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">Added via dashboard</div>
                </div>
              </div>
              
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-muted text-xs font-medium capitalize">
                  <Shield size={14} className="text-muted-foreground" />
                  {member.role}
                </div>
                
                <button 
                  onClick={() => handleRemove(member.user_id)}
                  className="text-muted-foreground hover:text-destructive transition-colors p-2"
                  disabled={member.user_id === currentWorkspace.owner_id}
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Invite New Member"
        footer={(
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button onClick={handleInvite} loading={isInviting} disabled={!inviteData.user_id}>
              Invite
            </Button>
          </>
        )}
      >
        <form onSubmit={handleInvite} className="space-y-4">
          <Input
            label="Target User ID"
            placeholder="e.g. 5"
            type="number"
            required
            value={inviteData.user_id}
            onChange={(e) => setInviteData({...inviteData, user_id: e.target.value})}
          />
          <div className="space-y-1">
            <label className="block text-sm font-medium text-foreground">Role</label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              value={inviteData.role}
              onChange={(e) => setInviteData({...inviteData, role: e.target.value})}
            >
              <option value="admin">Admin (Full Control)</option>
              <option value="agent">Agent (Handle Tickets)</option>
              <option value="viewer">Viewer (Read Only)</option>
            </select>
          </div>
          <div className="p-4 bg-muted/50 rounded-lg text-xs text-muted-foreground space-y-2">
            <p className="flex items-center gap-2 text-foreground font-medium">
              <CheckCircle2 size={14} className="text-green-500" />
              Role Permissions
            </p>
            <ul className="list-disc list-inside space-y-1 pl-1">
              <li><b>Admin:</b> Manage members, knowledge, and audit logs.</li>
              <li><b>Agent:</b> Respond to tickets and execute AI tools.</li>
              <li><b>Viewer:</b> Read-only access to tickets and conversation.</li>
            </ul>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default WorkspaceSettings;
