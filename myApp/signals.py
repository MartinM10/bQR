from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.conf import settings
from allauth.socialaccount.models import SocialApp
from myApp.config import PLANS
from myApp.models import SubscriptionPlan
from django.contrib.auth import get_user_model


@receiver(post_migrate)
def initialize_site_and_social_app(sender, **kwargs):
    # Configurar el sitio
    site, created = Site.objects.get_or_create(
        domain=settings.DOMAIN,
        defaults={'name': 'beQR'}
    )

    # Actualizar SITE_ID en la configuración
    settings.SITE_ID = site.id

    # Configurar la aplicación de Google
    social_app, created = SocialApp.objects.get_or_create(
        provider='google',
        name='Google',
        client_id=settings.GOOGLE_CLIENT_ID,
        secret=settings.GOOGLE_SECRET
    )

    # Añadir el sitio a la aplicación social si no está ya asociado
    if site not in social_app.sites.all():
        social_app.sites.add(site)

    # Asegurarse de que existe el plan gratuito
    free_plan, _ = SubscriptionPlan.objects.get_or_create(
        name='FREE',
        defaults={
            'price_monthly': 0,
            'price_yearly': 0,
            'duration_days': 365,
            'notifications_per_month': 3,
            'max_items': 1,
            'can_modify_notification_hours': False,
            'can_choose_notification_type': False
        }
    )

    # Asignar el plan gratuito a los usuarios existentes que no tienen plan
    User = get_user_model()
    users_without_plan = User.objects.filter(subscription_plan__isnull=True)
    for user in users_without_plan:
        user.subscription_plan = free_plan
        user.save()

    print(f"Inicialización completada: Sitio (ID: {site.id}), Google Social App y Plan Gratuito configurados.")


@receiver(post_migrate)
def create_subscription_plans(sender, **kwargs):
    for plan_name, plan_details in PLANS.items():
        SubscriptionPlan.objects.update_or_create(
            name=plan_name,
            defaults={
                'price_monthly': plan_details['price_monthly'],
                'price_yearly': plan_details['price_yearly'],
                'duration_days': plan_details['duration_days'],
                'notifications_per_month': plan_details['notifications_per_month'],
                'max_items': plan_details['max_items'],
                'can_modify_notification_hours': plan_details['can_modify_notification_hours'],
                'can_choose_notification_type': plan_details['can_choose_notification_type'],
            }
        )
    print("Planes de suscripción actualizados.")
