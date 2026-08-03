FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ unixodbc-dev gnupg2 curl apt-transport-https && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 && rm -rf /var/lib/apt/lists/*
COPY contentflow-lib /app/contentflow-lib
WORKDIR /app/contentflow-lib
RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir pyodbc
WORKDIR /app/contentflow-api
COPY contentflow-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY contentflow-api/ .
ENV PYTHONUNBUFFERED=1
ENV API_SERVER_HOST=0.0.0.0
ENV API_SERVER_PORT=8090
EXPOSE 8090
CMD ["python", "main.py"]