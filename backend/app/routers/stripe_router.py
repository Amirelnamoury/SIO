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


def _prix_par_plan() -> dict[str, str | None]:
    """stripe_price_id reste le nom historique (compatibilite) : c'est le
    prix du plan "essentiel", le premier palier payant."""
    return {
        "essentiel": settings.stripe_price_id,
        "pro": settings.stripe_price_id_pro,
        "business": settings.stripe_price_id_business,
    }


@router.post("/checkout-session")
def creer_session_paiement(
    plan: str = "essentiel",
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Cree une session Stripe Checkout pour l'un des 3 plans payants de
    Suite Artisan (essentiel/pro/business). Si Stripe n'est pas configure
    (cles absentes) ou que le prix du plan demande n'est pas defini, renvoie
    une erreur claire sans faire planter le reste de l'application."""
    if plan not in ("essentiel", "pro", "business"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="plan doit etre l'un de : essentiel, pro, business")
    if not _stripe_pret():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe n'est pas configure (STRIPE_SECRET_KEY manquant). Contactez l'administrateur.",
        )
    price_id = _prix_par_plan()[plan]
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Stripe n'est pas configure pour le plan {plan} (prix manquant).",
        )

    stripe.api_key = settings.stripe_secret_key

    if not artisan.stripe_customer_id:
        customer = stripe.Customer.create(email=artisan.email, name=artisan.nom_entreprise)
        artisan.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=artisan.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.app_base_url}/?abonnement=succes",
        cancel_url=f"{settings.app_base_url}/?abonnement=annule",
        metadata={"artisan_id": str(artisan.id), "plan": plan},
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
                plan = data.get("metadata", {}).get("plan")
                if plan in ("essentiel", "pro", "business"):
                    artisan.plan = plan
                # Toujours resynchroniser depuis l'evenement webhook (source
                # de verite Stripe), plutot que de dependre uniquement de
                # l'ecriture faite a la creation de la session de paiement -
                # rend customer.subscription.* fiable meme si cette premiere
                # ecriture avait echoue ou ete contournee.
                if data.get("customer"):
                    artisan.stripe_customer_id = data.get("customer")
                db.commit()

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.updated"):
        customer_id = data.get("customer")
        artisan = db.query(Artisan).filter(Artisan.stripe_customer_id == customer_id).first()
        if artisan:
            artisan.subscription_status = data.get("status", artisan.subscription_status)
            db.commit()

    return {"received": True}
