from django.core.mail import send_mail
from myApp.models import Notification, NotificationPreference
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from PIL import Image, ImageDraw, ImageFont
import io
import os
from django.conf import settings


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


def generate_styled_qr(data, item_name):
    # Crear el código QR
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    # Crear una imagen QR con esquinas redondeadas
    qr_img = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
    qr_img = qr_img.convert("RGBA")

    # Cargar la imagen de fondo
    background = Image.open(os.path.join(settings.STATIC_ROOT, 'images', 'qr_background.png')).convert("RGBA")

    # Redimensionar el código QR para que quepa en el centro de la imagen de fondo
    qr_size = min(background.size) // 2
    qr_img = qr_img.resize((qr_size, qr_size))

    # Calcular la posición para centrar el QR en la imagen de fondo
    position = ((background.width - qr_img.width) // 2, (background.height - qr_img.height) // 2)

    # Pegar el QR en el centro de la imagen de fondo
    background.paste(qr_img, position, qr_img)

    # Añadir el nombre del item
    draw = ImageDraw.Draw(background)
    font = ImageFont.load_default()
    text_bbox = draw.textbbox((0, 0), item_name, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_position = ((background.width - text_width) // 2, background.height - text_height - 10)
    draw.text(text_position, item_name, font=font, fill='black')

    # Convertir la imagen a bytes
    img_byte_arr = io.BytesIO()
    background.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
