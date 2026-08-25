from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan

router = APIRouter(prefix="/stripe", tags=["stripe"])

try:
    import stripe
except ImportError:  # le paquet stripe est optionnel
    stripe = None


def _stripe_pret() -> bool:
    return stripe is not None and bool(settings.stripe_secret_key)


@router.post("/checkout-session")
def creer_session_paiement(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Cree une session Stripe Checkout pour l'abonnement mensuel Suite Artisan.
    Si Stripe n'est pas configure (cles absentes), renvoie une erreur claire
    sans faire planter le reste de l'application."""
    if not _stripe_pret():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe n'est pas configure (STRIPE_SECRET_KEY manquant). Contactez l'administrateur.",
        )
    if not settings.stripe_price_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe n'est pas configure (STRIPE_PRICE_ID manquant).",
        )

    stripe.api_key = settings.stripe_secret_key

    if not artisan.stripe_customer_id:
        customer = stripe.Customer.create(email=artisan.email, name=artisan.nom_entreprise)
        artisan.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=artisan.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        success_url="https://example.com/abonnement/succes",
        cancel_url="https://example.com/abonnement/annule",
        metadata={"artisan_id": str(artisan.id)},
    )
    return {"checkout_url": session.url}


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    """Recoit les evenements Stripe (paiement reussi, abonnement annule, ...).
    Si Stripe n'est pas configure, renvoie une erreur claire plutot que de planter."""
    if not _stripe_pret() or not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe n'est pas configure (cles webhook manquantes).",
        )

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook invalide")

    data = event["data"]["object"]

    if event["type"] == "checkout.session.completed":
        artisan_id = data.get("metadata", {}).get("artisan_id")
        if artisan_id:
            artisan = db.query(Artisan).filter(Artisan.id == int(artisan_id)).first()
            if artisan:
                artisan.subscription_status = "active"
                artisan.stripe_subscription_id = data.get("subscription")
                db.commit()

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.updated"):
        customer_id = data.get("customer")
        artisan = db.query(Artisan).filter(Artisan.stripe_customer_id == customer_id).first()
        if artisan:
            artisan.subscription_status = data.get("status", artisan.subscription_status)
            db.commit()

    return {"received": True}
