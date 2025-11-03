from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import json
import zipfile
import io
from dotenv import load_dotenv
# Importer les fonctions de la base de données
from models import *
from database import init_db

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'b61a18f9ef47065d7cf7d69431e48771')  # Utilisez une vraie clé en production

# Initialiser la base de données au démarrage
init_db()

# Configuration pour l'upload de fichiers
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Créer le dossier uploads s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Définition des permissions par rôle
ROLE_PERMISSIONS = {
    'admin': {
        'view_dashboard': True,
        'view_jobs': True,
        'add_job': True,
        'edit_job': True,
        'delete_job': True,
        'view_applications': True,
        'edit_application': True,
        'delete_application': True,
        'view_employees': True,
        'add_employee': True,
        'edit_employee': True,
        'delete_employee': True
    },
    'hr': {
        'view_dashboard': True,
        'view_jobs': True,
        'add_job': True,
        'edit_job': True,
        'delete_job': False,
        'view_applications': True,
        'edit_application': True,
        'delete_application': True,
        'view_employees': False,
        'add_employee': False,
        'edit_employee': False,
        'delete_employee': False
    },
    'recruteur': {
        'view_dashboard': True,
        'view_jobs': True,
        'add_job': False,
        'edit_job': False,
        'delete_job': False,
        'view_applications': True,
        'edit_application': True,
        'delete_application': False,
        'view_employees': False,
        'add_employee': False,
        'edit_employee': False,
        'delete_employee': False
    }
}

def is_closing_soon(deadline_str):
    """Vérifie si la date limite est dans moins de 7 jours"""
    # Gérer à la fois les strings (SQLite) et les objets date (PostgreSQL)
    if isinstance(deadline_str, str):
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
    else:
        # C'est déjà un objet date/datetime (PostgreSQL)
        deadline = datetime.combine(deadline_str, datetime.min.time()) if hasattr(deadline_str, 'year') else deadline_str
    
    today = datetime.now()
    days_remaining = (deadline - today).days
    return days_remaining <= 7 and days_remaining >= 0

def allowed_file(filename):
    """Vérifie si le fichier a une extension autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user():
    """Récupère l'utilisateur actuellement connecté"""
    if 'user_id' in session:
        return get_employee_by_id(session['user_id'])
    return None

def has_permission(permission):
    """Vérifie si l'utilisateur actuel a une permission spécifique
    Si permission est None, retourne toutes les permissions de l'utilisateur"""
    user = get_current_user()
    if not user:
        return {} if permission is None else False
    
    user_permissions = ROLE_PERMISSIONS.get(user['role'], {})
    
    if permission is None:
        # Retourner toutes les permissions
        return user_permissions
    else:
        # Retourner une permission spécifique
        return user_permissions.get(permission, False)

def permission_required(permission):
    """Décorateur pour vérifier une permission spécifique"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                flash('Veuillez vous connecter', 'error')
                return redirect(url_for('admin_login'))
            if not has_permission(permission):
                flash('Vous n\'avez pas la permission d\'accéder à cette ressource', 'error')
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def login_required(f):
    """Décorateur pour protéger les routes admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Veuillez vous connecter', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_redirect_with_lang(route_name, **kwargs):
    """Redirige vers une route en préservant la langue"""
    lang = session.get('lang', 'fr')
    
    # Si la route a une version arabe et qu'on est en arabe
    if lang == 'ar' and not route_name.endswith('_ar'):
        ar_route = route_name + '_ar'
        # Vérifier si la route arabe existe
        try:
            return redirect(url_for(ar_route, **kwargs))
        except:
            # Si pas de version arabe, utiliser la version normale
            pass
    
    return redirect(url_for(route_name, **kwargs))

@app.route('/')
def home():
    """Route pour la page d'accueil - affiche directement les postes disponibles"""
    from models import are_spontaneous_applications_open
    return render_template('jobs.html', 
                         jobs=get_all_jobs(), 
                         is_closing_soon=is_closing_soon,
                         spontaneous_open=are_spontaneous_applications_open())

@app.route('/jobs')
def jobs():
    """Route pour afficher tous les postes disponibles"""
    from models import are_spontaneous_applications_open
    jobs = get_all_jobs()
    return render_template('jobs.html', 
                         jobs=jobs, 
                         is_closing_soon=is_closing_soon,
                         spontaneous_open=are_spontaneous_applications_open())

@app.route('/jobs_ar')
def jobs_ar():
    """Route pour afficher tous les postes disponibles en arabe"""
    from models import are_spontaneous_applications_open
    jobs = get_all_jobs()
    return render_template('jobs_ar.html', 
                         jobs=jobs, 
                         is_closing_soon=is_closing_soon,
                         spontaneous_open=are_spontaneous_applications_open())

