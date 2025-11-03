#!/bin/bash

# Script pour redémarrer l'application et voir les logs

echo "🔄 Arrêt des instances existantes de l'application..."

# Trouver et tuer tous les processus python app.py
pkill -f "python.*app.py"

sleep 2

echo "✅ Instances arrêtées"
echo ""
echo "🚀 Démarrage de l'application en mode debug..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Démarrer l'application
cd /Users/mohamedabdallah/Desktop/Salsabil
python3 app.py

# Les logs apparaîtront ici en temps réel
