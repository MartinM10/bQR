import os
import django
from django.core.exceptions import ImproperlyConfigured

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beQR.settings')
django.setup()

from django.contrib.sites.models import Site
from django.conf import settings
from allauth.socialaccount.models import SocialApp
from myApp.models import SubscriptionPlan
from myApp.config import PLANS

def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = f"Set the {var_name} environment variable"
        raise ImproperlyConfigured(error_msg)

def setup_site():
    # Crear o actualizar el sitio
    domain = get_env_variable('DOMAIN')
    site, created = Site.objects.get_or_create(
        domain=domain,
        defaults={'name': 'beQR'}
    )
    
    # Actualizar SITE_ID en settings
    settings_path = os.path.join(settings.BASE_DIR, 'beQR', 'settings.py')
    with open(settings_path, 'r') as f:
        content = f.read()
    
    new_content = content.replace(
        f"SITE_ID = {settings.SITE_ID}",
        f"SITE_ID = {site.id}"
    )
    
    with open(settings_path, 'w') as f:
        f.write(new_content)
    
    print(f"Site created/updated with ID: {site.id}")
    print("settings.py updated with new SITE_ID")

    # Configurar la aplicación de Google
    client_id = get_env_variable('GOOGLE_CLIENT_ID')
    secret = get_env_variable('GOOGLE_SECRET')

    social_app, created = SocialApp.objects.get_or_create(
        provider='google',
        name='Google',
        client_id=client_id,
        secret=secret
    )

    if created:
        print("Google Social App created")
    else:
        print("Google Social App updated")

    # Asegurarse de que el sitio esté asociado con la aplicación social
    social_app.sites.add(site)

    print("Google Social App associated with the site")

    # Crear o actualizar los planes de suscripción
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
    print("Subscription plans created/updated")

if __name__ == "__main__":
    setup_site()