@app.route('/jobs/<int:job_id>')
def job_detail(job_id):
    """Route pour afficher les détails d'un poste spécifique"""
    job = get_job_by_id(job_id)
    if job is None:
        flash('Poste non trouvé', 'error')
        return redirect(url_for('jobs'))
    return render_template('job_detail.html', job=job)

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply(job_id):
    """Route pour postuler à un poste"""
    from models import are_spontaneous_applications_open, get_spontaneous_status_message
    
    # Gérer les candidatures spontanées (job_id = 0)
    if job_id == 0:
        # Vérifier si les candidatures spontanées sont ouvertes
        if not are_spontaneous_applications_open():
            status_msg = get_spontaneous_status_message('fr')
            flash(status_msg['message'], 'warning')
            return render_template('jobs.html', 
                                 jobs=get_all_jobs(), 
                                 is_closing_soon=is_closing_soon,
                                 spontaneous_closed=True,
                                 spontaneous_message=status_msg)
        
        job = {
            'id': 0,
            'titre': 'Candidature Spontanée',
            'title': 'Candidature Spontanée',
            'type': 'Variable',
            'lieu': 'Toutes nos agences',
            'location': 'Toutes nos agences',
            'description': 'Nous sommes toujours à la recherche de nouveaux talents ! Envoyez-nous votre candidature spontanée.',
            'deadline': '2026-12-31',
            'posted_date': '2025-01-01',
            'department': 'Tous les départements',
            'requirements': []
        }
    else:
        job = get_job_by_id(job_id)
        if job is None:
            flash('Poste non trouvé', 'error')
            return redirect(url_for('jobs'))
    
    if request.method == 'POST':
        # 🔍 DEBUG CRITIQUE: Logs IMMEDIATS
        print("\n" + "="*80)
        print("🚨 POST REQUEST RECEIVED - DEBUT DU TRAITEMENT")
        print("="*80)
        print(f"📍 URL: {request.url}")
        print(f"📍 Path: {request.path}")
        print(f"📍 Method: {request.method}")
        print(f"📍 Content-Type: {request.content_type}")
        print(f"📍 Content-Length: {request.content_length}")
        print(f"📍 Form keys: {list(request.form.keys())[:20]}")  # Premier 20 clés
        print(f"📍 Files keys: {list(request.files.keys())}")
        print(f"📍 Headers: {dict(request.headers)}")
        print("="*80 + "\n")
        
        print("📝 Réception d'une candidature...")
        print(f"   Job ID: {job_id}")
        print(f"   Job titre: {job.get('titre', 'N/A')}")
        
        # 🔍 DEBUG: Afficher toutes les données du formulaire
        print("\n🔍 DEBUG - Données du formulaire reçues:")
        print(f"   Content-Type: {request.content_type}")
        print(f"   Nombre de champs form: {len(request.form)}")
        print(f"   Nombre de fichiers: {len(request.files)}")
        
        if len(request.form) > 0:
            print("   📋 Champs du formulaire:")
            for key in list(request.form.keys())[:10]:  # Afficher les 10 premiers
                value = request.form.get(key)
                print(f"      - {key}: {value[:50] if value and len(value) > 50 else value}")
        else:
            print("   ⚠️  ATTENTION: request.form est VIDE!")
            print(f"   📊 Tentative de récupération alternative...")
            print(f"      - request.data: {request.data[:200] if request.data else 'Vide'}")
            print(f"      - request.get_json(): {request.get_json(silent=True)}")
            
            # Si request.form est vide, on ne peut pas continuer
            if len(request.form) == 0 and len(request.files) == 0:
                print("   ❌ ERREUR CRITIQUE: Aucune donnée reçue du formulaire!")
                flash('Erreur: Les données du formulaire n\'ont pas été reçues. Veuillez réessayer.', 'error')
                return render_template('apply.html', job=job)
            
        if len(request.files) > 0:
            print("   📎 Fichiers uploadés:")
            for key in request.files.keys():
                file = request.files[key]
                print(f"      - {key}: {file.filename if file.filename else 'Aucun fichier'}")
        print()
        
        try:
            # Traiter les fichiers uploadés
            uploaded_files = {}
            files_to_upload = ['photo', 'cv', 'lettre_demande', 'carte_id', 
                             'lettre_recommandation', 'casier_judiciaire', 'diplome']
            
            print("📎 Traitement des fichiers...")
            for file_field in files_to_upload:
                file = request.files.get(file_field)
                if file and file.filename and allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"{timestamp}_{file_field}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    uploaded_files[file_field] = filename
                    print(f"   ✓ {file_field}: {filename}")
                else:
                    uploaded_files[file_field] = None
                    print(f"   ✗ {file_field}: Non fourni")
            
            # Gérer la lettre de demande : textarea OU fichier uploadé
            lettre_demande_value = None
            if uploaded_files.get('lettre_demande'):
                # Fichier uploadé
                lettre_demande_value = uploaded_files.get('lettre_demande')
                print(f"   📄 Lettre de demande: fichier {lettre_demande_value}")
            else:
                # Texte du textarea
                lettre_demande_text = request.form.get('lettre_demande_text', '').strip()
                if lettre_demande_text:
                    lettre_demande_value = lettre_demande_text
                    print(f"   📝 Lettre de demande: texte saisi ({len(lettre_demande_text)} caractères)")
                else:
                    print(f"   ℹ️  Lettre de demande: non fournie (optionnelle)")
            
            print("💾 Création de la candidature...")
            
            # Gérer les choix de travail (pour candidature spontanée)
            choix_travail = None
            if job_id == 0:  # Candidature spontanée
                choix_travail_list = request.form.getlist('choix_travail')
                if 'Autre' in choix_travail_list:
                    autre_precision = request.form.get('autre_travail_precision', '').strip()
                    if autre_precision:
                        # Remplacer "Autre" par la précision
                        choix_travail_list = [c if c != 'Autre' else f'Autre: {autre_precision}' for c in choix_travail_list]
                choix_travail = ', '.join(choix_travail_list) if choix_travail_list else None
                print(f"   💼 Choix de travail: {choix_travail}")
            
            # Utiliser 'titre' ou 'title' selon ce qui est disponible
            job_title_value = job.get('titre') or job.get('title') or 'Candidature Spontanée'
            print(f"   Job title utilisé: {job_title_value}")
            
            # Créer la candidature dans la base de données
            app_id = create_application(
                job_id=None if job_id == 0 else job_id,  # NULL pour candidatures spontanées
                job_title=job_title_value,
                prenom=request.form.get('prenom'),
                nom=request.form.get('nom'),
                email=request.form.get('email'),
                telephone=request.form.get('telephone'),
                adresse=request.form.get('adresse'),
                pays=request.form.get('pays'),
                region=request.form.get('region'),
                sexe=request.form.get('sexe') or None,
                lieu_naissance=request.form.get('lieu_naissance') or None,
                date_naissance=request.form.get('date_naissance') or None,
                nationalite=request.form.get('nationalite') or None,
                etat_civil=request.form.get('etat_civil') or None,
                travaille_actuellement=request.form.get('travaille_actuellement') or None,
                dernier_lieu_travail=request.form.get('dernier_lieu_travail') or None,
                raison_depart=request.form.get('raison_depart') or None,
                niveau_instruction=request.form.get('niveau_instruction') or None,
                specialisation=request.form.get('specialisation') or None,
                specialisation_autre=request.form.get('specialisation_autre') or None,
                langue_arabe=request.form.get('langue_arabe') or None,
                langue_anglaise=request.form.get('langue_anglaise') or None,
                langue_francaise=request.form.get('langue_francaise') or None,
                autre_langue_nom=request.form.get('autre_langue_nom') or None,
                autre_langue_niveau=request.form.get('autre_langue_niveau') or None,
                problemes_sante=request.form.get('problemes_sante') or None,
                nature_maladie=request.form.get('nature_maladie') or None,
                choix_travail=choix_travail,
                photo=uploaded_files.get('photo'),
                cv=uploaded_files.get('cv'),
                lettre_demande=lettre_demande_value,
                carte_id=uploaded_files.get('carte_id'),
                lettre_recommandation=uploaded_files.get('lettre_recommandation'),
                casier_judiciaire=uploaded_files.get('casier_judiciaire'),
                diplome=uploaded_files.get('diplome')
            )
            
            print(f"✅ Candidature créée avec succès! ID: {app_id}")
            # Rediriger vers la page de confirmation avec les détails
            return redirect(url_for('confirmation', 
                                  job_title=job_title_value,
                                  candidate_name=f"{request.form.get('prenom', '')} {request.form.get('nom', '')}",
                                  candidate_email=request.form.get('email', ''),
                                  reference_number=app_id))
            
        except Exception as e:
            print(f"❌ ERREUR lors de la création de la candidature: {str(e)}")
            print(f"   Type d'erreur: {type(e).__name__}")
            import traceback
            print("Détails complets de l'erreur:")
            traceback.print_exc()
            flash(f'Une erreur est survenue lors de l\'envoi de votre candidature. Veuillez réessayer.', 'error')
            return render_template('apply.html', job=job)
    
    return render_template('apply.html', job=job)

