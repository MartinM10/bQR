from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework.authtoken.views import obtain_auth_token

from beQR import settings
from myApp.views import (home, register, register_item, logout_request, login_request, edit_item, edit_profile,
                         download_qr, scan_qr, verify_email, change_password, password_change_success_view,
                         change_profile_picture, change_item_picture, upgrade_to_premium, manage_subscription,
                         edit_notification_preferences, view_all_notifications, mark_notification_as_read,
                         toggle_auto_renew)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="BeQR API",
        default_version='v1',
        description="API for BeQR application",
        terms_of_service="https://www.beQR.com/terms/",
        contact=openapi.Contact(email="contact@beQR.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/v1/', include('API.urls'), name='api'),
                  path('', home, name='home'),
                  # path('register/', views.register_user, name='register'),
                  path('register/', register, name='register'),
                  path('register/item/', register_item, name='register_item'),
                  path('logout/', logout_request, name='logout'),
                  path('login/', login_request, name='login'),
                  path('edit/item/<str:item_id>', edit_item, name='edit_item'),
                  path('edit-profile/', edit_profile, name='edit_profile'),
                  path('download-qr/<str:item_id>', download_qr, name='download_qr'),
                  path('scan-qr/<str:owner_id>', scan_qr, name='scan_qr'),
                  path('change_password/', change_password, name='change_password'),
                  path('password_change_success/', password_change_success_view, name='password_change_success'),
                  path('change_profile_picture/', change_profile_picture, name='change_profile_picture'),
                  path('change_item_picture/<str:item_id>', change_item_picture,
                       name='change_item_picture'),
                  path('upgrade-to-premium/', upgrade_to_premium, name='upgrade_to_premium'),
                  path('manage-subscription/', manage_subscription, name='manage_subscription'),
                  path('edit-notification-preferences/', edit_notification_preferences,
                       name='edit_notification_preferences'),
                  path('notifications/', view_all_notifications, name='view_all_notifications'),
                  path('notifications/mark-as-read/<int:notification_id>/', mark_notification_as_read,
                       name='mark_notification_as_read'),
                  path('toggle-auto-renew/', toggle_auto_renew, name='toggle_auto_renew'),
                  path('accounts/', include('allauth.urls')),
                  path('verify-email/<uidb64>/<token>/', verify_email, name='verify_email'),
                  path('api-token-auth/', obtain_auth_token),
                  re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),
                          name='schema-json'),
                  path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
                  path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
