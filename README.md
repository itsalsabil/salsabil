# 🚀 Salsabil - Système de Gestion de Recrutement

## 📋 Description
Application web Flask complète pour la gestion de recrutement avec :
- Interface publique pour les candidats
- Dashboard administratif avec système de permissions
- Base de données SQLite
- Gestion automatique des fichiers
- Système de rôles et permissions (Admin, HR, Recruteur)

## ⚡ Installation Rapide

### 1. Prérequis
- Python 3.7+
- pip

### 2. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 3. Initialiser la base de données
```bash
python3 database.py
```

### 4. Lancer l'application
```bash
python3 app.py
```

L'application sera accessible à : **http://127.0.0.1:5000/**

## 🌐 URLs Principales

### Interface Publique
- **Page d'accueil :** `/`
- **Offres d'emploi :** `/jobs`
- **Postuler :** `/apply/[job_id]`
- **Candidature spontanée :** `/apply/0`

### Interface Admin
- **Login :** `/admin/login`
- **Dashboard :** `/admin/dashboard`
- **Gestion des jobs :** `/admin/jobs`
- **Candidatures :** `/admin/applications`
- **Employés :** `/admin/employees` (Admin seulement)
- **Mon Profil :** `/admin/profile`

## 👥 Comptes par Défaut

| Username  | Password | Rôle      | Permissions |
|-----------|----------|-----------|-------------|
| admin     | admin123 | Admin     | Accès complet |
| hr        | hr123    | HR        | Jobs + Candidatures |
| recruteur | rec123   | Recruteur | Lecture seule |

⚠️ **Changez ces mots de passe en production !**

## 📁 Structure du Projet

```
Salsabil/
├── app.py                      # Application Flask principale
├── database.py                 # Configuration base de données
├── models.py                   # Fonctions CRUD + gestion fichiers
├── salsabil.db                 # Base de données SQLite
├── requirements.txt            # Dépendances Python
├── .gitignore                  # Fichiers ignorés par git
│
├── static/
│   ├── css/
│   │   ├── style.css          # Styles interface publique
│   │   └── admin.css          # Styles dashboard admin
│   └── uploads/                # 📂 Fichiers uploadés
│
├── templates/
│   ├── jobs.html              # Liste des offres
│   ├── apply.html             # Formulaire candidature
│   └── admin/
│       ├── login.html         # Login admin
│       ├── dashboard.html     # Dashboard principal
│       ├── jobs.html          # Gestion offres
│       ├── applications.html  # Liste candidatures
│       ├── application_detail.html  # Détails candidature
│       ├── employees.html     # Gestion employés
│       ├── job_candidates.html  # Candidats par offre
│       └── profile.html       # Profil utilisateur
│
├── 📚 Documentation/
│   ├── IDENTIFIANTS.md        # Comptes et accès
│   ├── README_DATABASE.md     # Documentation base de données
│   ├── README_ADMIN.md        # Guide admin
│   ├── README_EMPLOYEES.md    # Guide gestion employés
│   ├── README_FILE_DELETION.md # Suppression automatique fichiers
│   ├── MIGRATION_NOTES.md     # Notes de migration
│   └── RECAP_FILE_DELETION.md # Récap suppression fichiers
│
└── 🧪 Tests/
    ├── test_database.py       # Tests base de données
    └── test_file_deletion.py  # Tests suppression fichiers
```

## ✨ Fonctionnalités Principales

### Interface Publique
- ✅ Liste des offres d'emploi actives
- ✅ Détails de chaque offre
- ✅ Formulaire de candidature complet
- ✅ Candidature spontanée (job_id = 0)
- ✅ Upload de documents (CV, lettre, diplôme, etc.)
- ✅ Menu dropdown "Qui sommes-nous" avec liens
- ✅ Design responsive (mobile/desktop)

### Dashboard Admin
- ✅ Statistiques en temps réel (4 cartes)
- ✅ Gestion complète des offres d'emploi (CRUD)
- ✅ Gestion des candidatures avec statuts
- ✅ Détails complets de chaque candidature
- ✅ Prévisualisation des documents uploadés
- ✅ Système de permissions par rôle
- ✅ Gestion des employés (Admin uniquement)
- ✅ Profil utilisateur (changement mot de passe)

### Base de Données
- ✅ SQLite pour persistance des données
- ✅ 3 tables : employees, jobs, applications
- ✅ Relations entre tables
- ✅ Fonctions CRUD complètes

### Gestion des Fichiers
- ✅ Upload sécurisé dans `static/uploads/`
- ✅ **Suppression automatique lors de la suppression**
- ✅ Support de plusieurs formats (PDF, images)
- ✅ Prévisualisation dans l'admin

