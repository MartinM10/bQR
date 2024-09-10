from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, ItemViewSet, NotificationViewSet, SubscriptionPlanViewSet, \
    NotificationPreferenceViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'items', ItemViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'subscription-plans', SubscriptionPlanViewSet)
router.register(r'notification-preferences', NotificationPreferenceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
