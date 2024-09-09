import os
import django

# Configura el entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beQR.settings")
django.setup()

from django.contrib.auth import get_user_model
from myApp.models import SubscriptionPlan

User = get_user_model()

def assign_basic_plan():
    try:
        basic_plan = SubscriptionPlan.objects.get(name='FREE')
    except SubscriptionPlan.DoesNotExist:
        print("Error: El plan 'FREE' no existe. Por favor, ejecuta setup_site.py primero.")
        return

    users_without_plan = User.objects.filter(subscription_plan__isnull=True)
    
    for user in users_without_plan:
        user.subscription_plan = basic_plan
        user.save()
        print(f'Plan básico asignado a {user.username}')

    print(f'Se asignó el plan básico a {users_without_plan.count()} usuarios')

if __name__ == "__main__":
    assign_basic_plan()