from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from ownerQR import settings
from myApp import views

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/v1/', include('API.urls'), name='api'),
                  path('', views.home, name='home'),
                  path('register/', views.register_user, name='register'),
                  path('register/item/', views.register_item, name='register_item'),
                  path('logout/', views.logout_request, name='logout'),
                  path('login/', views.login_request, name='login'),
                  path('edit/item/<str:item_id>', views.edit_item, name='edit_item'),
                  path('edit/profile/', views.edit_profile, name='edit_profile'),
                  path('download-qr/<str:item_id>', views.download_qr, name='download_qr'),
                  path('scan-qr/<str:owner_id>', views.scan_qr, name='scan_qr'),
                  path('change_password/', views.change_password, name='change_password'),
                  path('password_change_success/', views.password_change_success_view, name='password_change_success'),
                  path('change_profile_picture/', views.change_profile_picture, name='change_profile_picture'),
                  path('change_item_picture/<str:item_id>', views.change_item_picture,
                       name='change_item_picture'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
