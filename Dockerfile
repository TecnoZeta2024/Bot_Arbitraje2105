# Usar una imagen base de Python
FROM python:3.11-slim-buster
# Para fijar la imagen a un digest específico y asegurar la inmutabilidad,
# se puede usar el formato FROM python:3.11-slim-buster@sha256:<digest_hash>.
# El digest_hash se obtiene después de construir y empujar la imagen a un registro.
# Por ejemplo: docker pull python:3.11-slim-buster --platform linux/amd64
# docker inspect --format='{{.RepoDigests}}' python:3.11-slim-buster

# Establecer el directorio de trabajo en /app
WORKDIR /app

# Copiar el archivo de requisitos e instalar las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente de la aplicación
COPY . .

# Exponer los puertos para el servidor de producción (FastAPI) y Streamlit
EXPOSE 8001
EXPOSE 8501

# Comando para iniciar el servidor de producción y el dashboard de Streamlit
# Usamos un script de entrada para manejar ambos procesos
CMD ["bash", "-c", "python src/production_server.py & streamlit run streamlit_dashboash.py --server.port 8501 --server.address 0.0.0.0"]