@app.route('/apply_ar/<int:job_id>', methods=['GET', 'POST'])
def apply_ar(job_id):
    """Route pour postuler à un poste en arabe"""
    from models import are_spontaneous_applications_open, get_spontaneous_status_message
    
    # Gérer les candidatures spontanées (job_id = 0)
    if job_id == 0:
        # Vérifier si les candidatures spontanées sont ouvertes
        if not are_spontaneous_applications_open():
            status_msg = get_spontaneous_status_message('ar')
            flash(status_msg['message'], 'warning')
            return render_template('jobs_ar.html', 
                                 jobs=get_all_jobs(), 
                                 is_closing_soon=is_closing_soon,
                                 spontaneous_closed=True,
                                 spontaneous_message=status_msg)
        
        job = {
            'id': 0,
            'titre': 'طلب توظيف عفوي',
            'title': 'طلب توظيف عفوي',
            'type': 'متغير',
            'lieu': 'جميع فروعنا',
            'location': 'جميع فروعنا',
            'description': 'نحن نبحث دائمًا عن مواهب جديدة! أرسل لنا طلبك العفوي.',
            'deadline': '2026-12-31',
            'posted_date': '2025-01-01',
            'department': 'جميع الأقسام',
            'requirements': []
        }
    else:
        job = get_job_by_id(job_id)
        if job is None:
            flash('لم يتم العثور على الوظيفة', 'error')
            return redirect(url_for('jobs_ar'))
    
    if request.method == 'POST':
        # 🔍 DEBUG CRITIQUE: Logs IMMEDIATS (VERSION ARABE)
        print("\n" + "="*80)
        print("🚨 POST REQUEST RECEIVED (ARABIC) - بداية المعالجة")
        print("="*80)
        print(f"📍 URL: {request.url}")
        print(f"📍 Path: {request.path}")
        print(f"📍 Method: {request.method}")
        print(f"📍 Content-Type: {request.content_type}")
        print(f"📍 Content-Length: {request.content_length}")
        print(f"📍 Form keys: {list(request.form.keys())[:20]}")  # Premier 20 clés
        print(f"📍 Files keys: {list(request.files.keys())}")
        print(f"📍 Headers: {dict(request.headers)}")
        print("="*80 + "\n")
        
        print("📝 استقبال طلب توظيف...")
        print(f"   Job ID: {job_id}")
        print(f"   Job titre: {job.get('titre', 'N/A')}")
        print(f"   Job title: {job.get('title', 'N/A')}")
        
        # 🔍 DEBUG: Afficher toutes les données du formulaire
        print("\n🔍 DEBUG - بيانات النموذج المستلمة:")
        print(f"   Content-Type: {request.content_type}")
        print(f"   Nombre de champs form: {len(request.form)}")
        print(f"   Nombre de fichiers: {len(request.files)}")
        
        if len(request.form) > 0:
            print("   📋 حقول النموذج:")
            for key in list(request.form.keys())[:10]:  # Afficher les 10 premiers
                value = request.form.get(key)
                print(f"      - {key}: {value[:50] if value and len(value) > 50 else value}")
        else:
            print("   ⚠️  تحذير: request.form فارغ!")
            print(f"   📊 محاولة استرداد بديلة...")
            print(f"      - request.data: {request.data[:200] if request.data else 'فارغ'}")
            print(f"      - request.get_json(): {request.get_json(silent=True)}")
            
            # Si request.form est vide, on ne peut pas continuer
            if len(request.form) == 0 and len(request.files) == 0:
                print("   ❌ خطأ حرج: لم يتم استلام أي بيانات من النموذج!")
                flash('خطأ: لم يتم استلام بيانات النموذج. الرجاء المحاولة مرة أخرى.', 'error')
                return render_template('apply_ar.html', job=job)
        
        if len(request.files) > 0:
            print("   📎 الملفات المرفوعة:")
            for key in request.files.keys():
                file = request.files[key]
                print(f"      - {key}: {file.filename if file.filename else 'لا يوجد ملف'}")
        print()
        
        try:
            # Même traitement que apply()
            uploaded_files = {}
            files_to_upload = ['photo', 'cv', 'lettre_demande', 'carte_id', 
                             'lettre_recommandation', 'casier_judiciaire', 'diplome']
            
            print("📎 معالجة الملفات...")
            for file_field in files_to_upload:
                file = request.files.get(file_field)
                if file and file.filename and allowed_file(file.filename):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"{timestamp}_{file_field}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    uploaded_files[file_field] = filename
                    print(f"   ✓ {file_field}: {filename}")
                else:
                    uploaded_files[file_field] = None
            
            # Gérer la lettre de demande
            lettre_demande_value = None
            if uploaded_files.get('lettre_demande'):
                lettre_demande_value = uploaded_files.get('lettre_demande')
            else:
                lettre_demande_text = request.form.get('lettre_demande_text', '').strip()
                if lettre_demande_text:
                    lettre_demande_value = lettre_demande_text
            
            # Gérer les choix de travail
            choix_travail = None
            if job_id == 0:
                choix_travail_list = request.form.getlist('choix_travail')
                if 'Autre' in choix_travail_list:
                    autre_precision = request.form.get('autre_travail_precision', '').strip()
                    if autre_precision:
                        choix_travail_list = [c if c != 'Autre' else f'Autre: {autre_precision}' for c in choix_travail_list]
                choix_travail = ', '.join(choix_travail_list) if choix_travail_list else None
            
            # Créer la candidature
            print("💾 Préparation des données de candidature...")
            
            # Utiliser 'titre' ou 'title' selon ce qui est disponible
            job_title_value = job.get('titre') or job.get('title') or 'طلب توظيف عفوي'
            print(f"   Job title utilisé: {job_title_value}")
            
            # Préparer les paramètres pour debug
            application_params = {
                'job_id': None if job_id == 0 else job_id,  # NULL pour candidatures spontanées
                'job_title': job_title_value,
                'prenom': request.form.get('prenom'),
                'nom': request.form.get('nom'),
                'email': request.form.get('email'),
                'telephone': request.form.get('telephone'),
                'adresse': request.form.get('adresse'),
                'pays': request.form.get('pays'),
                'region': request.form.get('region'),
                'sexe': request.form.get('sexe') or None,
                'lieu_naissance': request.form.get('lieu_naissance') or None,
                'date_naissance': request.form.get('date_naissance') or None,
                'nationalite': request.form.get('nationalite') or None,
                'etat_civil': request.form.get('etat_civil') or None,
                'travaille_actuellement': request.form.get('travaille_actuellement') or None,
                'dernier_lieu_travail': request.form.get('dernier_lieu_travail') or None,
                'raison_depart': request.form.get('raison_depart') or None,
                'niveau_instruction': request.form.get('niveau_instruction') or None,
                'specialisation': request.form.get('specialisation') or None,
                'specialisation_autre': request.form.get('specialisation_autre') or None,
                'langue_arabe': request.form.get('langue_arabe') or None,
                'langue_anglaise': request.form.get('langue_anglaise') or None,
                'langue_francaise': request.form.get('langue_francaise') or None,
                'autre_langue_nom': request.form.get('autre_langue_nom') or None,
                'autre_langue_niveau': request.form.get('autre_langue_niveau') or None,
                'problemes_sante': request.form.get('problemes_sante') or None,
                'nature_maladie': request.form.get('nature_maladie') or None,
                'choix_travail': choix_travail,
                'photo': uploaded_files.get('photo'),
                'cv': uploaded_files.get('cv'),
                'lettre_demande': lettre_demande_value,
                'carte_id': uploaded_files.get('carte_id'),
                'lettre_recommandation': uploaded_files.get('lettre_recommandation'),
                'casier_judiciaire': uploaded_files.get('casier_judiciaire'),
                'diplome': uploaded_files.get('diplome')
            }
            
            print("   Paramètres de candidature:")
            for key, value in application_params.items():
                if value:
                    print(f"      {key}: {str(value)[:50]}...")
            
            app_id = create_application(**application_params)
            
            print(f"✅ تم إنشاء الطلب بنجاح! ID: {app_id}")
            # الانتقال إلى صفحة التأكيد مع التفاصيل
            return redirect(url_for('confirmation_ar', 
                                  job_title=job_title_value,
                                  candidate_name=f"{request.form.get('prenom', '')} {request.form.get('nom', '')}",
                                  candidate_email=request.form.get('email', ''),
                                  reference_number=app_id))
            
        except Exception as e:
            print(f"❌ خطأ أثناء إنشاء الطلب: {str(e)}")
            print(f"   نوع الخطأ: {type(e).__name__}")
            import traceback
            print("التفاصيل الكاملة للخطأ:")
            traceback.print_exc()
            flash(f'حدث خطأ أثناء إرسال طلبك. الرجاء المحاولة مرة أخرى.', 'error')
            return render_template('apply_ar.html', job=job)
    
    return render_template('apply_ar.html', job=job)

# Routes de confirmation
@app.route('/confirmation')
def confirmation():
    """Page de confirmation après envoi de candidature (Français)"""
    from datetime import datetime
    
    job_title = request.args.get('job_title', '')
    candidate_name = request.args.get('candidate_name', '')
    candidate_email = request.args.get('candidate_email', '')
    reference_number = request.args.get('reference_number', '')
    submission_date = datetime.now().strftime('%d/%m/%Y à %H:%M')
    
    return render_template('confirmation.html', 
                         job_title=job_title,
                         candidate_name=candidate_name,
                         candidate_email=candidate_email,
                         reference_number=reference_number,
                         submission_date=submission_date)

@app.route('/confirmation_ar')
def confirmation_ar():
    """Page de confirmation après envoi de candidature (Arabe)"""
    from datetime import datetime
    
    job_title = request.args.get('job_title', '')
    candidate_name = request.args.get('candidate_name', '')
    candidate_email = request.args.get('candidate_email', '')
    reference_number = request.args.get('reference_number', '')
    submission_date = datetime.now().strftime('%d/%m/%Y - %H:%M')
    
    return render_template('confirmation_ar.html', 
                         job_title=job_title,
                         candidate_name=candidate_name,
                         candidate_email=candidate_email,
                         reference_number=reference_number,
                         submission_date=submission_date)

# Routes Admin
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Route pour la connexion des employés"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Chercher l'employé dans la base de données
        employee = get_employee_by_username(username)
        
        if employee and employee['password'] == password and employee['status'] == 'actif':
            session['logged_in'] = True
            session['user_id'] = employee['id']
            session['username'] = employee['username']
            session['role'] = employee['role']
            session['full_name'] = f"{employee['prenom']} {employee['nom']}"
            session['lang'] = 'fr'  # Définir la langue française
            flash(f'Bienvenue {employee["prenom"]} {employee["nom"]}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Identifiants incorrects ou compte désactivé', 'error')
            return render_template('admin/login.html')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Route pour la déconnexion"""
    # Sauvegarder la langue avant de vider la session
    lang = session.get('lang', 'fr')
    session.clear()
    
    if lang == 'ar':
        flash('تم تسجيل الخروج بنجاح', 'success')
        return redirect(url_for('admin_login_ar'))
    else:
        flash('Vous avez été déconnecté avec succès', 'success')
        return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Route pour le dashboard admin"""
    current_user = get_current_user()
    all_applications = get_all_applications()
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0)
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    return render_template('admin/dashboard.html', 
                         applications=regular_applications,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=ROLE_PERMISSIONS.get(current_user['role'], {}),
                         spontaneous_count=spontaneous_count)

