from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from myApp.models import Item, Customer, NotificationPreference
from django.core.exceptions import ValidationError
from PIL import Image
from datetime import time


# Validación para números de teléfono
def clean_telefono(value):
    if value and not value.isdigit():
        raise forms.ValidationError("El número de teléfono debe contener solo dígitos.")


def validate_image(value):
    if not value:
        raise ValidationError("Debes seleccionar una imagen.")
    if not value.content_type.startswith('image'):
        raise ValidationError("El archivo seleccionado no es una imagen válida.")
    try:
        image = Image.open(value)
        if image.format not in ['JPEG', 'PNG', 'WEBP']:
            raise ValidationError("El formato de la imagen no es válido. Debe ser JPEG, PNG o WEBP.")
    except Exception as e:
        raise ValidationError("No se pudo abrir la imagen. Asegúrate de que sea un archivo de imagen válido.")


def clean_image(value):
    if value:
        try:
            # Abre la image para verificar su formato
            image = Image.open(value)

            # Verifica si el formato es PNG o JPEG
            if image.format not in ['JPEG', 'PNG']:
                raise forms.ValidationError("El formato de la image no es válido. Debe ser JPEG o PNG.")

        except Exception as e:
            raise forms.ValidationError(
                "No se pudo abrir la image. Asegúrate de que sea un archivo de image válido.")


class CustomUserCreationForm(UserCreationForm):
    image = forms.ImageField(required=False, validators=[validate_image])
    phone = forms.CharField(max_length=15, required=True, validators=[clean_telefono])
    email = forms.EmailField(required=True)

    class Meta:
        model = Customer
        fields = ['username', 'first_name', 'last_name', 'gender', 'phone', 'email', 'password1', 'password2',
                  'image']

    def clean_image(self):
        return clean_image(self.cleaned_data.get('image'))


class FormItem(forms.ModelForm):
    image = forms.ImageField(required=False, validators=[validate_image])

    class Meta:
        model = Item
        fields = ['name', 'description', 'image']

    def clean_image(self):
        return clean_image(self.cleaned_data.get('image'))


class ChangeProfilePictureForm(forms.ModelForm):
    image = forms.ImageField(required=False, validators=[validate_image])

    class Meta:
        model = Customer
        fields = ['image']


class ChangeItemPictureForm(forms.ModelForm):
    image = forms.ImageField(required=False, validators=[validate_image])

    class Meta:
        model = Item
        fields = ['image']


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'image']


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['email', 'first_name', 'last_name', 'phone']


class ChangePasswordForm(PasswordChangeForm):
    # Puedes personalizar el formulario aquí
    new_password = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    confirm_password = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean_confirm_password(self):
        new_password = self.cleaned_data.get('new_password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden. Por favor, inténtalo de nuevo.")
        return confirm_password


class NotificationPreferenceForm(forms.ModelForm):
    NOTIFICATION_SCHEDULE_CHOICES = [
        ('24h', 'Las 24 horas'),
        ('day', 'Solo de día (08:00 - 21:00)'),
        ('night', 'Solo de noche (21:00 - 08:00)'),
        ('custom', 'Personalizado'),
    ]

    notification_schedule = forms.ChoiceField(
        choices=NOTIFICATION_SCHEDULE_CHOICES,
        widget=forms.RadioSelect,
        label="Horario de notificaciones"
    )

    class Meta:
        model = NotificationPreference
        fields = ['notification_schedule', 'notification_start_time', 'notification_end_time', 'email_notifications',
                  'sms_notifications', 'push_notifications', 'whatsapp_notifications', 'show_contact_info_on_scan']
        widgets = {
            'notification_start_time': forms.TimeInput(attrs={'type': 'time'}),
            'notification_end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(NotificationPreferenceForm, self).__init__(*args, **kwargs)
        if user and not user.subscription_plan.can_modify_notification_hours:
            del self.fields['notification_schedule']
            del self.fields['notification_start_time']
            del self.fields['notification_end_time']
        if user and not user.subscription_plan.can_choose_notification_type:
            del self.fields['email_notifications']
            del self.fields['sms_notifications']
            del self.fields['push_notifications']
            del self.fields['whatsapp_notifications']

    def clean(self):
        cleaned_data = super().clean()
        schedule = cleaned_data.get('notification_schedule')
        if schedule == '24h':
            cleaned_data['notification_start_time'] = time(0, 0)
            cleaned_data['notification_end_time'] = time(0, 0)
        elif schedule == 'day':
            cleaned_data['notification_start_time'] = time(8, 0)
            cleaned_data['notification_end_time'] = time(21, 0)
        elif schedule == 'night':
            cleaned_data['notification_start_time'] = time(21, 0)
            cleaned_data['notification_end_time'] = time(8, 0)
        return cleaned_data


class ContactForm(forms.Form):
    SEVERITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    REASON_CHOICES = [
        ('lost_item', 'Objeto perdido'),
        ('found_item', 'Objeto encontrado'),
        ('damaged_item', 'Objeto dañado'),
        ('other', 'Otro'),
    ]

    severity = forms.ChoiceField(choices=SEVERITY_CHOICES, label='Gravedad')
    reason = forms.ChoiceField(choices=REASON_CHOICES, label='Motivo')
    contact_method = forms.ChoiceField(required=False, label='Método de contacto')
    message = forms.CharField(widget=forms.Textarea, label='Mensaje')

    def __init__(self, *args, **kwargs):
        contact_methods = kwargs.pop('contact_methods', [])
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['contact_method'].choices = [(method, label) for method, label, _ in contact_methods]
