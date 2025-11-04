# file: Dockerfile

# 1. Usa un'immagine ufficiale Python come base.
# Scegliamo una versione snella ("slim") per ridurre le dimensioni.
FROM python:3.11-slim

# 2. Imposta la directory di lavoro all'interno del container
WORKDIR /app

# 3. Copia il file delle dipendenze nel container
COPY requirements.txt .

# 4. Installa le dipendenze
# --no-cache-dir riduce le dimensioni dell'immagine
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia tutto il resto del codice sorgente dell'API nel container
COPY . .

# 6. Esponi la porta su cui girerà l'applicazione (la stessa usata da uvicorn)
EXPOSE 8000

# 7. Comando per avviare l'applicazione quando il container parte
# Uvicorn è il server ASGI che esegue FastAPI.
# --host 0.0.0.0 è fondamentale per rendere l'app accessibile dall'esterno del container.
# --port 8000 è la porta standard.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}