from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.knowledge_base import Document, DocumentChunk
from app.services.ai_service import generate_embeddings
import re

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Splits text into chunks of roughly `chunk_size` characters with `overlap`.
    A simple approach: split by sentences and re-group.
    """
    # Split into sentences (simple regex)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Keep overlap: start next chunk with some previous context if possible
            # Or just start fresh for simplicity in this MVP
            current_chunk = sentence + " "
            
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def ingest_document(db: Session, workspace_id: int, filename: str, content: str) -> Document:
    """
    Ingets a document: stores metadata, chunks the text, 
    generates embeddings for each chunk, and saves to DB.
    """
    # Create document record
    doc = Document(filename=filename, workspace_id=workspace_id)
    db.add(doc)
    db.flush()
    
    chunks = chunk_text(content)
    for chunk_text_content in chunks:
        embedding = generate_embeddings(chunk_text_content, task_type="retrieval_document")
        if embedding:
            chunk = DocumentChunk(
                document_id=doc.id,
                text=chunk_text_content,
                embedding=embedding,
                workspace_id=workspace_id
            )
            db.add(chunk)
    
    db.commit()
    db.refresh(doc)
    return doc

def search_knowledge(db: Session, workspace_id: int, query: str, limit: int = 3) -> list[DocumentChunk]:
    """
    Performs vector similarity search for the given query.
    Uses the <=> operator for cosine distance.
    """
    query_embedding = generate_embeddings(query, task_type="retrieval_query")
    if not query_embedding:
        return []

    # Using SQLite fallback (typically in tests): fetch all chunks for workspace, and sort in memory
    if "sqlite" in str(db.bind.url):
        import math
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.workspace_id == workspace_id
        ).all()
        
        def cosine_distance(v1, v2):
            if v1 is None or v2 is None:
                return 1.0
            dot_prod = sum(a * b for a, b in zip(v1, v2))
            mag1 = math.sqrt(sum(a * a for a in v1))
            mag2 = math.sqrt(sum(b * b for b in v2))
            if mag1 == 0 or mag2 == 0:
                return 1.0
            return 1.0 - (dot_prod / (mag1 * mag2))
        
        chunks.sort(key=lambda c: cosine_distance(c.embedding, query_embedding))
        return chunks[:limit]

    # Using raw SQL for vector similarity search via pgvector
    # Order by <=> (cosine distance), lower is better
    # We filter by workspace_id to ensure isolation
    results = db.query(DocumentChunk).filter(
        DocumentChunk.workspace_id == workspace_id
    ).order_by(
        DocumentChunk.embedding.cosine_distance(query_embedding)
    ).limit(limit).all()
    
    return results

