import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';
import api from '../api';
import { 
  Search, 
  Filter, 
  Plus, 
  MessageSquare, 
  Clock, 
  User as UserIcon,
  ChevronUp,
  ChevronDown
} from 'lucide-react';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

const TicketListPage = () => {
  const { currentWorkspace } = useWorkspace();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ status: '', priority: '' });
  const navigate = useNavigate();

  useEffect(() => {
    if (currentWorkspace) {
      fetchTickets();
    }
  }, [currentWorkspace, filter]);

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/workspaces/${currentWorkspace.id}/tickets/`);
      let data = response.data;
      
      // Client-side filtering as an example (backend might support this too)
      if (filter.status) data = data.filter(t => t.status === filter.status);
      if (filter.priority) data = data.filter(t => t.priority === filter.priority);
      
      setTickets(data);
    } catch (err) {
      console.error('Failed to fetch tickets', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusVariant = (status) => {
    switch (status) {
      case 'open': return 'info';
      case 'in_progress': return 'warning';
      case 'resolved': return 'success';
      case 'closed': return 'secondary';
      default: return 'outline';
    }
  };

  const getPriorityVariant = (priority) => {
    switch (priority) {
      case 'urgent': return 'destructive';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'secondary';
      default: return 'outline';
    }
  };

  if (!currentWorkspace) return <div className="p-8">Please select a workspace first.</div>;

  return (
    <div className="p-8 space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Tickets</h1>
          <p className="text-muted-foreground">Manage and respond to customer requests in {currentWorkspace.name}.</p>
        </div>
        <Button onClick={() => navigate('/tickets/new')} className="gap-2 self-start">
          <Plus size={18} />
          New Ticket
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-4 bg-card p-4 rounded-lg border">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
          <input 
            type="text" 
            placeholder="Search tickets..." 
            className="w-full pl-10 pr-4 py-2 bg-background border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        
        <select 
          className="bg-background border rounded-md px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
          value={filter.status}
          onChange={(e) => setFilter({...filter, status: e.target.value})}
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>

        <select 
          className="bg-background border rounded-md px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
          value={filter.priority}
          onChange={(e) => setFilter({...filter, priority: e.target.value})}
        >
          <option value="">All Priorities</option>
          <option value="urgent">Urgent</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="bg-card border rounded-lg overflow-hidden shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted/50 border-b">
            <tr>
              <th className="px-6 py-4 font-medium text-muted-foreground w-1/4">Ticket</th>
              <th className="px-6 py-4 font-medium text-muted-foreground">Status</th>
              <th className="px-6 py-4 font-medium text-muted-foreground">Priority</th>
              <th className="px-6 py-4 font-medium text-muted-foreground">Assigned To</th>
              <th className="px-6 py-4 font-medium text-muted-foreground">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td className="px-6 py-4"><div className="h-4 bg-muted rounded w-3/4"></div></td>
                  <td className="px-6 py-4"><div className="h-4 bg-muted rounded w-20"></div></td>
                  <td className="px-6 py-4"><div className="h-4 bg-muted rounded w-20"></div></td>
                  <td className="px-6 py-4"><div className="h-4 bg-muted rounded w-24"></div></td>
                  <td className="px-6 py-4"><div className="h-4 bg-muted rounded w-20"></div></td>
                </tr>
              ))
            ) : tickets.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-6 py-20 text-center">
                  <MessageSquare className="mx-auto text-muted-foreground mb-4 opacity-20" size={48} />
                  <p className="text-muted-foreground">No tickets found.</p>
                </td>
              </tr>
            ) : tickets.map((ticket) => (
              <tr 
                key={ticket.id} 
                className="hover:bg-muted/30 transition-colors cursor-pointer"
                onClick={() => navigate(`/tickets/${ticket.id}`)}
              >
                <td className="px-6 py-4">
                  <div className="font-semibold text-foreground truncate max-w-xs">{ticket.subject}</div>
                  <div className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                    <span>#{ticket.id}</span>
                    <span>•</span>
                    <span className="truncate">{ticket.description?.substring(0, 40)}...</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <Badge variant={getStatusVariant(ticket.status)}>
                    {ticket.status.replace('_', ' ')}
                  </Badge>
                </td>
                <td className="px-6 py-4">
                  <Badge variant={getPriorityVariant(ticket.priority)}>
                    {ticket.priority}
                  </Badge>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center">
                      <UserIcon size={12} />
                    </div>
                    <span className="text-muted-foreground">
                      {ticket.assigned_to_user_id ? `User ${ticket.assigned_to_user_id}` : 'Unassigned'}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Clock size={14} />
                    {new Date(ticket.created_at).toLocaleDateString()}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TicketListPage;
