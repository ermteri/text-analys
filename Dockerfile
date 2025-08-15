FROM python:3.10-slim

# Skapa en användare
RUN useradd -m appuser

# Ange arbetskatalog
WORKDIR /home/appuser/app

# Kopiera kod
COPY . .

# Installera beroenden
RUN pip install --no-cache-dir -r requirements.txt

# Ladda modell som root till /home/appuser/app/stanza_resources
RUN mkdir -p /home/appuser/app/stanza_resources && \
    python3 -c "import stanza; stanza.download('sv', model_dir='/home/appuser/app/stanza_resources')"

# Ändra ägarskap till appuser (viktig detalj)
RUN chown -R appuser:appuser /home/appuser/app

# Ange miljövariabel
ENV STANZA_RESOURCES_DIR=/home/appuser/app/stanza_resources

# Växla till användaren
USER appuser

CMD ["python", "app.py"]

