#!/bin/bash

# Script d'aide pour Git et déploiement
# Usage: bash git_deploy.sh

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       🚀 SCRIPT DE DÉPLOIEMENT - SALSABIL RH             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier si Git est installé
if ! command -v git &> /dev/null; then
    echo "❌ Git n'est pas installé. Installez-le d'abord."
    exit 1
fi

echo "1️⃣  Vérification des fichiers..."

# Vérifier que les fichiers importants existent
files=("requirements.txt" "Procfile" "runtime.txt" "start.sh" "app.py")
missing_files=()

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (MANQUANT)"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo ""
    echo "❌ Fichiers manquants détectés. Impossible de continuer."
    exit 1
fi

echo ""
echo "2️⃣  État du repository Git..."

# Vérifier si Git est initialisé
if [ ! -d ".git" ]; then
    echo "   📁 Git n'est pas initialisé. Initialisation..."
    git init
    echo "   ✅ Git initialisé"
else
    echo "   ✅ Git déjà initialisé"
fi

# Afficher le statut
echo ""
echo "   📊 Statut actuel :"
git status --short

echo ""
echo "3️⃣  Configuration Git..."

# Vérifier si l'email et le nom sont configurés
if ! git config user.email > /dev/null 2>&1; then
    echo "   ⚙️  Configuration de Git..."
    read -p "   Entrez votre email Git : " git_email
    read -p "   Entrez votre nom : " git_name
    git config user.email "$git_email"
    git config user.name "$git_name"
    echo "   ✅ Configuration Git sauvegardée"
else
    echo "   ✅ Git déjà configuré"
    echo "      Email : $(git config user.email)"
    echo "      Nom   : $(git config user.name)"
fi

echo ""
echo "4️⃣  Ajout des fichiers..."

# Ajouter tous les fichiers
git add .
echo "   ✅ Tous les fichiers ajoutés"

echo ""
echo "5️⃣  Commit..."

# Demander le message de commit
default_message="Préparer application pour déploiement sur Render"
read -p "   Message de commit [$default_message] : " commit_message
commit_message=${commit_message:-$default_message}

git commit -m "$commit_message"
echo "   ✅ Commit créé"

echo ""
echo "6️⃣  Configuration du remote..."

# Vérifier si un remote existe
if git remote get-url origin > /dev/null 2>&1; then
    echo "   ✅ Remote déjà configuré : $(git remote get-url origin)"
    read -p "   Voulez-vous changer l'URL du remote ? (o/N) : " change_remote
    if [[ $change_remote =~ ^[Oo]$ ]]; then
        read -p "   Nouvelle URL du repository : " repo_url
        git remote set-url origin "$repo_url"
        echo "   ✅ Remote mis à jour"
    fi
else
    echo "   ⚠️  Aucun remote configuré"
    read -p "   URL du repository (ex: https://github.com/user/repo.git) : " repo_url
    if [ -n "$repo_url" ]; then
        git remote add origin "$repo_url"
        echo "   ✅ Remote ajouté"
    else
        echo "   ⚠️  Aucun remote configuré. Vous devrez le faire manuellement."
        echo "   Commande : git remote add origin URL"
        exit 0
    fi
fi

echo ""
echo "7️⃣  Push vers le repository..."

# Déterminer la branche
current_branch=$(git branch --show-current)
if [ -z "$current_branch" ]; then
    current_branch="main"
    git branch -M main
fi

echo "   📤 Push vers la branche : $current_branch"
read -p "   Continuer ? (O/n) : " do_push
if [[ ! $do_push =~ ^[Nn]$ ]]; then
    git push -u origin "$current_branch"
    echo "   ✅ Code poussé vers le repository"
else
    echo "   ⏭️  Push ignoré"
    echo "   Pour pousser manuellement : git push -u origin $current_branch"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   ✅ TERMINÉ !                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Prochaines étapes :"
echo ""
echo "1. Allez sur https://dashboard.render.com"
echo "2. Cliquez sur 'New +' → 'Web Service'"
echo "3. Connectez votre repository"
echo "4. Configurez les variables d'environnement :"
echo "   - SECRET_KEY (généré automatiquement)"
echo "   - FLASK_ENV=production"
echo "   - DEBUG=False"
echo "5. Déployez !"
echo ""
echo "📚 Guide complet : DEPLOYMENT.md"
echo "✅ Checklist : DEPLOYMENT_CHECKLIST.md"
echo ""
echo "🎉 Bonne chance avec votre déploiement !"