@app.route('/admin/applications')
@login_required
@permission_required('view_applications')
def admin_applications():
    """Route pour voir toutes les candidatures (sauf spontanées)"""
    all_applications = get_all_applications()
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0)
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)  # Get all permissions
    return render_template('admin/applications.html', 
                         applications=regular_applications,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count)

@app.route('/admin/spontaneous-applications')
@login_required
@permission_required('view_applications')
def admin_spontaneous_applications():
    """Route pour voir uniquement les candidatures spontanées"""
    from models import are_spontaneous_applications_open
    
    all_applications = get_all_applications()
    # Filtrer uniquement les candidatures spontanées (job_id = 0)
    spontaneous_apps = [app for app in all_applications if app.get('job_id') is None]
    spontaneous_count = len(spontaneous_apps)
    
    current_user = get_current_user()
    permissions = has_permission(None)  # Get all permissions
    
    # Vérifier si les candidatures spontanées sont ouvertes
    is_open = are_spontaneous_applications_open()
    
    return render_template('admin/spontaneous_applications.html', 
                         applications=spontaneous_apps,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         spontaneous_open=is_open,
                         lang='fr')

@app.route('/admin/toggle-spontaneous-applications', methods=['POST'])
@login_required
@permission_required('edit_application')
def admin_toggle_spontaneous():
    """Route pour activer/désactiver les candidatures spontanées"""
    from models import toggle_spontaneous_applications
    
    # Sauvegarder la langue
    lang = session.get('lang', 'fr')
    
    try:
        new_status = toggle_spontaneous_applications()
        
        if new_status:
            if lang == 'ar':
                flash('✅ تم فتح الطلبات العفوية', 'success')
            else:
                flash('✅ Candidatures spontanées ouvertes', 'success')
        else:
            if lang == 'ar':
                flash('🔒 تم إغلاق الطلبات العفوية مؤقتاً', 'info')
            else:
                flash('🔒 Candidatures spontanées fermées temporairement', 'info')
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('admin_spontaneous_applications'))

@app.route('/admin/favorite-applications')
@login_required
@permission_required('view_applications')
def admin_favorite_applications():
    """Route pour voir uniquement les candidatures favorites"""
    from models import get_favorite_applications
    
    # Récupérer uniquement les candidatures favorites
    favorite_apps = get_favorite_applications()
    
    all_applications = get_all_applications()
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)
    
    return render_template('admin/spontaneous_applications.html', 
                         applications=favorite_apps,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         is_favorites_view=True,
                         lang='fr')

@app.route('/admin/spontaneous-applications/<int:app_id>')
@login_required
@permission_required('view_applications')
def admin_spontaneous_application_detail(app_id):
    """Route dédiée pour voir les détails d'une candidature spontanée"""
    all_applications = get_all_applications()
    application = next((app for app in all_applications if app['id'] == app_id), None)
    
    if application is None:
        flash('Candidature non trouvée', 'error')
        return redirect(url_for('admin_spontaneous_applications'))
    
    # Vérifier que c'est bien une candidature spontanée
    if application.get('job_id') is not None:
        flash('Cette candidature n\'est pas une candidature spontanée', 'error')
        return redirect(url_for('admin_applications'))
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0) pour le badge
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)
    
    return render_template('admin/application_detail.html', 
                         application=application, 
                         applications=regular_applications,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         is_spontaneous_view=True)

@app.route('/admin/applications/<int:app_id>')
@login_required
@permission_required('view_applications')
def admin_application_detail(app_id):
    """Route pour voir les détails d'une candidature"""
    all_applications = get_all_applications()
    application = next((app for app in all_applications if app['id'] == app_id), None)
    if application is None:
        flash('Candidature non trouvée', 'error')
        # Rediriger vers la page appropriée selon la source (referrer)
        referrer = request.referrer
        if referrer and 'spontaneous-applications' in referrer:
            return redirect(url_for('admin_spontaneous_applications'))
        return redirect(url_for('admin_applications'))
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0) pour le badge
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)  # Get all permissions
    
    return render_template('admin/application_detail.html', 
                         application=application, 
                         applications=regular_applications,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count)

@app.route('/admin/applications/<int:app_id>/update-status', methods=['POST'])
@login_required
@permission_required('edit_application')
def admin_update_status(app_id):
    """Route pour mettre à jour le statut d'une candidature"""
    
    new_status = request.form.get('status')
    if new_status in ['en attente', 'acceptée', 'rejetée']:
        try:
            update_application_status(app_id, new_status)
            flash(f'Statut mis à jour: {new_status}', 'success')
        except Exception as e:
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
    else:
        flash('Statut invalide', 'error')
    
    return redirect(url_for('admin_application_detail', app_id=app_id))

@app.route('/admin/applications/<int:app_id>/delete', methods=['POST'])
@login_required
@permission_required('delete_application')
def admin_delete_application(app_id):
    """Route pour supprimer une candidature"""
    
    # Sauvegarder la langue actuelle
    lang = session.get('lang', 'fr')
    
    try:
        # Récupérer l'info de la candidature AVANT suppression pour savoir où rediriger
        all_applications = get_all_applications()
        application = next((app for app in all_applications if app['id'] == app_id), None)
        is_spontaneous = application and application.get('job_id') is None
        
        # Supprimer la candidature de la base de données (fichiers inclus)
        delete_application(app_id)
        
        if lang == 'ar':
            flash('تم حذف الطلب بنجاح', 'success')
        else:
            flash('Candidature supprimée avec succès', 'success')
        
        # Rediriger vers la bonne page selon le type
        if is_spontaneous:
            return redirect(url_for('admin_spontaneous_applications'))
        return redirect(url_for('admin_applications'))
    except Exception as e:
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
        # En cas d'erreur, utiliser le referrer pour savoir où revenir
        referrer = request.referrer
        if referrer and 'spontaneous-applications' in referrer:
            return redirect(url_for('admin_spontaneous_applications'))
        return redirect(url_for('admin_applications'))


@app.route('/admin/applications/<int:app_id>/toggle-favorite', methods=['POST'])
@login_required
@permission_required('view_applications')
def admin_toggle_favorite(app_id):
    """Route pour marquer/démarquer une candidature spontanée comme favorite"""
    from models import toggle_favorite
    
    # Sauvegarder la langue actuelle
    lang = session.get('lang', 'fr')
    
    try:
        new_status = toggle_favorite(app_id)
        if new_status is not None:
            if new_status == 1:
                if lang == 'ar':
                    flash('✨ تمت إضافة الطلب إلى المفضلة', 'success')
                else:
                    flash('✨ Candidature ajoutée aux favoris', 'success')
            else:
                if lang == 'ar':
                    flash('تمت إزالة الطلب من المفضلة', 'info')
                else:
                    flash('Candidature retirée des favoris', 'info')
        else:
            if lang == 'ar':
                flash('فقط الطلبات العفوية يمكن إضافتها إلى المفضلة', 'error')
            else:
                flash('Seules les candidatures spontanées peuvent être marquées comme favorites', 'error')
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
    
    # Retour à la page précédente en préservant la langue
    referrer = request.referrer
    if referrer and 'spontaneous-applications' in referrer:
        # Si on vient de la liste spontanée OU de la page détails spontanée
        if f'/spontaneous-applications/{app_id}' in referrer:
            return redirect(url_for('admin_spontaneous_application_detail', app_id=app_id))
        else:
            return redirect(url_for('admin_spontaneous_applications'))
    else:
        # Par défaut, retourner à la page détails spontanée
        return redirect(url_for('admin_spontaneous_application_detail', app_id=app_id))


