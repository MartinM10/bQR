import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from ownerQR.settings import MEDIA_URL, STATIC_URL


def upload_to_profile(instance, filename):
    return f'images/{instance.username}/profile_images/{filename}'


def upload_to_items(instance, filename):
    return f'images/{instance.owner.username}/items/{filename}'


def upload_to_qr(instance, filename):
    return f'images/{instance.owner.username}/qr_codes/{filename}'


def upload_to_notification(instance, filename):
    return f'images/{instance.owner.username}/notifications/{filename}'


# Create your models here.
class Customer(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    gender = models.CharField(max_length=10,
                              choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
                              null=True,
                              blank=True)
    phone = models.CharField(max_length=15)
    image = models.ImageField(upload_to=upload_to_profile, null=True, blank=True)
    conditionsAccepted = models.BooleanField(default=False)
    byWhatsapp = models.BooleanField(default=False)
    byPhoneNumber = models.BooleanField(default=False)
    byEmail = models.BooleanField(default=False)
    byNotifications = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email", "phone"]

    class Meta:
        verbose_name = _("customer")
        verbose_name_plural = _("customer")

    def __str__(self):
        return self.username

    def get_image(self):
        """
        Return the user image.
        """
        if self.image:
            return '{}{}'.format(MEDIA_URL, self.image)

        return '{}{}'.format(STATIC_URL, 'images/user_image_empty.png')


class Item(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to=upload_to_items, null=True, blank=True)
    qrCode = models.ImageField(upload_to=upload_to_qr, null=True, blank=True)

    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")

    def __str__(self):
        return self.name

    def get_image(self):
        """
        Return the item image.
        """
        if self.image:
            return '{}{}'.format(MEDIA_URL, self.image)

        return '{}{}'.format(STATIC_URL, 'images/item_image_empty.png')

    def get_qrcode(self):
        """
        Return the QR Code image.
        """
        if self.qrCode:
            return '{}{}'.format(MEDIA_URL, self.qrCode)

        else:
            return None


class Notification(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # emisor = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='mensajes_enviados')
    idQRSend = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='assigned_qr')
    receiver = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='receiver_message')
    ipUserThatSend = models.CharField(max_length=50)
    title = models.CharField(max_length=150)
    description = models.TextField()
    optionalObservation = models.TextField()
    image = models.ImageField(upload_to=upload_to_notification, null=True, blank=True)
    dateNotificationSend = models.DateTimeField(auto_now_add=True)

    # received = models.BooleanField(default=False)
    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")

    def get_image(self):
        """
        Return the notification image.
        """
        if self.image:
            return '{}{}'.format(MEDIA_URL, self.image)

        else:
            return None
