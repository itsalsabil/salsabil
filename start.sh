#!/bin/bash

# Script de démarrage pour Render.com

echo "🚀 Démarrage de l'application Salsabil..."

# Créer les dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p static/uploads
mkdir -p static/convocations
mkdir -p static/acceptances
mkdir -p uploads

# Initialiser la base de données si nécessaire
echo "🗄️  Initialisation de la base de données..."
python -c "from database import init_db; init_db()"

echo "✅ Configuration terminée!"
echo "🌐 Démarrage du serveur..."

# Lancer l'application avec Gunicorn
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
