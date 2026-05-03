import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import api from '../api';
import { 
  History, 
  Search, 
  Activity, 
  User as UserIcon,
  Calendar,
  Filter
} from 'lucide-react';
import Badge from '../components/ui/Badge';

const AuditLogPage = () => {
  const { currentWorkspace } = useWorkspace();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    if (currentWorkspace) {
      fetchLogs();
    }
  }, [currentWorkspace, filter]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = filter ? { event_type: filter } : {};
      const response = await api.get(`/workspaces/${currentWorkspace.id}/audit-logs`, { params });
      setLogs(response.data);
    } catch (err) {
      console.error('Failed to fetch audit logs', err);
    } finally {
      setLoading(false);
    }
  };

  const getEventVariant = (type) => {
    if (type.includes('created')) return 'success';
    if (type.includes('updated') || type.includes('executed')) return 'info';
    if (type.includes('deleted')) return 'destructive';
    return 'outline';
  };

  if (!currentWorkspace) return <div className="p-8">Please select a workspace first.</div>;

  return (
    <div className="p-8 space-y-6 animate-in fade-in duration-500">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Audit Logs</h1>
        <p className="text-muted-foreground mt-1">Tracking all activity in {currentWorkspace.name}.</p>
      </div>

      <div className="flex flex-wrap items-center gap-4 bg-card p-4 rounded-lg border">
        <div className="flex-1 min-w-[200px] relative font-medium text-sm flex items-center gap-2">
          <Activity size={18} className="text-primary" />
          <span>Activity Stream</span>
        </div>
        
        <select 
          className="bg-background border rounded-md px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="">All Events</option>
          <option value="ticket_created">Ticket Created</option>
          <option value="message_created">Message Created</option>
          <option value="tool_executed">Tool Executed</option>
          <option value="suggestion_approved">Suggestion Approved</option>
        </select>
      </div>

      <div className="bg-card border rounded-lg overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/50 border-b">
              <tr>
                <th className="px-6 py-4 font-medium text-muted-foreground">Timestamp</th>
                <th className="px-6 py-4 font-medium text-muted-foreground">Action</th>
                <th className="px-6 py-4 font-medium text-muted-foreground">Entity</th>
                <th className="px-6 py-4 font-medium text-muted-foreground">Performed By</th>
                <th className="px-6 py-4 font-medium text-muted-foreground">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan="5" className="px-6 py-4"><div className="h-4 bg-muted rounded w-full"></div></td>
                  </tr>
                ))
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-20 text-center">
                    <History className="mx-auto text-muted-foreground mb-4 opacity-20" size={48} />
                    <p className="text-muted-foreground">No activities logged yet.</p>
                  </td>
                </tr>
              ) : logs.map((log) => (
                <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-6 py-4 text-muted-foreground font-mono text-[11px]">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <Badge variant={getEventVariant(log.event_type)}>
                      {log.event_type.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="font-semibold uppercase text-[10px] text-muted-foreground">{log.entity_type}</span>
                      <span>#{log.entity_id}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                       <UserIcon size={12} className="text-muted-foreground" />
                       <span>User {log.actor_user_id}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 max-w-xs">
                    <p className="truncate text-muted-foreground italic" title={log.detail}>
                      {log.detail || 'No extra details'}
                    </p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AuditLogPage;
