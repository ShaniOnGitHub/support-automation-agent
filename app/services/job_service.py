import uuid
import datetime
from typing import Callable, Any, Optional
from sqlalchemy.orm import Session
import traceback

from app.models.job import Job, JobStatus
from app.models.audit_log import AuditLog

def enqueue_job(db: Session, name: str, payload: dict, workspace_id: Optional[int] = None, actor_user_id: Optional[int] = None) -> Job:
    """
    📚 Method: Job Queueing
    Creates a pending Job record in the database.
    """
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        name=name,
        payload=payload,
        status=JobStatus.pending
    )
    db.add(job)
    
    # Optional audit log if context is provided
    if workspace_id and actor_user_id:
        audit = AuditLog(
            event_type="job_enqueued",
            entity_type="job",
            entity_id=0, # or could use string if entity_id supported it, but it's Integer
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            detail=f"Enqueued background job '{name}' with id {job_id}",
        )
        db.add(audit)
        
    db.commit()
    db.refresh(job)
    return job


def execute_job(session_factory, job_id: str, processor_func: Callable[[Session, dict], Any]):
    """
    📚 Method: Background Execution wrapper
    Opens its own DB session, updates the Job status, executes the logic safely,
    and records success or failure.
    """
    db: Session = session_factory()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or job.status != JobStatus.pending:
            return # Already picked up or doesn't exist

        # Mark as processing
        job.status = JobStatus.processing
        job.started_at = datetime.datetime.utcnow()
        db.commit()

        try:
            # Run the actual work
            processor_func(db, job.payload)
            
            # Mark as completed
            job.status = JobStatus.completed
            job.completed_at = datetime.datetime.utcnow()
            db.commit()
            
        except Exception as e:
            db.rollback()
            
            job = db.query(Job).filter(Job.id == job_id).first()
            job.status = JobStatus.failed
            job.completed_at = datetime.datetime.utcnow()
            job.error = str(e) + "\n" + traceback.format_exc()
            db.commit()
    finally:
        db.close()
