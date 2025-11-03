#!/usr/bin/env bash
# exit on error
set -o errexit

# Force Python 3.11 pour compatibilité psycopg2
export PYTHON_VERSION=3.11.9

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Initialiser la base de données PostgreSQL
echo "Initialisation de la base de données..."
python database.py

echo "✅ Build terminé avec succès!"
