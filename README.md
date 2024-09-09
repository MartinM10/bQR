# 🔒 bQR: Tus cosas, tu seguridad, tu QR 🔒

## 📱 ¿Qué es bQR?

bQR es una innovadora aplicación web que te permite proteger tus pertenencias mediante códigos QR personalizados. Con bQR, puedes:

- 🏷️ Crear etiquetas QR únicas para tus objetos valiosos
- 📢 Recibir notificaciones si alguien encuentra tus pertenencias perdidas
- 🔐 Gestionar la información de contacto que compartes
- 👥 Conectar de forma segura con las personas que encuentren tus objetos

## 🚀 Características principales

- 🎨 Generación de códigos QR personalizados
- 📅 Planes de suscripción flexibles
- 🔔 Sistema de notificaciones configurable
- 👤 Perfiles de usuario personalizables
- 🌙 Modo oscuro para una mejor experiencia visual

## 🛠️ Instalación y despliegue

### Requisitos previos

- Python 3.8+
- pip
- virtualenv (opcional, pero recomendado)

### Pasos para la instalación

1. Clona el repositorio:
   ```
   git clone https://github.com/tu-usuario/bQR.git
   cd bQR
   ```

2. Crea y activa un entorno virtual (opcional):
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Configura las variables de entorno:
   modifica el nombre del fichero `.env.template` en la raíz del proyecto y llamalo `.env`; Establece los valores de las variables que se utilizan en el proyecto.
   Por ejemplo estas son algunas de las variables:
   ```
   SECRET_KEY=tu_clave_secreta
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=sqlite:///db.sqlite3
   GOOGLE_CLIENT_ID=tu_id_de_cliente_de_google
   GOOGLE_SECRET=tu_secreto_de_google

   FREE_PLAN_PRICE_MONTHLY=0
   FREE_PLAN_PRICE_YEARLY=0
   FREE_PLAN_DURATION_DAYS=365
   FREE_PLAN_NOTIFICATIONS_PER_MONTH=3
   FREE_PLAN_MAX_ITEMS=1

   PREMIUM_PLAN_PRICE_MONTHLY=9.99
   PREMIUM_PLAN_PRICE_YEARLY=99.99
   PREMIUM_PLAN_DURATION_DAYS=365
   PREMIUM_PLAN_NOTIFICATIONS_PER_MONTH=100
   PREMIUM_PLAN_MAX_ITEMS=5

   PRO_PLAN_PRICE_MONTHLY=19.99
   PRO_PLAN_PRICE_YEARLY=199.99
   PRO_PLAN_DURATION_DAYS=365
   PRO_PLAN_NOTIFICATIONS_PER_MONTH=500
   PRO_PLAN_MAX_ITEMS=10
   ```

5. Realiza las migraciones de la base de datos:
   ```
   python manage.py migrate
   ```

6. Crea un superusuario:
   ```
   python manage.py createsuperuser
   ```

7. Inicia el servidor de desarrollo:
   ```
   python manage.py runserver
   ```

8. Visita `http://localhost:8000` en tu navegador para ver la aplicación en funcionamiento.

## 🌟 Uso

1. Regístrate o inicia sesión en la aplicación.
2. Crea un nuevo item y genera su código QR.
3. Imprime o guarda el código QR y colócalo en tu objeto.
4. Configura tus preferencias de notificación.
5. ¡Listo! Ahora tus objetos están protegidos con bQR.

## 🤝 Contribuir

¡Agradecemos las contribuciones! Si quieres contribuir al proyecto, por favor:

1. Haz un fork del repositorio
2. Crea una nueva rama (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Haz push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## 📞 Contacto

Si tienes alguna pregunta o sugerencia, no dudes en contactarnos:

- 📧 Email: support@bqr.com
- 🌐 Sitio web: https://www.bqr.com
- 🐦 Twitter: @bQR_official

---

Hecho con ❤️ por el equipo de bQR
