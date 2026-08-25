import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Document
from app.schemas import DOCUMENT_TYPES, DocumentCreate, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])

# Extensions acceptees pour l'upload : documents administratifs et photos de chantier usuels.
EXTENSIONS_AUTORISEES = {
    ".pdf", ".jpg", ".jpeg", ".png", ".heic", ".heif",
    ".doc", ".docx", ".xls", ".xlsx", ".odt", ".txt",
}


def _uploads_root() -> Path:
    root = Path(settings.uploads_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


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
    """Enregistre un document sous forme de lien externe (ex: Google Drive)."""
    document = Document(artisan_id=artisan.id, **payload.model_dump())
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def uploader_document(
    file: UploadFile,
    nom: str | None = Form(None),
    type: str = Form("autre"),
    client_id: int | None = Form(None),
    chantier_id: int | None = Form(None),
    devis_id: int | None = Form(None),
    facture_id: int | None = Form(None),
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Uploade reellement un fichier et le stocke sur disque (pas de faux lien)."""
    if type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"type doit etre l'un de : {sorted(DOCUMENT_TYPES)}")

    extension = Path(file.filename or "").suffix.lower()
    if extension not in EXTENSIONS_AUTORISEES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension non autorisee. Formats acceptes : {sorted(EXTENSIONS_AUTORISEES)}",
        )

    max_bytes = settings.max_upload_mo * 1024 * 1024
    contenu = await file.read()
    if len(contenu) > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Fichier trop volumineux (max {settings.max_upload_mo} Mo)")
    if len(contenu) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide")

    artisan_dir = _uploads_root() / str(artisan.id)
    artisan_dir.mkdir(parents=True, exist_ok=True)
    nom_disque = f"{uuid.uuid4().hex}{extension}"
    chemin = artisan_dir / nom_disque
    chemin.write_bytes(contenu)

    document = Document(
        artisan_id=artisan.id,
        client_id=client_id,
        chantier_id=chantier_id,
        devis_id=devis_id,
        facture_id=facture_id,
        nom=nom or file.filename or nom_disque,
        type=type,
        chemin_fichier=str(chemin),
        nom_original=file.filename,
        taille_octets=len(contenu),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/{document_id}/fichier")
def telecharger_document(
    document_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    document = db.query(Document).filter(Document.id == document_id, Document.artisan_id == artisan.id).first()
    if document is None or not document.chemin_fichier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier introuvable")
    chemin = Path(document.chemin_fichier)
    if not chemin.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier introuvable")
    return FileResponse(
        path=chemin,
        filename=document.nom_original or document.nom,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_document(
    document_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    document = db.query(Document).filter(Document.id == document_id, Document.artisan_id == artisan.id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable")
    if document.chemin_fichier:
        chemin = Path(document.chemin_fichier)
        if chemin.is_file():
            chemin.unlink()
    db.delete(document)
    db.commit()
