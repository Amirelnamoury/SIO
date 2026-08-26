import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Document
from app.schemas import DOCUMENT_TYPES, DocumentCreate, DocumentOut
from app.storage import get_storage

router = APIRouter(prefix="/documents", tags=["documents"])

# Extensions acceptees pour l'upload : documents administratifs et photos de chantier usuels.
EXTENSIONS_AUTORISEES = {
    ".pdf", ".jpg", ".jpeg", ".png", ".heic", ".heif",
    ".doc", ".docx", ".xls", ".xlsx", ".odt", ".txt",
}


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
    """Uploade reellement un fichier et le stocke (pas de faux lien). Passe
    par l'abstraction de stockage (app/storage.py) : disque local pour
    l'instant, migrable vers un stockage objet sans toucher ce router."""
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

    # Cle relative (jamais le nom fourni par l'utilisateur) : prefixee par
    # l'artisan pour qu'un meme uuid ne puisse jamais collisionner entre
    # deux entreprises, et pour rester lisible si on inspecte le stockage.
    nom_disque = f"{uuid.uuid4().hex}{extension}"
    cle = f"{artisan.id}/{nom_disque}"
    get_storage().save(cle, contenu)

    document = Document(
        artisan_id=artisan.id,
        client_id=client_id,
        chantier_id=chantier_id,
        devis_id=devis_id,
        facture_id=facture_id,
        nom=nom or file.filename or nom_disque,
        type=type,
        chemin_fichier=cle,
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
    """Jamais de fichier expose directement (pas de mount statique) : cet
    endpoint verifie la propriete avant de streamer le contenu, quel que
    soit le backend de stockage derriere get_storage()."""
    document = db.query(Document).filter(Document.id == document_id, Document.artisan_id == artisan.id).first()
    if document is None or not document.chemin_fichier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier introuvable")
    contenu = get_storage().read(document.chemin_fichier)
    if contenu is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier introuvable")
    nom_fichier = document.nom_original or document.nom
    type_mime = mimetypes.guess_type(nom_fichier)[0] or "application/octet-stream"
    return Response(
        content=contenu,
        media_type=type_mime,
        headers={"Content-Disposition": f'attachment; filename="{nom_fichier}"'},
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
        get_storage().delete(document.chemin_fichier)
    db.delete(document)
    db.commit()
