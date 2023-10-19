# Usa una imagen base de Python
FROM python:3.10.4

# Establece el directorio de trabajo en la imagen
WORKDIR /app

# Copia los archivos de requerimientos y los instala
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py migrate

# Copia el código fuente de tu aplicación en la imagen
COPY . /app/

# Expone el puerto en el que se ejecutará la aplicación
EXPOSE 8000

# Define el comando para ejecutar la aplicación
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
