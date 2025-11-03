#!/bin/bash
# Script de déploiement rapide sur Render.com

echo "🚀 Déploiement sur Render.com"
echo "=============================="
echo ""

# Afficher le statut git
echo "📊 Statut actuel:"
git status --short
echo ""

# Demander confirmation
echo "⚠️  Voulez-vous déployer ces changements sur Render ? (y/n)"
read -r confirm

if [ "$confirm" != "y" ]; then
    echo "❌ Déploiement annulé"
    exit 0
fi

# Ajouter tous les fichiers
echo "📦 Ajout des fichiers..."
git add .

# Demander le message de commit
echo ""
echo "📝 Message de commit (appuyez sur Entrée pour un message par défaut):"
read -r commit_message

if [ -z "$commit_message" ]; then
    commit_message="🔧 Fix: Ajout des logs de debug pour formulaire arabe + Support QR codes + Police Amiri"
fi

# Commit
echo ""
echo "💾 Commit des changements..."
git commit -m "$commit_message"

# Push vers GitHub (qui déclenchera le déploiement Render)
echo ""
echo "🌐 Push vers GitHub..."
git push origin main

# Vérifier le résultat
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Déploiement réussi !"
    echo ""
    echo "📋 Prochaines étapes:"
    echo "   1. Allez sur https://dashboard.render.com"
    echo "   2. Ouvrez votre service 'salsabil'"
    echo "   3. Attendez que le déploiement se termine (≈5 minutes)"
    echo "   4. Consultez les logs en temps réel"
    echo "   5. Testez la soumission du formulaire en arabe"
    echo ""
    echo "🔍 Liens utiles:"
    echo "   - Dashboard: https://dashboard.render.com"
    echo "   - Logs: https://dashboard.render.com/web/[votre-service]/logs"
else
    echo ""
    echo "❌ Erreur lors du push"
    echo "Vérifiez votre connexion GitHub"
fi
