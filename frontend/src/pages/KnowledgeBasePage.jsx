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
  const [isIngesting, setIsIngesting] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);
  const [filesQueue, setFilesQueue] = useState([]); // Array of { id, file, filename, content, status, errorMsg }

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

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFilesToQueue(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      addFilesToQueue(Array.from(e.target.files));
    }
  };

  const addFilesToQueue = (files) => {
    const newItems = files.map((file, index) => ({
      id: Date.now() + '-' + index + '-' + Math.random(),
      file,
      filename: file.name,
      content: '',
      status: 'pending',
      errorMsg: ''
    }));

    setFilesQueue(prev => [...prev, ...newItems]);

    newItems.forEach(item => {
      parseFileInQueue(item);
    });
  };

  const parseFileInQueue = async (item) => {
    setFilesQueue(prev => prev.map(f => f.id === item.id ? { ...f, status: 'parsing' } : f));
    
    const uploadData = new FormData();
    uploadData.append('file', item.file);

    try {
      const response = await api.post(`/workspaces/${currentWorkspace.id}/knowledge/parse-file`, uploadData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setFilesQueue(prev => prev.map(f => f.id === item.id ? {
        ...f,
        status: 'success',
        filename: response.data.filename || f.filename,
        content: response.data.content || ''
      } : f));
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.detail || 'Failed to parse file';
      setFilesQueue(prev => prev.map(f => f.id === item.id ? {
        ...f,
        status: 'error',
        errorMsg: errMsg
      } : f));
    }
  };

  const updateQueueFile = (id, fields) => {
    setFilesQueue(prev => prev.map(f => f.id === id ? { ...f, ...fields } : f));
  };

  const removeQueueFile = (id) => {
    setFilesQueue(prev => prev.filter(f => f.id !== id));
  };

  const handleIngest = async (e) => {
    e.preventDefault();
    const successfulFiles = filesQueue.filter(f => f.status === 'success' && f.content.trim() && f.filename.trim());
    if (successfulFiles.length === 0) {
      alert('No valid files ready to ingest.');
      return;
    }

    setIsIngesting(true);
    let successCount = 0;
    let failCount = 0;

    for (const item of successfulFiles) {
      try {
        await api.post(`/workspaces/${currentWorkspace.id}/knowledge/`, {
          filename: item.filename,
          content: item.content
        });
        successCount++;
      } catch (err) {
        console.error(`Failed to ingest ${item.filename}`, err);
        failCount++;
      }
    }

    setIsIngesting(false);
    
    if (failCount > 0) {
      alert(`Ingestion complete: ${successCount} documents ingested, ${failCount} failed.`);
    } else {
      setIsModalOpen(false);
      setFilesQueue([]);
    }
    fetchDocuments();
  };

  if (!currentWorkspace) return <div className="p-8">Please select a workspace first.</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Knowledge Base</h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-xl">
            Manage documents used by the AI to ground its responses.
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2 shrink-0">
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
          <div key={doc.id} className="bg-card border border-border/80 dark:border-border/30 rounded-2xl p-5 shadow-sm hover:shadow-lg hover:-translate-y-1 hover:border-primary/40 dark:hover:border-primary/50 transition-all duration-300 group overflow-hidden relative">
            <div className="flex items-start justify-between">
              <div className="p-2.5 bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 rounded-xl group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40 transition-colors">
                <FileText size={20} />
              </div>
              <button className="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-all duration-200 cursor-pointer">
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
        onClose={() => {
          setIsModalOpen(false);
          setFilesQueue([]);
        }}
        title="Ingest Knowledge Base Documents"
        footer={(
          <>
            <Button variant="ghost" onClick={() => {
              setIsModalOpen(false);
              setFilesQueue([]);
            }}>
              Cancel
            </Button>
            <Button 
              onClick={handleIngest} 
              loading={isIngesting} 
              disabled={filesQueue.filter(f => f.status === 'success').length === 0}
            >
              {isIngesting ? 'Ingesting...' : `Ingest ${filesQueue.filter(f => f.status === 'success').length} Document(s)`}
            </Button>
          </>
        )}
      >
        <div className="space-y-4">
          {/* Drag and Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              isDragActive 
                ? 'border-primary bg-primary/5 scale-[0.98]' 
                : 'border-muted-foreground/30 hover:border-primary/50 bg-muted/10'
            }`}
            onClick={() => document.getElementById('multi-file-input').click()}
          >
            <input
              id="multi-file-input"
              type="file"
              multiple
              accept=".pdf,.docx,.doc,.txt,.md,.csv,.json"
              className="hidden"
              onChange={handleFileSelect}
            />
            <Upload className="mx-auto text-muted-foreground/60 mb-3" size={32} />
            <p className="text-sm font-semibold text-foreground">Drag & drop files here, or click to select</p>
            <p className="text-xs text-muted-foreground mt-1">Accepts PDF, DOCX, TXT, MD, CSV, JSON</p>
          </div>

          {filesQueue.length > 0 && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-muted-foreground uppercase">Selected Files ({filesQueue.length})</span>
                <button
                  type="button"
                  onClick={() => document.getElementById('multi-file-input').click()}
                  className="text-xs text-primary font-semibold hover:underline flex items-center gap-1"
                >
                  <Plus size={14} /> Add More
                </button>
              </div>

              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
                {filesQueue.map((item) => (
                  <div key={item.id} className="border rounded-lg p-3 bg-card dark:bg-muted/10 space-y-2 relative group/item">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        {item.status === 'parsing' && <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary" />}
                        {item.status === 'success' && <div className="h-2 w-2 rounded-full bg-green-500" />}
                        {item.status === 'error' && <div className="h-2 w-2 rounded-full bg-red-500" />}
                        {item.status === 'pending' && <div className="h-2 w-2 rounded-full bg-yellow-500" />}
                        <span className="text-xs font-semibold truncate max-w-[200px] text-foreground">{item.file.name}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeQueueFile(item.id)}
                        className="text-muted-foreground hover:text-destructive p-1 rounded"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>

                    {item.status === 'error' && (
                      <p className="text-[11px] text-destructive italic">{item.errorMsg}</p>
                    )}

                    {item.status === 'success' && (
                      <div className="space-y-2">
                        <input
                          type="text"
                          value={item.filename}
                          onChange={(e) => updateQueueFile(item.id, { filename: e.target.value })}
                          placeholder="Filename"
                          className="w-full bg-muted border border-input rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary font-medium text-foreground"
                        />
                        <textarea
                          value={item.content}
                          onChange={(e) => updateQueueFile(item.id, { content: e.target.value })}
                          placeholder="Parsed text content..."
                          className="w-full h-20 bg-muted border border-input rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary resize-none font-mono text-foreground"
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs text-muted-foreground bg-blue-50 dark:bg-blue-950/20 p-3 rounded-md border border-blue-100 dark:border-blue-900/30 italic">
            Note: The system will automatically chunk these documents and generate semantic embeddings for RAG-assisted support.
          </p>
        </div>
      </Modal>
    </div>
  );
};

export default KnowledgeBasePage;
