from django.core.mail import send_mail
from django.conf import settings
from myApp.models import Notification, NotificationPreference


# Importa aquí las funciones necesarias para enviar SMS y notificaciones push

def send_notification(user, message, severity, reason):
    if not user.can_receive_notification():
        return False

    notification = Notification.objects.create(
        user=user,
        message=message,
        severity=severity,
        reason=reason
    )

    try:
        preferences = NotificationPreference.objects.get(user=user)
    except NotificationPreference.DoesNotExist:
        preferences = None

    sent = False

    if preferences:
        if preferences.email_notifications and user.email:
            send_mail(
                'Nueva notificación',
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
            sent = True

        if preferences.sms_notifications and user.phone:
            # Aquí iría el código para enviar SMS
            # send_sms(user.phone, message)
            sent = True

        if preferences.push_notifications:
            # Aquí iría el código para enviar notificaciones push
            # send_push_notification(user, message)
            sent = True

        if preferences.whatsapp_notifications and user.phone:
            # Aquí iría el código para enviar mensajes de WhatsApp
            # send_whatsapp(user.phone, message)
            sent = True

    if sent:
        user.notifications_count += 1
        user.save()
        return True
    else:
        # Si no se pudo enviar por ningún método, eliminamos la notificación creada
        notification.delete()
        return False
