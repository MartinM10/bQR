from django.contrib import admin
from .models import Customer, Item, SubscriptionPlan, Notification, NotificationPreference

admin.site.register(Customer)
admin.site.register(Item)
admin.site.register(SubscriptionPlan)
admin.site.register(Notification)
admin.site.register(NotificationPreference)
