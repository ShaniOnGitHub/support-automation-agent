import React, { useState, useEffect } from 'react';
import api from '../../api';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { 
  Sparkles, 
  RefreshCw, 
  Check, 
  X, 
  Play, 
  ExternalLink,
  ChevronDown,
  ChevronUp,
  BrainCircuit,
  Wrench,
  MessageSquare,
  BookOpen
} from 'lucide-react';

const AIAssistantSidebar = ({ ticket, onUpdate }) => {
  const [actions, setActions] = useState([]);
  const [loadingSuggestion, setLoadingSuggestion] = useState(false);
  const [isKBOpen, setIsKBOpen] = useState(false);
  const [executingActionId, setExecutingActionId] = useState(null);

  useEffect(() => {
    if (ticket?.id) {
      fetchActions();
    }
  }, [ticket?.id]);

  const fetchActions = async () => {
    try {
      const response = await api.get(`/workspaces/${ticket.workspace_id}/tickets/${ticket.id}/actions/`);
      setActions(response.data);
    } catch (err) {
      console.error('Failed to fetch tool actions', err);
    }
  };

  const handleRegenerate = async () => {
    setLoadingSuggestion(true);
    try {
      await api.post(`/workspaces/${ticket.workspace_id}/tickets/${ticket.id}/suggested-reply`);
      onUpdate();
    } catch (err) {
      alert('Failed to regenerate suggestion');
    } finally {
      setLoadingSuggestion(false);
    }
  };

  const handleApprove = async () => {
    try {
      await api.post(`/workspaces/${ticket.workspace_id}/tickets/${ticket.id}/approve-reply`);
      onUpdate();
    } catch (err) {
      alert('Failed to approve reply');
    }
  };

  const handleReject = async () => {
    try {
      await api.post(`/workspaces/${ticket.workspace_id}/tickets/${ticket.id}/reject-reply`);
      onUpdate();
    } catch (err) {
      alert('Failed to reject reply');
    }
  };

  const handleExecuteAction = async (actionId) => {
    setExecutingActionId(actionId);
    try {
      await api.post(`/workspaces/${ticket.workspace_id}/tickets/${ticket.id}/actions/${actionId}/execute`);
      fetchActions();
      // Usually execution might change the suggestion, so we could regenerate here too
    } catch (err) {
      alert('Failed to execute tool');
    } finally {
      setExecutingActionId(null);
    }
  };

  return (
    <div className="w-80 border-l bg-muted/10 h-full overflow-y-auto flex flex-col">
      <div className="p-4 border-b bg-background flex items-center gap-2">
        <Sparkles className="text-primary fill-primary/10" size={18} />
        <h2 className="font-bold">AI Assistant</h2>
      </div>

      <div className="p-4 space-y-6">
        {/* Section A: Triage */}
        <section className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <BrainCircuit size={14} />
            AI Triage Result
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20">
              {ticket.priority || 'Medium'}
            </Badge>
            <Badge variant="outline" className="bg-background">
              Technical Issue
            </Badge>
          </div>
        </section>

        {/* Section B: Suggested Reply */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <MessageSquare className="w-3.5 h-3.5" />
              Suggested Reply
            </div>
            <button 
              onClick={handleRegenerate}
              disabled={loadingSuggestion}
              className="text-primary hover:bg-primary/10 p-1 rounded transition-colors disabled:opacity-50"
              title="Regenerate suggestion"
            >
              <RefreshCw size={14} className={loadingSuggestion ? 'animate-spin' : ''} />
            </button>
          </div>

          <div className="bg-card border rounded-lg p-3 text-sm relative group overflow-hidden">
            {ticket.suggested_reply ? (
              <>
                <div className="whitespace-pre-wrap text-foreground/90 italic leading-relaxed">
                  "{ticket.suggested_reply}"
                </div>
                <div className="mt-4 flex gap-2">
                  <Button 
                    variant="primary" 
                    className="flex-1 py-1 h-8 text-xs gap-1"
                    onClick={handleApprove}
                    disabled={ticket.suggested_reply_status === 'approved'}
                  >
                    <Check size={14} />
                    Approve
                  </Button>
                  <Button 
                    variant="outline" 
                    className="flex-1 py-1 h-8 text-xs gap-1"
                    onClick={handleReject}
                    disabled={ticket.suggested_reply_status === 'rejected'}
                  >
                    <X size={14} />
                    Reject
                  </Button>
                </div>
                {ticket.suggested_reply_status && (
                  <div className={`mt-2 text-[10px] font-bold uppercase text-center py-0.5 rounded ${
                    ticket.suggested_reply_status === 'approved' ? 'bg-green-100 text-green-700' : 
                    ticket.suggested_reply_status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {ticket.suggested_reply_status}
                  </div>
                )}
              </>
            ) : (
              <div className="text-muted-foreground italic py-4 text-center">
                Click regenerate to get an AI suggestion.
              </div>
            )}
          </div>
        </section>

        {/* Section C: Tool Actions */}
        <section className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <Wrench size={14} />
            Proposed Actions
          </div>
          <div className="space-y-2">
            {actions.map((action) => (
              <div key={action.id} className="bg-background border rounded-lg p-3 text-sm space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="font-medium text-primary flex items-center gap-1">
                    <span className="capitalize">{action.tool_name.replace('_', ' ')}</span>
                  </div>
                  {!action.executed_at && (
                    <button 
                      onClick={() => handleExecuteAction(action.id)}
                      disabled={executingActionId === action.id}
                      className="text-primary hover:bg-primary/10 p-1.5 rounded-md border border-primary/20 transition-all flex items-center gap-1 h-7"
                    >
                      <Play size={10} fill="currentColor" />
                      <span className="text-[10px] font-bold">EXECUTE</span>
                    </button>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">Args: {JSON.stringify(action.tool_args)}</p>
                {action.executed_at && (
                  <div className="mt-2 p-2 bg-muted/50 rounded border border-dashed text-[11px] font-mono whitespace-pre-wrap break-all">
                    {action.tool_result}
                  </div>
                )}
              </div>
            ))}
            {actions.length === 0 && (
              <div className="text-[11px] text-muted-foreground italic py-2">
                AI hasn't proposed any tools yet.
              </div>
            )}
          </div>
          <p className="text-[10px] text-muted-foreground/60 italic leading-tight">
            Tool results will be contextually used to regenerate more accurate suggestions.
          </p>
        </section>

        {/* Section D: KB Context */}
        <section className="space-y-2">
          <button 
            onClick={() => setIsKBOpen(!isKBOpen)}
            className="flex items-center justify-between w-full text-xs font-semibold text-muted-foreground uppercase tracking-wider"
          >
            <div className="flex items-center gap-2">
              <BookOpen size={14} />
              Grounding Context
            </div>
            {isKBOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          
          {isKBOpen && (
            <div className="space-y-2 animate-in slide-in-from-top-2 duration-200">
              <div className="bg-blue-50/50 border border-blue-100 rounded p-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold text-blue-700">RefundPolicy.pdf</span>
                  <ExternalLink size={10} className="text-blue-400" />
                </div>
                <p className="text-[10px] text-blue-800/70 leading-relaxed italic">
                  "...refunds for orders over $50 require manager approval if requested after 14 days..."
                </p>
              </div>
              <div className="bg-blue-50/50 border border-blue-100 rounded p-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold text-blue-700">ShippingGuide.docx</span>
                  <ExternalLink size={10} className="text-blue-400" />
                </div>
                <p className="text-[10px] text-blue-800/70 leading-relaxed italic">
                  "...standard shipping takes 3-5 business days depending on the zone..."
                </p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default AIAssistantSidebar;