## 🔒 Système de Permissions

### Admin (Rôle: admin)
- ✅ Gestion des employés (ajouter, modifier, supprimer)
- ✅ Gestion des offres d'emploi (toutes actions)
- ✅ Gestion des candidatures (toutes actions)
- ✅ Accès au profil

### HR (Rôle: hr)
- ❌ Gestion des employés
- ✅ Gestion des offres d'emploi (ajouter, modifier)
- ✅ Gestion des candidatures (toutes actions)
- ✅ Accès au profil

### Recruteur (Rôle: recruteur)
- ❌ Gestion des employés
- ❌ Gestion des offres d'emploi
- ✅ Consultation des candidatures (lecture seule)
- ✅ Accès au profil

## 🧪 Tests

### Tester la base de données
```bash
python3 test_database.py
```
Tests : Employés, Jobs, Candidatures, Statistiques, Profil

### Tester la suppression de fichiers
```bash
python3 test_file_deletion.py
```
Tests : Suppression candidature, Suppression job (cascade)

## 🛠️ Commandes Utiles

### Réinitialiser la base de données
```bash
python3 database.py
```

### Accéder à la base de données SQLite
```bash
sqlite3 salsabil.db
```

### Vérifier les tables
```sql
.tables
SELECT * FROM employees;
SELECT * FROM jobs;
SELECT * FROM applications;
```

## 📚 Documentation Complète

- **IDENTIFIANTS.md** - Comptes et permissions
- **README_DATABASE.md** - Structure et requêtes SQL
- **README_ADMIN.md** - Guide utilisation admin
- **README_EMPLOYEES.md** - Gestion des employés
- **README_FILE_DELETION.md** - Suppression automatique
- **MIGRATION_NOTES.md** - Migration vers SQLite
- **RECAP_FILE_DELETION.md** - Récap fonctionnalité

## 🎯 Fonctionnalités Récentes

### ✅ Suppression Automatique des Fichiers
Lorsqu'une candidature ou un job est supprimé, **tous les fichiers associés sont automatiquement supprimés du système de fichiers**.

**Fichiers concernés :**
- Photo d'identité
- CV
- Lettre de demande
- Carte d'identité
- Lettre de recommandation
- Casier judiciaire
- Diplôme

**Tests réussis :** ✅ Tous les tests passent

## 🚨 Important pour la Production

### Sécurité
1. ⚠️ **Changer tous les mots de passe par défaut**
2. ⚠️ **Hasher les mots de passe** avec `werkzeug.security`
3. ⚠️ **Configurer SECRET_KEY** dans Flask
4. ⚠️ **Utiliser HTTPS**
5. ⚠️ **Limiter les tentatives de connexion**

### Backup
- 💾 Sauvegarder régulièrement `salsabil.db`
- 💾 Sauvegarder le dossier `static/uploads/`
- 💾 Les fichiers sont supprimés **définitivement** (pas de corbeille)

### Performance
- 🚀 Considérer PostgreSQL/MySQL pour grande échelle
- 🚀 Optimiser les requêtes SQL
- 🚀 Mettre en cache les statistiques

## 🐛 Dépannage

### Base de données verrouillée
```bash
# Arrêter l'application et réinitialiser
python3 database.py
```

### Fichiers non supprimés
```bash
# Vérifier les permissions du dossier uploads
chmod 755 static/uploads/
```

### Problèmes de connexion
- Vérifier les identifiants dans `IDENTIFIANTS.md`
- Réinitialiser la base de données si nécessaire

## 📞 Support

Pour toute question :
1. Consultez la documentation dans le dossier racine
2. Exécutez les scripts de test
3. Vérifiez les logs dans la console

## 📝 License

Projet privé - Tous droits réservés

---

## 🌐 Déploiement

### Déploiement sur Render.com

Consultez le guide complet de déploiement : **[DEPLOYMENT.md](DEPLOYMENT.md)**

**Résumé rapide :**

1. **Préparer le repository Git** :
```bash
git init
git add .
git commit -m "Préparer pour déploiement"
git push
```

2. **Créer un service sur Render.com** :
   - Connecter votre repository
   - Configurer les variables d'environnement
   - Déployer automatiquement

3. **Variables d'environnement requises** :
   - `SECRET_KEY` : Clé secrète Flask (générée automatiquement)
   - `FLASK_ENV` : `production`
   - `DEBUG` : `False`

4. **Accéder à votre application** :
   - URL : `https://votre-app.onrender.com`

📖 **Guide détaillé complet** : [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Version :** 2.0.0  
**Date :** 13 Octobre 2025  
**Auteur :** Équipe Salsabil

🎉 **Application 100% fonctionnelle et prête pour le déploiement !**
