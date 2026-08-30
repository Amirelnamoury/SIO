"""Validation et optimisation des images destinees aux sites vitrines."""
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings


ALLOWED_EXTENSIONS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}
FORMAT_MIME = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
MIME_ALIASES = {"image/jpg": "image/jpeg"}


class MediaValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ProcessedImage:
    web: bytes
    thumbnail: bytes
    mime_type: str
    width: int
    height: int
    checksum: str


def _encoded_webp(image: Image.Image, *, quality: int) -> bytes:
    output = BytesIO()
    image.save(output, format="WEBP", quality=quality, method=6)
    return output.getvalue()


def process_site_image(content: bytes, filename: str, declared_mime: str | None) -> ProcessedImage:
    max_bytes = settings.site_media_max_upload_mo * 1024 * 1024
    if not content:
        raise MediaValidationError("Le fichier image est vide")
    if len(content) > max_bytes:
        raise MediaValidationError(f"Image trop volumineuse (maximum {settings.site_media_max_upload_mo} Mo)")

    extension = Path(filename or "").suffix.lower()
    expected_format = ALLOWED_EXTENSIONS.get(extension)
    if expected_format is None:
        raise MediaValidationError("Format non autorise. Utilisez PNG, JPG/JPEG ou WEBP")

    declared = MIME_ALIASES.get((declared_mime or "").split(";", 1)[0].strip().lower(), (declared_mime or "").split(";", 1)[0].strip().lower())
    if declared not in FORMAT_MIME.values():
        raise MediaValidationError("Le type MIME annonce n'est pas une image autorisee")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as opened:
                actual_format = (opened.format or "").upper()
                if actual_format not in FORMAT_MIME:
                    raise MediaValidationError("Le fichier n'est pas une image PNG, JPEG ou WEBP valide")
                if actual_format != expected_format:
                    raise MediaValidationError("L'extension du fichier ne correspond pas a son contenu reel")
                actual_mime = FORMAT_MIME[actual_format]
                if declared != actual_mime:
                    raise MediaValidationError("Le type MIME annonce ne correspond pas au contenu reel de l'image")
                if getattr(opened, "n_frames", 1) != 1:
                    raise MediaValidationError("Les images animees ne sont pas acceptees")
                width, height = opened.size
                if width < 32 or height < 32:
                    raise MediaValidationError("L'image est trop petite (minimum 32 x 32 pixels)")
                if width > settings.site_media_max_source_dimension or height > settings.site_media_max_source_dimension:
                    raise MediaValidationError(
                        f"Dimensions trop grandes (maximum {settings.site_media_max_source_dimension} pixels par cote)"
                    )
                if width * height > settings.site_media_max_source_pixels:
                    raise MediaValidationError("L'image contient trop de pixels")
                opened.load()
                oriented = ImageOps.exif_transpose(opened)
                has_alpha = oriented.mode in ("RGBA", "LA") or (oriented.mode == "P" and "transparency" in oriented.info)
                clean = oriented.convert("RGBA" if has_alpha else "RGB")
    except MediaValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise MediaValidationError("Le fichier image est corrompu ou illisible") from exc

    web_image = clean.copy()
    web_image.thumbnail(
        (settings.site_media_web_max_dimension, settings.site_media_web_max_dimension),
        Image.Resampling.LANCZOS,
    )
    thumbnail_image = clean.copy()
    thumbnail_image.thumbnail(
        (settings.site_media_thumbnail_max_dimension, settings.site_media_thumbnail_max_dimension),
        Image.Resampling.LANCZOS,
    )
    web = _encoded_webp(web_image, quality=84)
    thumbnail = _encoded_webp(thumbnail_image, quality=76)
    return ProcessedImage(
        web=web,
        thumbnail=thumbnail,
        mime_type="image/webp",
        width=web_image.width,
        height=web_image.height,
        checksum=sha256(web).hexdigest(),
    )
