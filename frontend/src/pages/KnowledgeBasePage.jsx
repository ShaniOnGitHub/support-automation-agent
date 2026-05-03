import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import api from '../api';
import { 
  Plus, 
  FileText, 
  Trash2, 
  Upload, 
  Database,
  Search,
  BookOpen
} from 'lucide-react';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';

const KnowledgeBasePage = () => {
  const { currentWorkspace } = useWorkspace();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ filename: '', content: '' });
  const [isIngesting, setIsIngesting] = useState(false);

  useEffect(() => {
    if (currentWorkspace) {
      fetchDocuments();
    }
  }, [currentWorkspace]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/workspaces/${currentWorkspace.id}/knowledge/`);
      setDocuments(response.data);
    } catch (err) {
      console.error('Failed to fetch documents', err);
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async (e) => {
    e.preventDefault();
    setIsIngesting(true);
    try {
      await api.post(`/workspaces/${currentWorkspace.id}/knowledge/`, formData);
      setIsModalOpen(false);
      setFormData({ filename: '', content: '' });
      fetchDocuments();
    } catch (err) {
      alert('Failed to ingest document');
    } finally {
      setIsIngesting(false);
    }
  };

  if (!currentWorkspace) return <div className="p-8">Please select a workspace first.</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Knowledge Base</h1>
          <p className="text-muted-foreground mt-1">Manage documents used by the AI to ground its responses.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2">
          <Plus size={18} />
          Ingest Document
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-muted/30 border rounded-xl animate-pulse" />
          ))
        ) : documents.length === 0 ? (
          <div className="col-span-full py-20 text-center border-2 border-dashed rounded-xl">
            <BookOpen className="mx-auto text-muted-foreground mb-4 opacity-20" size={48} />
            <p className="text-muted-foreground">No documents ingested yet.</p>
          </div>
        ) : documents.map((doc) => (
          <div key={doc.id} className="bg-card border rounded-xl p-5 shadow-sm hover:border-primary/50 transition-colors group">
            <div className="flex items-start justify-between">
              <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                <FileText size={20} />
              </div>
              <button className="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity">
                <Trash2 size={16} />
              </button>
            </div>
            <h3 className="font-semibold mt-4 mb-1 truncate">{doc.filename}</h3>
            <p className="text-xs text-muted-foreground mb-4">Ingested: {new Date(doc.created_at).toLocaleDateString()}</p>
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase text-primary bg-primary/5 px-2 py-1 rounded inline-block">
              <Database size={10} />
              Vectorized
            </div>
          </div>
        ))}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Ingest New Document"
        footer={(
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button onClick={handleIngest} loading={isIngesting} disabled={!formData.filename || !formData.content}>
              Ingest
            </Button>
          </>
        )}
      >
        <form onSubmit={handleIngest} className="space-y-4">
          <Input
            label="Filename (e.g. RefundPolicy.pdf)"
            placeholder="HelpCenter_Article_01.txt"
            required
            value={formData.filename}
            onChange={(e) => setFormData({...formData, filename: e.target.value})}
          />
          <div className="space-y-1">
            <label className="block text-sm font-medium text-foreground">Content</label>
            <textarea
              className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              placeholder="Paste document text here..."
              required
              value={formData.content}
              onChange={(e) => setFormData({...formData, content: e.target.value})}
            />
          </div>
          <p className="text-xs text-muted-foreground bg-blue-50 p-3 rounded-md border border-blue-100 italic">
            Note: The system will automatically chunk this text and generate semantic embeddings for RAG-assisted support.
          </p>
        </form>
      </Modal>
    </div>
  );
};

export default KnowledgeBasePage;
