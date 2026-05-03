import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';
import api from '../api';
import { ArrowLeft, Send } from 'lucide-react';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';

const NewTicketPage = () => {
  const { currentWorkspace } = useWorkspace();
  const [formData, setFormData] = useState({
    subject: '',
    description: '',
    priority: 'medium',
    order_id: null
  });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.post(`/workspaces/${currentWorkspace.id}/tickets/`, formData);
      navigate(`/tickets/${response.data.id}`);
    } catch (err) {
      alert('Failed to create ticket');
    } finally {
      setLoading(false);
    }
  };

  if (!currentWorkspace) return <div className="p-8">Please select a workspace first.</div>;

  return (
    <div className="p-8 max-w-2xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <button 
        onClick={() => navigate('/tickets')}
        className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-4"
      >
        <ArrowLeft size={16} />
        Back to tickets
      </button>

      <div>
        <h1 className="text-2xl font-bold tracking-tight">Create New Ticket</h1>
        <p className="text-muted-foreground">Open a new support request for {currentWorkspace.name}.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-card border rounded-xl p-6 shadow-sm space-y-6">
        <Input
          label="Subject"
          placeholder="Issue with order #12345"
          required
          value={formData.subject}
          onChange={(e) => setFormData({...formData, subject: e.target.value})}
        />

        <div className="space-y-1">
          <label className="block text-sm font-medium text-foreground">Description</label>
          <textarea
            className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Explain the customer's issue in detail..."
            required
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="block text-sm font-medium text-foreground">Priority</label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              value={formData.priority}
              onChange={(e) => setFormData({...formData, priority: e.target.value})}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
          
          <Input
            label="Order ID (Optional)"
            placeholder="555"
            type="number"
            value={formData.order_id || ''}
            onChange={(e) => setFormData({...formData, order_id: e.target.value ? parseInt(e.target.value) : null})}
          />
        </div>

        <div className="pt-4 border-t flex justify-end gap-3">
          <Button variant="ghost" onClick={() => navigate('/tickets')}>Cancel</Button>
          <Button type="submit" loading={loading} className="gap-2">
            <Send size={16} />
            Create Ticket
          </Button>
        </div>
      </form>
    </div>
  );
};

export default NewTicketPage;
