import os
import django
import random
from datetime import timedelta
from io import BytesIO
import qrcode
from django.core.files.uploadedfile import SimpleUploadedFile
from myApp.config import DOMAIN, PLANS

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beQR.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from myApp.models import SubscriptionPlan, Item, NotificationPreference, Notification

Customer = get_user_model()

def create_subscription_plans():
    for plan_name, plan_data in PLANS.items():
        SubscriptionPlan.objects.update_or_create(
            name=plan_name,
            defaults=plan_data
        )
    print("Planes de suscripción creados o actualizados.")

def create_customers():
    plans = list(SubscriptionPlan.objects.all())
    customers = [
        {
            'username': 'usuario1',
            'email': 'usuario1@example.com',
            'password': 'contraseña123',
            'first_name': 'Usuario',
            'last_name': 'Uno',
            'gender': 'M',
            'phone': '123456789',
        },
        {
            'username': 'usuario2',
            'email': 'usuario2@example.com',
            'password': 'contraseña123',
            'first_name': 'Usuario',
            'last_name': 'Dos',
            'gender': 'F',
            'phone': '987654321',
        },
        {
            'username': 'usuario3',
            'email': 'usuario3@example.com',
            'password': 'contraseña123',
            'first_name': 'Usuario',
            'last_name': 'Tres',
            'gender': 'O',
            'phone': '555555555',
        },
    ]

    for i, customer_data in enumerate(customers):
        customer, created = Customer.objects.update_or_create(
            username=customer_data['username'],
            defaults=customer_data
        )
        if created:
            customer.set_password(customer_data['password'])
        customer.subscription_plan = plans[i % len(plans)]
        customer.subscription_end_date = timezone.now() + timedelta(days=customer.subscription_plan.duration_days)
        customer.auto_renew = bool(i % 2)
        customer.save()

    print("Clientes creados o actualizados.")

def create_items():
    customers = Customer.objects.all()
    items = [
        {'name': 'Llaves', 'description': 'Llaves de casa'},
        {'name': 'Cartera', 'description': 'Cartera de cuero'},
        {'name': 'Teléfono', 'description': 'Smartphone'},
        {'name': 'Laptop', 'description': 'Computadora portátil'},
        {'name': 'Tablet', 'description': 'Tablet Android'},
        {'name': 'Reloj', 'description': 'Reloj de pulsera'},
    ]

    for customer in customers:
        max_items = customer.subscription_plan.max_items
        for item_data in items[:max_items]:
            item, created = Item.objects.update_or_create(
                owner=customer,
                name=item_data['name'],
                defaults={'description': item_data['description']}
            )

            if created or not item.qrCode:
                owner_uuid = str(customer.uuid)
                url = f'{DOMAIN}/scan-qr/{owner_uuid}'
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
                qr.add_data(url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                image_io = BytesIO()
                img.save(image_io, 'PNG')
                image_file = SimpleUploadedFile(f'{customer.username}/qr_codes/{item.name}.png',
                                                image_io.getvalue(), content_type='image/png')
                item.qrCode = image_file
                item.save()

    print("Items creados o actualizados respetando los límites del plan y con códigos QR generados.")

def create_notification_preferences():
    customers = Customer.objects.all()

    for customer in customers:
        NotificationPreference.objects.update_or_create(
            user=customer,
            defaults={
                'email_notifications': random.choice([True, False]),
                'sms_notifications': random.choice([True, False]),
                'push_notifications': random.choice([True, False]),
                'whatsapp_notifications': random.choice([True, False]),
                'notification_start_time': timezone.now().time().replace(hour=random.randint(0, 12),
                                                                         minute=random.randint(0, 59)),
                'notification_end_time': timezone.now().time().replace(hour=random.randint(13, 23),
                                                                       minute=random.randint(0, 59)),
                'show_contact_info_on_scan': random.choice([True, False]),
            }
        )

    print("Preferencias de notificación creadas o actualizadas.")

def create_notifications():
    customers = Customer.objects.all()
    severity_choices = ['low', 'medium', 'high', 'urgent']
    reason_choices = ['lost_item', 'found_item', 'system']

    for customer in customers:
        for _ in range(5):
            Notification.objects.create(
                user=customer,
                severity=random.choice(severity_choices),
                reason=random.choice(reason_choices),
                message=f'Notificación de prueba para {customer.username}: {random.choice(reason_choices)} - {random.choice(severity_choices)}',
                is_read=random.choice([True, False]),
            )

    print("Notificaciones creadas.")

if __name__ == '__main__':
    create_subscription_plans()
    create_customers()
    create_items()
    create_notification_preferences()
    create_notifications()
    print("Datos de prueba cargados exitosamente.")
