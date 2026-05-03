import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';
import api from '../api';
import { 
  ArrowLeft, 
  Send, 
  User as UserIcon, 
  Bot, 
  Clock, 
  MoreVertical,
  ChevronDown
} from 'lucide-react';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import AIAssistantSidebar from '../components/tickets/AIAssistantSidebar';

const TicketDetailPage = () => {
  const { id } = useParams();
  const { currentWorkspace } = useWorkspace();
  const [ticket, setTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (currentWorkspace && id) {
      fetchTicketData();
    }
  }, [currentWorkspace, id]);

  const fetchTicketData = async () => {
    try {
      const [ticketRes, messagesRes] = await Promise.all([
        api.get(`/workspaces/${currentWorkspace.id}/tickets/${id}`),
        api.get(`/workspaces/${currentWorkspace.id}/tickets/${id}/messages/`)
      ]);
      setTicket(ticketRes.data);
      setMessages(messagesRes.data);
    } catch (err) {
      console.error('Failed to fetch ticket info', err);
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;
    
    setSending(true);
    try {
      await api.post(`/workspaces/${currentWorkspace.id}/tickets/${id}/messages/`, { body: newMessage });
      setNewMessage('');
      fetchTicketData();
    } catch (err) {
      alert('Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const handleUpdateStatus = async (status) => {
    try {
      await api.patch(`/workspaces/${currentWorkspace.id}/tickets/${id}`, { status });
      fetchTicketData();
    } catch (err) {
      alert('Failed to update status');
    }
  };

  if (loading) return <div className="p-8">Loading ticket details...</div>;
  if (!ticket) return <div className="p-8">Ticket not found.</div>;

  return (
    <div className="flex h-full overflow-hidden bg-background">
      {/* Main Content: Thread */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="px-6 py-4 border-b flex items-center justify-between bg-card z-10 sticky top-0">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate('/tickets')} className="text-muted-foreground hover:text-foreground">
              <ArrowLeft size={20} />
            </button>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <h1 className="text-lg font-bold truncate max-w-lg">{ticket.subject}</h1>
                <Badge variant={ticket.status === 'open' ? 'info' : 'success'}>{ticket.status}</Badge>
              </div>
              <p className="text-xs text-muted-foreground flex items-center gap-2">
                <span>#{ticket.id} opened {new Date(ticket.created_at).toLocaleDateString()}</span>
                <span>•</span>
                <span className="flex items-center gap-1 font-medium text-foreground">
                  <UserIcon size={12} />
                  {ticket.assigned_to_user_id || 'Unassigned'}
                </span>
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <select 
              className="bg-muted border-none rounded-md px-3 py-1 text-xs font-bold uppercase outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer"
              value={ticket.status}
              onChange={(e) => handleUpdateStatus(e.target.value)}
            >
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="bg-muted/30 border rounded-xl p-4 mb-8">
            <h3 className="text-sm font-semibold mb-2">Issue Description</h3>
            <p className="text-sm text-foreground/80 whitespace-pre-wrap">{ticket.description}</p>
          </div>

          {messages.map((msg, index) => (
            <div 
              key={msg.id} 
              className={`flex gap-3 max-w-[85%] ${msg.user_id ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.user_id ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'
              }`}>
                {msg.user_id ? <UserIcon size={16} /> : <Bot size={16} />}
              </div>
              <div className="space-y-1">
                <div className={`p-4 rounded-2xl text-sm shadow-sm ${
                  msg.user_id 
                    ? 'bg-primary text-primary-foreground rounded-tr-none' 
                    : 'bg-card border rounded-tl-none'
                }`}>
                  <p className="leading-relaxed">{msg.body}</p>
                </div>
                <div className={`text-[10px] text-muted-foreground px-1 ${msg.user_id ? 'text-right' : 'text-left'}`}>
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <footer className="p-4 border-t bg-card sticky bottom-0">
          <form onSubmit={handleSendMessage} className="relative">
            <textarea
              rows="1"
              placeholder="Type your response..."
              className="w-full bg-muted/50 border border-input rounded-2xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none transition-all focus:bg-background"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e);
                }
              }}
            />
            <button 
              type="submit"
              disabled={sending || !newMessage.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-all disabled:opacity-50 disabled:scale-95"
            >
              <Send size={18} />
            </button>
          </form>
        </footer>
      </div>

      {/* Sidebar: AI Co-pilot */}
      <AIAssistantSidebar ticket={ticket} onUpdate={fetchTicketData} />
    </div>
  );
};

export default TicketDetailPage;
