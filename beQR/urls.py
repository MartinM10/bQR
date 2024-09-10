from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from beQR import settings
from myApp import views

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/v1/', include('API.urls'), name='api'),
                  path('', views.home, name='home'),
                  # path('register/', views.register_user, name='register'),
                  path('register/', views.register, name='register'),
                  path('register/item/', views.register_item, name='register_item'),
                  path('logout/', views.logout_request, name='logout'),
                  path('login/', views.login_request, name='login'),
                  path('edit/item/<str:item_id>', views.edit_item, name='edit_item'),
                  path('edit-profile/', views.edit_profile, name='edit_profile'),
                  path('download-qr/<str:item_id>', views.download_qr, name='download_qr'),
                  path('scan-qr/<str:owner_id>', views.scan_qr, name='scan_qr'),
                  path('change_password/', views.change_password, name='change_password'),
                  path('password_change_success/', views.password_change_success_view, name='password_change_success'),
                  path('change_profile_picture/', views.change_profile_picture, name='change_profile_picture'),
                  path('change_item_picture/<str:item_id>', views.change_item_picture,
                       name='change_item_picture'),
                  path('upgrade-to-premium/', views.upgrade_to_premium, name='upgrade_to_premium'),
                  path('manage-subscription/', views.manage_subscription, name='manage_subscription'),
                  path('edit-notification-preferences/', views.edit_notification_preferences,
                       name='edit_notification_preferences'),
                  path('notifications/', views.view_all_notifications, name='view_all_notifications'),
                  path('notifications/mark-as-read/<int:notification_id>/', views.mark_notification_as_read,
                       name='mark_notification_as_read'),
                  path('toggle-auto-renew/', views.toggle_auto_renew, name='toggle_auto_renew'),
                  path('accounts/', include('allauth.urls')),
                  path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
