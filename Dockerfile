# Utiliza una imagen de Python con Alpine Linux ya que es más ligera
FROM python:3.9

# Establece un directorio de trabajo
WORKDIR /app

# Copia el archivo de requerimientos a la imagen
COPY requirements.txt .

RUN pip install --upgrade pip
# Instala los requerimientos de la aplicación
RUN pip install -r requirements.txt

# Copia el resto de los archivos de la aplicación a la imagen
COPY . .

# Comando para iniciar la aplicación
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000", "webesfm:app", "--access-logfile", "-", "--error-logfile", "-"]