@app.route('/admin/applications/<int:app_id>/download-all')
@login_required
@permission_required('view_applications')
def admin_download_all_documents(app_id):
    """Route pour télécharger tous les documents d'une candidature en ZIP"""
    
    # Récupérer la candidature
    application = next((app for app in get_all_applications() if app['id'] == app_id), None)
    if application is None:
        flash('Candidature non trouvée', 'error')
        return redirect(url_for('admin_applications'))
    
    # Créer le nom du dossier : Prenom_Nom
    folder_name = f"{application['prenom']}_{application['nom']}"
    # Nettoyer le nom (enlever les caractères spéciaux)
    folder_name = secure_filename(folder_name)
    
    # Créer un fichier ZIP en mémoire
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Liste des champs de documents
        document_fields = [
            ('photo', 'Photo'),
            ('cv', 'CV'),
            ('lettre_demande', 'Lettre_de_Demande'),
            ('carte_id', 'Carte_Identite'),
            ('lettre_recommandation', 'Lettre_Recommandation'),
            ('casier_judiciaire', 'Casier_Judiciaire'),
            ('diplome', 'Diplome')
        ]
        
        documents_added = 0
        
        for field_name, display_name in document_fields:
            filename = application.get(field_name)
            
            # Vérifier si le document existe
            if filename and filename.strip():
                # Gérer le cas où lettre_demande est du texte et non un fichier
                if field_name == 'lettre_demande' and not (filename.endswith('.pdf') or filename.endswith('.doc') or filename.endswith('.docx')):
                    # C'est du texte, créer un fichier texte
                    text_content = filename
                    zipf.writestr(f"{folder_name}/Lettre_de_Demande.txt", text_content)
                    documents_added += 1
                else:
                    # C'est un fichier, l'ajouter au ZIP
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    if os.path.exists(file_path):
                        # Obtenir l'extension du fichier
                        file_extension = os.path.splitext(filename)[1]
                        # Créer un nouveau nom : Type_Document + extension
                        new_filename = f"{display_name}{file_extension}"
                        
                        # Ajouter le fichier au ZIP dans le dossier du candidat
                        zipf.write(file_path, f"{folder_name}/{new_filename}")
                        documents_added += 1
        
        # Créer un fichier README avec les infos du candidat
        readme_content = f"""CANDIDATURE - {application['prenom']} {application['nom']}
=====================================

Informations du candidat:
- Nom complet: {application['prenom']} {application['nom']}
- Email: {application['email']}
- Téléphone: {application['telephone']}
- Adresse: {application['adresse']}
- Poste: {application['job_title']}
- Date de soumission: {application['date_soumission']}
- Statut: {application['status']}

Documents inclus: {documents_added}

Ce dossier a été généré automatiquement par le système de recrutement Salsabil.
Date de génération: {datetime.now().strftime('%d/%m/%Y à %H:%M')}
"""
        
        zipf.writestr(f"{folder_name}/README.txt", readme_content)
    
    # Rembobiner le fichier en mémoire
    memory_file.seek(0)
    
    # Envoyer le fichier ZIP
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"{folder_name}.zip"
    )

# ============================================================================
# ROUTES POUR LE WORKFLOW DE RECRUTEMENT (2 PHASES)
# ============================================================================

@app.route('/admin/applications/<int:app_id>/phase1-decision', methods=['POST'])
@login_required
@permission_required('edit_application')
def admin_phase1_decision(app_id):
    """Route pour prendre une décision en Phase 1"""
    from models import update_phase1_status, get_interview_invitation_pdf
    from notifications import prepare_notification
    
    decision = request.form.get('decision')  # 'selected_for_interview' ou 'rejected'
    interview_date = request.form.get('interview_date')
    rejection_reason = request.form.get('rejection_reason')
    selected_job_title = request.form.get('selected_job_title')  # Pour candidatures spontanées
    
    try:
        # Récupérer la candidature
        application = next((app for app in get_all_applications() if app['id'] == app_id), None)
        if not application:
            flash('Candidature non trouvée', 'error')
            return redirect(url_for('admin_applications'))
        
        # Si candidature spontanée et poste sélectionné, le sauvegarder
        if application['job_id'] is None and selected_job_title:
            conn = get_db_connection()
            conn.execute('UPDATE applications SET selected_job_title = ? WHERE id = ?', 
                        (selected_job_title, app_id))
            conn.commit()
            conn.close()
            # Mettre à jour l'objet application pour l'utiliser dans les notifications
            application['job_title'] = selected_job_title
        
        # Mettre à jour le statut en base de données
        update_phase1_status(app_id, decision, interview_date, rejection_reason)
        
        # Récupérer le chemin du PDF si le candidat est sélectionné pour interview
        pdf_filename = None
        if decision == 'selected_for_interview':
            pdf_filename = get_interview_invitation_pdf(app_id)
            pdf_path = os.path.join('static', 'convocations', pdf_filename) if pdf_filename else None
        else:
            pdf_path = None
        
        # Préparer les notifications
        notifications = prepare_notification(
            application, 
            phase=1, 
            decision=decision, 
            interview_date=interview_date,
            rejection_reason=rejection_reason,
            pdf_path=pdf_path
        )
        
        # Stocker les liens de notification dans la session
        session['pending_notifications'] = {
            'app_id': app_id,
            'phase': 1,
            'email_link': notifications['email_link'],
            'whatsapp_link': notifications['whatsapp_link'],
            'pdf_path': pdf_path,
            'pdf_filename': pdf_filename
        }
        
        if decision == 'selected_for_interview':
            if selected_job_title:
                flash(f'✅ Candidat sélectionné pour un entretien ({selected_job_title}) le {interview_date}', 'success')
            else:
                flash(f'✅ Candidat sélectionné pour un entretien le {interview_date}', 'success')
        else:
            flash('❌ Candidat rejeté en Phase 1', 'info')
        
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('admin_application_detail', app_id=app_id))

@app.route('/admin/applications/<int:app_id>/phase2-decision', methods=['POST'])
@login_required
@permission_required('edit_application')
def admin_phase2_decision(app_id):
    """Route pour prendre une décision en Phase 2 (après interview)"""
    from models import update_phase2_status
    from notifications import prepare_notification
    
    decision = request.form.get('decision')  # 'accepted' ou 'rejected'
    rejection_reason = request.form.get('rejection_reason')
    interview_notes = request.form.get('interview_notes')
    
    try:
        # Récupérer la candidature
        application = next((app for app in get_all_applications() if app['id'] == app_id), None)
        if not application:
            flash('Candidature non trouvée', 'error')
            return redirect(url_for('admin_applications'))
        
        # Sauvegarder les notes d'entretien si fournies
        if interview_notes:
            from models import add_interview_notes
            add_interview_notes(app_id, interview_notes)
        
        # Mettre à jour le statut en base de données
        update_phase2_status(app_id, decision, rejection_reason)
        
        # Générer le PDF de lettre d'acceptation si le candidat est accepté
        pdf_path = None
        if decision == 'accepted':
            from pdf_generator import (generate_acceptance_letter_pdf, 
                                      generate_acceptance_letter_filename,
                                      generate_verification_code)
            from models import save_acceptance_letter_pdf
            from datetime import datetime
            
            # Générer un code de vérification unique
            verification_code = generate_verification_code(app_id, 'acceptation')
            
            # Générer le nom du fichier
            candidate_name = f"{application['prenom']}_{application['nom']}"
            pdf_filename = generate_acceptance_letter_filename(candidate_name, app_id)
            
            # Créer le dossier si nécessaire
            acceptance_dir = os.path.join('static', 'acceptances')
            if not os.path.exists(acceptance_dir):
                os.makedirs(acceptance_dir)
            
            # Chemin complet du fichier
            pdf_path = os.path.join(acceptance_dir, pdf_filename)
            
            # URL de base pour le QR code
            base_url = request.url_root.rstrip('/')
            
            # Détecter la langue actuelle
            lang = session.get('lang', 'fr')
            
            # Générer le PDF avec QR code
            generate_acceptance_letter_pdf(
                application, 
                pdf_path,
                verification_code=verification_code,
                base_url=base_url,
                lang=lang
            )
            
            # Sauvegarder le chemin dans la base de données
            save_acceptance_letter_pdf(app_id, pdf_filename)
            
            # Enregistrer le code de vérification dans la base de données
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO document_verifications 
                (verification_code, application_id, document_type, candidate_name, job_title, issue_date, pdf_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                verification_code,
                app_id,
                'acceptation',
                f"{application['prenom']} {application['nom']}",
                application.get('selected_job_title') or application['job_title'],
                datetime.now().strftime('%d/%m/%Y'),
                pdf_path,
                'valide'
            ))
            conn.commit()
            conn.close()
        
        # Préparer les notifications
        notifications = prepare_notification(
            application, 
            phase=2, 
            decision=decision,
            rejection_reason=rejection_reason
        )
        
        # Stocker les liens de notification dans la session
        session['pending_notifications'] = {
            'app_id': app_id,
            'phase': 2,
            'email_link': notifications['email_link'],
            'whatsapp_link': notifications['whatsapp_link'],
            'pdf_path': pdf_path
        }
        
        if decision == 'accepted':
            flash('🎉 Candidat accepté ! Lettre d\'acceptation générée avec succès !', 'success')
        else:
            flash('❌ Candidat rejeté après interview', 'info')
        
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('admin_application_detail', app_id=app_id))

