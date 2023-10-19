from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from myApp.models import Item, Customer
from django.core.exceptions import ValidationError
from PIL import Image


# Validación para números de teléfono
def clean_telefono(value):
    if value and not value.isdigit():
        raise forms.ValidationError("El número de teléfono debe contener solo dígitos.")


def validate_image(value):
    if not value:
        raise ValidationError("Debes seleccionar una image.")
    if not value.content_type.startswith('image'):
        raise ValidationError("El archivo seleccionado no es una image válida.")


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


class EditUserProfileForm(forms.ModelForm):
    image = forms.ImageField(required=False, validators=[validate_image])
    phone = forms.CharField(max_length=15, required=True, validators=[clean_telefono])
    email = forms.EmailField(required=True)

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'gender', 'phone', 'email', 'image']


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
