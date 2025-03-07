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


def upload_to_promotional_qr(instance, filename):
    return f'images/promotional_qr/{filename}'


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Subscription plan {self.name}'


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
    email_verified = models.BooleanField(default=False)
    google_picture_url = models.URLField(max_length=255, blank=True, null=True)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    notifications_count = models.IntegerField(default=0)
    notifications_reset_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ["email", "phone"]

    class Meta:
        verbose_name = _("customer")
        verbose_name_plural = _("customers")

    def __str__(self):
        return self.username

    def get_image(self):
        """
        Return the user image.
        """
        if self.image:
            return f'{MEDIA_URL}{self.image}'
        elif self.google_picture_url:
            return self.google_picture_url
        return f'{STATIC_URL}images/user_image_empty.png'

    def get_default_shipping_address(self):
        return self.shipping_addresses.filter(default=True).first()

    def get_subscription_type(self):
        return self.subscription_plan.name if self.subscription_plan else "Free"

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
        if not self.subscription_plan:
            return False  # Los usuarios sin plan no pueden crear ítems
        return self.items.count() < self.subscription_plan.max_items


class QRCode(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # code = models.CharField(max_length=32, unique=True)
    secret_code = models.CharField(max_length=6, blank=True, null=True)
    qr_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    is_physical = models.BooleanField(default=False)
    is_assigned = models.BooleanField(default=False)
    is_activated = models.BooleanField(default=False)
    # activation_email = models.EmailField(blank=True, null=True)
    used_on = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # used_by = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)

    # associated_item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True)
    # qr_image = models.ImageField(upload_to=upload_to_promotional_qr, null=True, blank=True)

    def __str__(self):
        return f"QR Code {self.uuid}"


class Item(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to=upload_to_items, null=True, blank=True)
    qr_code = models.OneToOneField(QRCode, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
        if self.qr_code and self.qr_code.qr_image:
            return f'{settings.MEDIA_URL}{self.qr_code.qr_image}'
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
        self.qr_code.save(file_name, File(str(buffer)))
        self.save()  # Agregando la llamada para guardar


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

    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='receiver_notifications')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferencias de notificación de {self.user.username}"


class ShippingAddress(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='shipping_addresses')
    default = models.BooleanField(default=False)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}, {self.country}"


class QRCodeOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'En Proceso'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]

    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='receiver_qrcode_orders')
    items = models.ManyToManyField(Item)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True,
                                         related_name='shipping_orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido #{self.id} - {self.user.username} - {self.status}"

    def get_items_count(self):
        return self.items.count()

    def get_items_list(self):
        return ", ".join([item.name for item in self.items.all()])

    def is_cancelable(self):
        return self.status in ['pending', 'processing']

    def cancel_order(self):
        if self.is_cancelable():
            self.status = 'cancelled'
            self.save()
            return True
        return False

    def update_status(self, new_status):
        if new_status in dict(self.STATUS_CHOICES):
            self.status = new_status
            self.save()
            return True
        return False

    def is_recent(self):
        return (timezone.now() - self.created_at).days < 7
