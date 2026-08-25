from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Document
from app.schemas import DocumentCreate, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def lister_documents(
    client_id: int | None = None,
    chantier_id: int | None = None,
    devis_id: int | None = None,
    facture_id: int | None = None,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    query = db.query(Document).filter(Document.artisan_id == artisan.id)
    if client_id:
        query = query.filter(Document.client_id == client_id)
    if chantier_id:
        query = query.filter(Document.chantier_id == chantier_id)
    if devis_id:
        query = query.filter(Document.devis_id == devis_id)
    if facture_id:
        query = query.filter(Document.facture_id == facture_id)
    return query.order_by(Document.created_at.desc()).all()


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def creer_document(
    payload: DocumentCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    document = Document(artisan_id=artisan.id, **payload.model_dump())
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_document(
    document_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    document = db.query(Document).filter(Document.id == document_id, Document.artisan_id == artisan.id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable")
    db.delete(document)
    db.commit()
