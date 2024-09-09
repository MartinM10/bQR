from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field

from myApp.models import NotificationPreference, SubscriptionPlan

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        
        # Guardar información adicional
        user.email_verified = sociallogin.account.extra_data.get('email_verified', False)
        user.google_picture = sociallogin.account.extra_data.get('picture', '')
        
        # Asegurarse de que el nombre y apellido se guarden correctamente
        user_field(user, 'first_name', sociallogin.account.extra_data.get('given_name', ''))
        user_field(user, 'last_name', sociallogin.account.extra_data.get('family_name', ''))
        
        # Añade esta línea después de guardar la imagen de Google:
        user.image = user.google_picture
        
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        
        # Asignar el plan básico por defecto
        basic_plan = SubscriptionPlan.objects.get(name='FREE')
        user.subscription_plan = basic_plan
        user.save()
        
        # Crear preferencias de notificación por defecto
        NotificationPreference.objects.get_or_create(user=user)
        
        return user