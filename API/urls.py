from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls
from .views import CustomerViewSet, ItemViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'items', ItemViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('docs/', include_docs_urls(title='API V1 documentation'))
]
