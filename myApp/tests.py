from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Item, NotificationPreference, Notification


class ModelTests(TestCase):
    def setUp(self):
        self.Customer = get_user_model()
        self.customer = self.Customer.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_customer_creation(self):
        self.assertEqual(self.customer.username, 'testuser')
        self.assertEqual(self.customer.email, 'test@example.com')

    def test_item_creation(self):
        item = Item.objects.create(
            owner=self.customer,
            name='Test Item',
            description='This is a test item'
        )
        self.assertEqual(item.name, 'Test Item')
        self.assertEqual(item.owner, self.customer)

    def test_notification_preference_creation(self):
        pref = NotificationPreference.objects.create(
            user=self.customer,
            email_notifications=True,
            sms_notifications=False
        )
        self.assertEqual(pref.user, self.customer)
        self.assertTrue(pref.email_notifications)
        self.assertFalse(pref.sms_notifications)

    def test_notification_creation(self):
        notif = Notification.objects.create(
            user=self.customer,
            severity='high',
            reason='lost_item',
            message='Your item has been found'
        )
        self.assertEqual(notif.user, self.customer)
        self.assertEqual(notif.severity, 'high')
        self.assertEqual(notif.reason, 'lost_item')
