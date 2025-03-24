# Usa una imagen base de Python
FROM python:3.9

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos del proyecto al contenedor
COPY . /app

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto en el que se ejecutará Flask
EXPOSE 5000

# Comando de inicio de la aplicación Flask
CMD ["python", "run.py"]
