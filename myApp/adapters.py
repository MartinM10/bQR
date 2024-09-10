from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_field
from django.core.files.base import ContentFile
import requests
from django.conf import settings
from myApp.models import NotificationPreference, SubscriptionPlan


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # Guardar información adicional
        user.email_verified = sociallogin.account.extra_data.get('email_verified', False)
        user.google_picture_url = sociallogin.account.extra_data.get('picture', '')

        # Asegurarse de que el nombre y apellido se guarden correctamente
        user_field(user, 'first_name', sociallogin.account.extra_data.get('given_name', ''))
        user_field(user, 'last_name', sociallogin.account.extra_data.get('family_name', ''))

        # Añade esta línea después de guardar la imagen de Google:
        # user.image = user.google_picture

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # Asignar el plan básico por defecto
        basic_plan = SubscriptionPlan.objects.get(name='FREE')
        user.subscription_plan = basic_plan
        user.save()

        # Crear preferencias de notificación por defecto
        NotificationPreference.objects.get_or_create(user=user)

        if sociallogin.account.provider == 'google':
            user.email_verified = True
            picture_url = sociallogin.account.extra_data.get('picture')
            if picture_url:
                if getattr(settings, 'DOWNLOAD_SOCIAL_PROFILE_PICTURE', False):
                    # Download and save the image
                    response = requests.get(picture_url)
                    if response.status_code == 200:
                        filename = f"{user.username}_profile_pic.jpg"
                        user.image.save(filename, ContentFile(response.content), save=True)
                else:
                    # Store the URL directly
                    user.google_picture_url = picture_url
                    user.save()
        return user
