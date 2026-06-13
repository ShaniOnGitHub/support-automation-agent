from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import pypdf
import docx
import io

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.schemas.knowledge import KnowledgeIngest, DocumentResponse
from app.services import knowledge_service
from app.services.workspace_service import check_workspace_membership

router = APIRouter()

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def ingest_knowledge(
    workspace_id: int,
    ingest: KnowledgeIngest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Ingest a document into the workspace's knowledge base.
    Chunks the text and generates embeddings for semantic search.
    """
    # Verify membership (Admin/Agent)
    role = check_workspace_membership(db, current_user.id, workspace_id)
    if role == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot ingest knowledge")
        
    return knowledge_service.ingest_document(
        db, workspace_id, ingest.filename, ingest.content
    )

@router.get("/", response_model=List[DocumentResponse])
def list_knowledge(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List all documents in the workspace knowledge base."""
    check_workspace_membership(db, current_user.id, workspace_id)
    from app.models.knowledge_base import Document
    return db.query(Document).filter(Document.workspace_id == workspace_id).all()


@router.post("/parse-file")
async def parse_file(
    workspace_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Parse a PDF, DOCX, TXT, or MD file and return its content as text.
    """
    filename = file.filename
    content = ""
    
    # Check file extension
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    
    try:
        if ext == "pdf":
            # Read PDF
            pdf_bytes = await file.read()
            pdf_file = io.BytesIO(pdf_bytes)
            reader = pypdf.PdfReader(pdf_file)
            text_list = []
            for page in reader.pages:
                text_list.append(page.extract_text() or "")
            content = "\n".join(text_list)
        elif ext in ["docx", "doc"]:
            # Read DOCX
            docx_bytes = await file.read()
            docx_file = io.BytesIO(docx_bytes)
            doc = docx.Document(docx_file)
            text_list = []
            for para in doc.paragraphs:
                text_list.append(para.text)
            content = "\n".join(text_list)
        elif ext in ["txt", "md", "csv", "json"]:
            # Read standard text file
            text_bytes = await file.read()
            content = text_bytes.decode("utf-8", errors="ignore")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {ext}. Only PDF, DOCX, TXT, MD, CSV, and JSON are supported."
            )
            
        return {"filename": filename, "content": content}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse file: {str(e)}"
        )

