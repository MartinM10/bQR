from io import BytesIO
import uuid
from click import File
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import qrcode
from beQR.settings import MEDIA_URL, STATIC_URL
from django.utils import timezone


def upload_to_profile(instance, filename):
    return f'images/{instance.username}/profile_images/{filename}'


def upload_to_items(instance, filename):
    return f'images/{instance.owner.username}/items/{filename}'


def upload_to_qr(instance, filename):
    return f'images/{instance.owner.username}/qr_codes/{filename}'


def upload_to_notification(instance, filename):
    return f'images/{instance.owner.username}/notifications/{filename}'


# Create your models here.
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price_monthly = models.DecimalField(max_digits=6, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=6, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    notifications_per_month = models.IntegerField()
    max_items = models.IntegerField()
    can_modify_notification_hours = models.BooleanField(default=False)
    can_choose_notification_type = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Customer(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    gender = models.CharField(max_length=10,
                              choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
                              null=True,
                              blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    image = models.ImageField(upload_to=upload_to_profile, null=True, blank=True)
    conditionsAccepted = models.BooleanField(default=False)
    public_profile = models.BooleanField(default=False)
    email = models.EmailField(blank=True, null=True)

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

    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    notifications_count = models.IntegerField(default=0)
    notifications_reset_date = models.DateTimeField(default=timezone.now)

    def get_subscription_type(self):
        return self.subscription_plan.name if self.subscription_plan else "Gratuito"

    def can_receive_notification(self):
        if not self.subscription_plan:
            return False

        # Check if it's time to reset the notification count
        if timezone.now() >= self.notifications_reset_date:
            self.notifications_count = 0
            self.notifications_reset_date = timezone.now() + timezone.timedelta(days=30)
            self.save()

        # Check if the user has reached their notification limit
        if self.notifications_count >= self.subscription_plan.notifications_per_month:
            return False

        # Check if the current time is within the user's preferred notification hours
        try:
            preferences = self.notificationpreference
        except NotificationPreference.DoesNotExist:
            return False

        now = timezone.localtime(timezone.now()).time()
        start_time = preferences.notification_start_time
        end_time = preferences.notification_end_time

        if start_time < end_time:
            return start_time <= now < end_time
        else:  # Si el rango cruza la medianoche
            return now >= start_time or now < end_time

    def increment_notification_count(self):
        self.notifications_count += 1
        self.save()

    def update_subscription(self, new_plan):
        self.subscription_plan = new_plan
        self.subscription_end_date = timezone.now() + timezone.timedelta(days=new_plan.duration_days)
        self.save()

    def can_create_item(self):
        return self.item_set.count() < self.subscription_plan.max_items


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

    def generate_qr_code(self):
        url = f'{settings.DOMAIN}/scan-qr/{self.uuid}/'
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        file_name = f'{self.owner.username}/qr_codes/{self.name}.png'
        self.qrCode.save(file_name, File(buffer), save=False)


class Notification(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ]
    REASON_CHOICES = [
        ('lost_item', 'Objeto Perdido'),
        ('found_item', 'Objeto Encontrado'),
        ('system', 'Notificación del Sistema'),
        ('others', 'Otros')
    ]

    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def get_severity_display(self):
        return dict(self.SEVERITY_CHOICES).get(self.severity, self.severity)

    def get_reason_display(self):
        return dict(self.REASON_CHOICES).get(self.reason, self.reason)


class NotificationPreference(models.Model):
    user = models.OneToOneField(Customer, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=False)
    notification_start_time = models.TimeField(default='09:00')
    notification_end_time = models.TimeField(default='21:00')
    show_contact_info_on_scan = models.BooleanField(default=False)

    def __str__(self):
        return f"Preferencias de notificación para {self.user.username}"