@app.route('/admin/applications/<int:app_id>/send-notification')
@login_required
@permission_required('edit_application')
def admin_send_notification(app_id):
    """Route pour marquer qu'une notification a été envoyée"""
    from models import mark_notification_sent
    
    phase = request.args.get('phase', type=int)
    
    try:
        mark_notification_sent(app_id, phase)
        flash('✅ Notification marquée comme envoyée', 'success')
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('admin_application_detail', app_id=app_id))

@app.route('/admin/applications/<int:app_id>/generate-interview-invitation')
@login_required
@permission_required('edit_application')
def admin_generate_interview_invitation(app_id):
    """Route pour générer le PDF de convocation à l'entretien avec QR code de vérification"""
    from pdf_generator import (generate_interview_invitation_pdf, 
                               generate_interview_invitation_filename,
                               generate_verification_code)
    from models import save_interview_invitation_pdf
    
    try:
        # Récupérer la candidature
        application = next((app for app in get_all_applications() if app['id'] == app_id), None)
        if not application:
            flash('Candidature non trouvée', 'error')
            return redirect(url_for('admin_applications'))
        
        # Vérifier que le candidat est sélectionné pour interview
        if application.get('phase1_status') != 'selected_for_interview':
            flash('Le candidat doit d\'abord être sélectionné pour un entretien', 'error')
            return redirect(url_for('admin_application_detail', app_id=app_id))
        
        # Vérifier qu'une date d'interview existe
        if not application.get('interview_date'):
            flash('Aucune date d\'entretien n\'est définie', 'error')
            return redirect(url_for('admin_application_detail', app_id=app_id))
        
        # Générer un code de vérification unique
        verification_code = generate_verification_code(app_id, 'convocation')
        
        # Générer le nom du fichier
        candidate_name = f"{application['prenom']}_{application['nom']}"
        pdf_filename = generate_interview_invitation_filename(candidate_name, app_id)
        
        # Chemin complet du fichier
        pdf_path = os.path.join('static', 'convocations', pdf_filename)
        
        # URL de base pour le QR code
        base_url = request.url_root.rstrip('/')
        
        # Détecter la langue actuelle
        lang = session.get('lang', 'fr')
        
        # Générer le PDF avec QR code
        generate_interview_invitation_pdf(
            application_data=application,
            interview_date=application['interview_date'],
            output_path=pdf_path,
            verification_code=verification_code,
            base_url=base_url,
            lang=lang
        )
        
        # Sauvegarder le chemin dans la base de données
        save_interview_invitation_pdf(app_id, pdf_filename)
        
        # Enregistrer le code de vérification dans la base de données
        conn = get_db_connection()
        from datetime import datetime
        conn.execute('''
            INSERT INTO document_verifications 
            (verification_code, application_id, document_type, candidate_name, job_title, issue_date, pdf_path, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            verification_code,
            app_id,
            'convocation',
            f"{application['prenom']} {application['nom']}",
            application.get('selected_job_title') or application['job_title'],
            datetime.now().strftime('%d/%m/%Y'),
            pdf_path,
            'valide'
        ))
        conn.commit()
        conn.close()
        
        flash('✅ Convocation générée avec succès avec code de vérification QR !', 'success')
        
    except Exception as e:
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'error')
    
    return redirect(url_for('admin_application_detail', app_id=app_id))

@app.route('/admin/applications/<int:app_id>/download-interview-invitation')
@login_required
@permission_required('view_applications')
def admin_download_interview_invitation(app_id):
    """Route pour télécharger le PDF de convocation"""
    from models import get_interview_invitation_pdf
    
    try:
        # Récupérer le nom du fichier depuis la BDD
        pdf_filename = get_interview_invitation_pdf(app_id)
        
        if not pdf_filename:
            flash('Aucune convocation n\'a été générée pour cette candidature', 'error')
            return redirect(url_for('admin_application_detail', app_id=app_id))
        
        # Chemin complet du fichier
        pdf_path = os.path.join('static', 'convocations', pdf_filename)
        
        if not os.path.exists(pdf_path):
            flash('Le fichier de convocation est introuvable', 'error')
            return redirect(url_for('admin_application_detail', app_id=app_id))
        
        # Envoyer le fichier
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_filename
        )
        
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('admin_application_detail', app_id=app_id))

@app.route('/admin/jobs')


# Routes pour la gestion des offres d'emploi
@app.route('/admin/jobs')
@login_required
@permission_required('view_jobs')
def admin_jobs():
    """Route pour afficher la page de gestion des offres"""
    all_applications = get_all_applications()
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0)
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)  # Get all permissions
    return render_template('admin/jobs.html', 
                         jobs=get_all_jobs(), 
                         applications=regular_applications,
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         is_closing_soon=is_closing_soon)

@app.route('/admin/jobs/<int:job_id>/candidates')
@login_required
@permission_required('view_applications')
def admin_job_candidates(job_id):
    """Route pour afficher les candidats d'un job spécifique"""
    job = next((job for job in get_all_jobs() if job['id'] == job_id), None)
    if job is None:
        flash('Offre d\'emploi non trouvée', 'error')
        return redirect(url_for('admin_jobs'))
    
    # Filtrer les candidatures pour ce job
    all_applications = get_all_applications()
    job_applications = [app for app in all_applications if app['job_id'] == job_id]
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0) pour le badge
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)  # Get all permissions
    
    return render_template('admin/job_candidates.html', 
                         job=job,
                         applications=job_applications,
                         all_applications=regular_applications,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count)

@app.route('/admin/jobs/<int:job_id>/candidates_ar')
@login_required
@permission_required('view_applications')
def admin_job_candidates_ar(job_id):
    """Route pour afficher les candidats d'un job spécifique - Version Arabe"""
    session['lang'] = 'ar'  # Maintenir la langue arabe
    job = next((job for job in get_all_jobs() if job['id'] == job_id), None)
    if job is None:
        flash('عرض العمل غير موجود', 'error')
        return redirect(url_for('admin_jobs_ar'))
    
    # Filtrer les candidatures pour ce job
    all_applications = get_all_applications()
    job_applications = [app for app in all_applications if app['job_id'] == job_id]
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0) pour le badge
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)  # Get all permissions
    
    return render_template('admin/job_candidates.html', 
                         job=job,
                         applications=job_applications,
                         all_applications=regular_applications,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         lang='ar')

@app.route('/admin/jobs/add', methods=['POST'])
@login_required
@permission_required('add_job')
def admin_add_job():
    """Route pour ajouter une nouvelle offre"""
    
    try:
        # Récupérer les requirements
        requirements_text = request.form.get('requirements', '').strip()
        
        # Récupérer le department
        department = request.form.get('department', '').strip()
        
        # Récupérer les langues sélectionnées
        langues = []
        if request.form.get('langue_arabe'):
            langues.append('Arabe')
        if request.form.get('langue_anglaise'):
            langues.append('Anglais')
        if request.form.get('langue_francaise'):
            langues.append('Français')
        
        langues_requises = ', '.join(langues) if langues else None
        
        # Créer le job dans la base de données
        job_id = create_job(
            titre=request.form.get('title'),
            type_job=request.form.get('type'),
            lieu=request.form.get('location'),
            description=request.form.get('description'),
            date_limite=request.form.get('deadline'),
            requirements=requirements_text if requirements_text else None,
            department=department if department else None,
            langues_requises=langues_requises
        )
        
        flash('Offre d\'emploi ajoutée avec succès!', 'success')
    except Exception as e:
        flash(f'Erreur lors de l\'ajout de l\'offre: {str(e)}', 'error')
    
    return redirect(url_for('admin_jobs'))

@app.route('/admin/jobs/edit', methods=['POST'])
@login_required
@permission_required('edit_job')
def admin_edit_job():
    """Route pour modifier une offre existante"""
    
    try:
        job_id = int(request.form.get('job_id'))
        
        # Récupérer les requirements
        requirements_text = request.form.get('requirements', '').strip()
        
        # Récupérer le department
        department = request.form.get('department', '').strip()
        
        # Récupérer les langues sélectionnées
        langues = []
        if request.form.get('langue_arabe'):
            langues.append('Arabe')
        if request.form.get('langue_anglaise'):
            langues.append('Anglais')
        if request.form.get('langue_francaise'):
            langues.append('Français')
        
        langues_requises = ', '.join(langues) if langues else None
        
        # Mettre à jour le job dans la base de données
        update_job(
            job_id=job_id,
            titre=request.form.get('title'),
            type_job=request.form.get('type'),
            lieu=request.form.get('location'),
            description=request.form.get('description'),
            date_limite=request.form.get('deadline'),
            requirements=requirements_text if requirements_text else None,
            department=department if department else None,
            langues_requises=langues_requises
        )
        
        flash('Offre d\'emploi modifiée avec succès!', 'success')
    except Exception as e:
        flash(f'Erreur lors de la modification de l\'offre: {str(e)}', 'error')
    
    return redirect(url_for('admin_jobs'))

@app.route('/admin/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@permission_required('delete_job')
def admin_delete_job(job_id):
    """Route pour supprimer une offre"""
    
    try:
        # Supprimer le job de la base de données (cascade sur les candidatures)
        delete_job(job_id)
        flash('Offre d\'emploi supprimée avec succès!', 'success')
    except Exception as e:
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('admin_jobs'))
    return redirect(url_for('admin_jobs'))

@app.route('/admin/jobs/<int:job_id>/data')
@login_required
@permission_required('view_jobs')
def admin_job_data(job_id):
    """Route API pour récupérer les données d'une offre (pour l'édition)"""
    job = next((job for job in get_all_jobs() if job['id'] == job_id), None)
    
    if job is None:
        return {'error': 'Offre non trouvée'}, 404
    
    return job

# Routes pour la gestion des employés (Admin seulement)
@app.route('/admin/employees')
@login_required
@permission_required('view_employees')
def admin_employees():
    """Route pour afficher la liste des employés"""
    all_applications = get_all_applications()
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0)
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    return render_template('admin/employees.html', 
                         employees=get_all_employees(),
                         jobs=get_all_jobs(),
                         applications=regular_applications,
                         current_user=current_user,
                         permissions=ROLE_PERMISSIONS.get(current_user['role'], {}),
                         spontaneous_count=spontaneous_count)

@app.route('/admin/employees/add', methods=['POST'])
@login_required
@permission_required('add_employee')
def admin_add_employee():
    """Route pour ajouter un nouvel employé"""
    
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        prenom = request.form.get('prenom')
        nom = request.form.get('nom')
        email = request.form.get('email')
        role = request.form.get('role')
        
        # Vérifier si le username existe déjà
        if get_employee_by_username(username):
            flash('Ce nom d\'utilisateur existe déjà', 'error')
            return redirect(url_for('admin_employees'))
        
        # Créer l'employé dans la base de données
        emp_id = create_employee(username, password, prenom, nom, email, role, 'actif')
        
        flash(f'Employé {prenom} {nom} ajouté avec succès!', 'success')
        return redirect(url_for('admin_employees'))
    except Exception as e:
        flash(f'Erreur lors de l\'ajout de l\'employé: {str(e)}', 'error')
        return redirect(url_for('admin_employees'))

@app.route('/admin/employees/<int:emp_id>/toggle-status', methods=['POST'])
@login_required
@permission_required('edit_employee')
def admin_toggle_employee_status(emp_id):
    """Route pour activer/désactiver un employé"""
    employee = get_employee_by_id(emp_id)
    
    if employee is None:
        flash('Employé non trouvé', 'error')
        return redirect(url_for('admin_employees'))
    
    # Ne pas permettre de désactiver son propre compte
    if employee['id'] == session.get('user_id'):
        flash('Vous ne pouvez pas désactiver votre propre compte', 'error')
        return redirect(url_for('admin_employees'))
    
    try:
        # Basculer le statut dans la base de données
        new_status = toggle_employee_status(emp_id)
        flash(f'Statut de {employee["prenom"]} {employee["nom"]} mis à jour: {new_status}', 'success')
    except Exception as e:
        flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
    
    return redirect(url_for('admin_employees'))

@app.route('/admin/employees/<int:emp_id>/delete', methods=['POST'])
@login_required
@permission_required('delete_employee')
def admin_delete_employee(emp_id):
    """Route pour supprimer un employé"""
    
    employee = get_employee_by_id(emp_id)
    
    if employee is None:
        flash('Employé non trouvé', 'error')
        return redirect(url_for('admin_employees'))
    
    # Ne pas permettre de supprimer son propre compte
    if employee['id'] == session.get('user_id'):
        flash('Vous ne pouvez pas supprimer votre propre compte', 'error')
        return redirect(url_for('admin_employees'))
    
    # Supprimer l'employé de la base de données
    try:
        delete_employee(emp_id)
        flash(f'Employé {employee["prenom"]} {employee["nom"]} supprimé', 'success')
    except Exception as e:
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('admin_employees'))

# Routes pour la gestion de profil (tous les utilisateurs)
@app.route('/admin/profile')
@login_required
def admin_profile():
    """Route pour afficher le profil de l'utilisateur connecté"""
    all_applications = get_all_applications()
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0)
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)
    return render_template('admin/profile.html',
                         current_user=current_user,
                         jobs=get_all_jobs(),
                         applications=regular_applications,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count)

@app.route('/admin/profile/update', methods=['POST'])
@login_required
def admin_update_profile():
    """Route pour mettre à jour le profil de l'utilisateur"""
    
    current_user = get_current_user()
    if not current_user:
        flash('Utilisateur non trouvé', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        prenom = request.form.get('prenom', current_user['prenom'])
        nom = request.form.get('nom', current_user['nom'])
        email = request.form.get('email', current_user['email'])
        new_username = request.form.get('username')
        
        # Vérifier si l'username est unique (si modifié)
        if new_username and new_username != current_user['username']:
            existing_user = get_employee_by_username(new_username)
            if existing_user and existing_user['id'] != current_user['id']:
                flash('Ce nom d\'utilisateur est déjà utilisé', 'error')
                return redirect(url_for('admin_profile'))
            username = new_username
            session['username'] = new_username
        else:
            username = current_user['username']
        
        # Mettre à jour dans la base de données
        update_employee_profile(current_user['id'], username, prenom, nom, email)
        
        # Mettre à jour la session
        session['full_name'] = f"{prenom} {nom}"
        
        flash('Profil mis à jour avec succès', 'success')
    except Exception as e:
        flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
    
    return redirect(url_for('admin_profile'))

@app.route('/admin/profile/change-password', methods=['POST'])
@login_required
def admin_change_password():
    """Route pour changer le mot de passe"""
    
    current_user = get_current_user()
    if not current_user:
        flash('Utilisateur non trouvé', 'error')
        return redirect(url_for('admin_login'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Vérifier l'ancien mot de passe
    if current_user['password'] != current_password:
        flash('Mot de passe actuel incorrect', 'error')
        return redirect(url_for('admin_profile'))
    
    # Vérifier que les nouveaux mots de passe correspondent
    if new_password != confirm_password:
        flash('Les nouveaux mots de passe ne correspondent pas', 'error')
        return redirect(url_for('admin_profile'))
    
    # Vérifier la longueur du mot de passe
    if len(new_password) < 6:
        flash('Le mot de passe doit contenir au moins 6 caractères', 'error')
        return redirect(url_for('admin_profile'))
    
    try:
        # Mettre à jour le mot de passe dans la base de données
        update_employee_password(current_user['id'], new_password)
        flash('Mot de passe changé avec succès', 'success')
    except Exception as e:
        flash(f'Erreur lors du changement de mot de passe: {str(e)}', 'error')
    
    return redirect(url_for('admin_profile'))

# ==================== ROUTES ADMIN ARABES ====================

@app.route('/admin/login_ar', methods=['GET', 'POST'])
def admin_login_ar():
    """Route pour la connexion des employés - Version Arabe"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        employee = get_employee_by_username(username)
        
        if employee and employee['password'] == password and employee['status'] == 'actif':
            session['logged_in'] = True
            session['user_id'] = employee['id']
            session['username'] = employee['username']
            session['role'] = employee['role']
            session['full_name'] = f"{employee['prenom']} {employee['nom']}"
            session['lang'] = 'ar'  # Définir la langue arabe
            flash(f'مرحباً {employee["prenom"]} {employee["nom"]}!', 'success')
            return redirect(url_for('admin_dashboard_ar'))
        else:
            flash('بيانات الدخول غير صحيحة أو الحساب غير مفعل', 'error')
            return render_template('admin/login.html', lang='ar')
    
    return render_template('admin/login.html', lang='ar')

@app.route('/admin/dashboard_ar')
@login_required
def admin_dashboard_ar():
    """Route pour le dashboard admin - Version Arabe"""
    session['lang'] = 'ar'  # Maintenir la langue arabe
    current_user = get_current_user()
    all_applications = get_all_applications()
    
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    return render_template('admin/dashboard.html', 
                         applications=regular_applications,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=ROLE_PERMISSIONS.get(current_user['role'], {}),
                         spontaneous_count=spontaneous_count,
                         lang='ar')

@app.route('/admin/applications_ar')
@login_required
@permission_required('view_applications')
def admin_applications_ar():
    """Route pour voir toutes les candidatures - Version Arabe"""
    session['lang'] = 'ar'  # Maintenir la langue arabe
    all_applications = get_all_applications()
    
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)
    return render_template('admin/applications.html', 
                         applications=regular_applications,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         lang='ar')

@app.route('/admin/spontaneous_applications_ar')
@login_required
@permission_required('view_applications')
def admin_spontaneous_applications_ar():
    """Route pour voir les candidatures spontanées - Version Arabe"""
    session['lang'] = 'ar'  # Maintenir la langue arabe
    all_applications = get_all_applications()
    spontaneous_apps = [app for app in all_applications if app.get('job_id') is None]
    spontaneous_count = len(spontaneous_apps)
    
    current_user = get_current_user()
    permissions = has_permission(None)
    return render_template('admin/spontaneous_applications.html', 
                         applications=spontaneous_apps,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         lang='ar')

@app.route('/admin/favorite-applications_ar')
@login_required
@permission_required('view_applications')
def admin_favorite_applications_ar():
    """Route pour voir uniquement les candidatures favorites - Version Arabe"""
    session['lang'] = 'ar'  # Maintenir la langue arabe
    from models import get_favorite_applications
    
    # Récupérer uniquement les candidatures favorites
    favorite_apps = get_favorite_applications()
    
    all_applications = get_all_applications()
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)
    
    return render_template('admin/spontaneous_applications.html', 
                         applications=favorite_apps,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         is_favorites_view=True,
                         lang='ar')

@app.route('/admin/jobs_ar')
@login_required
@permission_required('view_jobs')
def admin_jobs_ar():
    """Route pour voir toutes les offres d'emploi - Version Arabe"""
    session['lang'] = 'ar'  # Maintenir la langue arabe
    all_applications = get_all_applications()
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)
    return render_template('admin/jobs.html',
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         is_closing_soon=is_closing_soon,
                         lang='ar')

@app.route('/admin/employees_ar')
@login_required
@permission_required('view_employees')
def admin_employees_ar():
    """Route pour voir tous les employés - Version Arabe"""
    session['lang'] = 'ar'  # Maintenir la langue arabe
    all_applications = get_all_applications()
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)
    return render_template('admin/employees.html',
                         employees=get_all_employees(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         lang='ar')

@app.route('/admin/profile_ar')
@login_required
def admin_profile_ar():
    """Route pour le profil de l'employé - Version Arabe"""
    session['lang'] = 'ar'  # Maintenir la langue arabe
    current_user = get_current_user()
    all_applications = get_all_applications()
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    permissions = has_permission(None)
    return render_template('admin/profile.html',
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         lang='ar')

@app.route('/admin/applications_ar/<int:app_id>')
@login_required
@permission_required('view_applications')
def admin_application_detail_ar(app_id):
    """Route pour voir les détails d'une candidature - Version Arabe"""
    session['lang'] = 'ar'  # Maintenir la langue arabe
    all_applications = get_all_applications()
    application = next((app for app in all_applications if app['id'] == app_id), None)
    if application is None:
        flash('لم يتم العثور على الطلب', 'error')
        # Rediriger vers la page appropriée selon la source
        referrer = request.referrer
        if referrer and 'spontaneous' in referrer:
            return redirect(url_for('admin_spontaneous_applications_ar'))
        return redirect(url_for('admin_applications_ar'))
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0) pour le badge
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)
    
    return render_template('admin/application_detail.html', 
                         application=application, 
                         applications=regular_applications,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         lang='ar')

@app.route('/admin/spontaneous_applications_ar/<int:app_id>')
@login_required
@permission_required('view_applications')
def admin_spontaneous_application_detail_ar(app_id):
    """Route pour voir les détails d'une candidature spontanée - Version Arabe"""
    session['lang'] = 'ar'  # Maintenir la langue arabe
    all_applications = get_all_applications()
    application = next((app for app in all_applications if app['id'] == app_id), None)
    
    if application is None:
        flash('لم يتم العثور على الطلب', 'error')
        return redirect(url_for('admin_spontaneous_applications_ar'))
    
    # Vérifier que c'est bien une candidature spontanée
    if application.get('job_id') is not None:
        flash('هذا الطلب ليس طلبًا عفويًا', 'error')
        return redirect(url_for('admin_applications_ar'))
    
    # Filtrer pour exclure les candidatures spontanées (job_id = 0) pour le badge
    regular_applications = [app for app in all_applications if app.get('job_id') is not None]
    spontaneous_count = len([app for app in all_applications if app.get('job_id') is None])
    
    current_user = get_current_user()
    permissions = has_permission(None)
    
    return render_template('admin/application_detail.html', 
                         application=application, 
                         applications=regular_applications,
                         jobs=get_all_jobs(),
                         current_user=current_user,
                         permissions=permissions,
                         spontaneous_count=spontaneous_count,
                         is_spontaneous_view=True,
                         lang='ar')

# ==================== ROUTES DE VÉRIFICATION DE DOCUMENTS ====================

@app.route('/verify/<verification_code>')
def verify_document(verification_code):
    """
    Route publique pour vérifier l'authenticité d'un document via QR code
    Permet au personnel de sécurité de scanner le QR code et vérifier le document
    """
    conn = get_db_connection()
    
    # Rechercher le document dans la base de données
    document = conn.execute('''
        SELECT 
            verification_code,
            application_id,
            document_type,
            candidate_name,
            job_title,
            issue_date,
            pdf_path,
            status,
            created_at
        FROM document_verifications
        WHERE verification_code = ?
    ''', (verification_code.upper(),)).fetchone()
    
    conn.close()
    
    # Convertir en dictionnaire si trouvé
    if document:
        document = dict(document)
    
    return render_template('verify.html', 
                         document=document, 
                         verification_code=verification_code.upper())

@app.route('/test-verify')
def test_verify():
    """
    Page de test pour vérifier les documents
    Permet d'entrer manuellement un code de vérification
    """
    return render_template('test_verify.html')

@app.route('/verify-redirect', methods=['POST'])
def verify_redirect():
    """
    Redirection vers la page de vérification avec le code entré
    """
    verification_code = request.form.get('verification_code', '').strip().upper()
    if not verification_code:
        flash('Veuillez entrer un code de vérification', 'error')
        return redirect(url_for('test_verify'))
    
    return redirect(url_for('verify_document', verification_code=verification_code))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
