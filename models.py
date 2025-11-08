from database import get_db_connection, is_postgresql
from datetime import datetime, timezone, timedelta
import os

# ==================== TIMEZONE CONFIGURATION ====================

# Fuseau horaire des Comores (UTC+3)
COMOROS_TZ = timezone(timedelta(hours=3))

def get_comoros_time():
    """Retourne l'heure actuelle aux Comores (UTC+3) sans timezone info"""
    return datetime.now(COMOROS_TZ).replace(tzinfo=None)

# ==================== UTILITY FUNCTIONS ====================

def get_placeholder():
    """Retourne le placeholder SQL approprié selon la base de données"""
    return '%s' if is_postgresql() else '?'

def convert_query_placeholders(query, num_params):
    """Convertit les placeholders ? en %s si nécessaire pour PostgreSQL"""
    if is_postgresql():
        # Remplacer tous les ? par %s
        return query.replace('?', '%s')
    return query

def delete_file_if_exists(filename):
    """Supprimer un fichier du système de fichiers s'il existe"""
    if filename:
        # Chemins possibles pour les fichiers
        paths = [
            os.path.join('static', 'uploads', filename),
            os.path.join('uploads', filename)
        ]
        
        for filepath in paths:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"✅ Fichier supprimé: {filepath}")
                    return True
                except Exception as e:
                    print(f"❌ Erreur lors de la suppression de {filepath}: {str(e)}")
                    return False
    return False

def delete_application_files(application):
    """Supprimer tous les fichiers associés à une candidature (locaux et Cloudinary)"""
    import os
    from cloudinary_config import delete_file_from_cloudinary
    
    files_to_delete = [
        application.get('photo'),
        application.get('cv'),
        application.get('lettre_demande'),
        application.get('carte_id'),
        application.get('lettre_recommandation'),
        application.get('casier_judiciaire'),
        application.get('diplome')
    ]
    
    deleted_count = 0
    for file_url_or_name in files_to_delete:
        if not file_url_or_name:
            continue
            
        # Vérifier si c'est une URL Cloudinary
        if file_url_or_name.startswith('http://') or file_url_or_name.startswith('https://'):
            # C'est une URL Cloudinary - extraire le public_id
            if 'cloudinary.com' in file_url_or_name:
                try:
                    # Format URL Cloudinary: https://res.cloudinary.com/cloud/image/upload/v123/folder/filename.ext
                    # Public ID = folder/filename (sans extension pour les images)
                    parts = file_url_or_name.split('/upload/')
                    if len(parts) > 1:
                        # Extraire le chemin après /upload/
                        path_parts = parts[1].split('/')
                        # Ignorer le v123456 (version) et reconstruire le public_id
                        if len(path_parts) > 1:
                            # Retirer l'extension du dernier élément
                            filename_with_ext = path_parts[-1]
                            filename_without_ext = '.'.join(filename_with_ext.split('.')[:-1])
                            # Reconstruire le public_id
                            public_id = '/'.join(path_parts[1:-1] + [filename_without_ext])
                            
                            if delete_file_from_cloudinary(public_id):
                                deleted_count += 1
                                print(f"☁️ Fichier Cloudinary supprimé: {public_id}")
                            else:
                                print(f"⚠️ Échec suppression Cloudinary: {public_id}")
                except Exception as e:
                    print(f"⚠️ Erreur lors de la suppression Cloudinary: {e}")
        else:
            # C'est un fichier local
            if delete_file_if_exists(file_url_or_name):
                deleted_count += 1
    
    # Supprimer le PDF de convocation s'il existe
    pdf_filename = application.get('interview_invitation_pdf')
    if pdf_filename:
        pdf_path = os.path.join('static', 'convocations', pdf_filename)
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                deleted_count += 1
                print(f"📄 PDF de convocation supprimé: {pdf_filename}")
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression du PDF: {e}")
    
    # Supprimer le PDF de lettre d'acceptation s'il existe
    acceptance_pdf_filename = application.get('acceptance_letter_pdf')
    if acceptance_pdf_filename:
        acceptance_pdf_path = os.path.join('static', 'acceptances', acceptance_pdf_filename)
        if os.path.exists(acceptance_pdf_path):
            try:
                os.remove(acceptance_pdf_path)
                deleted_count += 1
                print(f"✅ PDF de lettre d'acceptation supprimé: {acceptance_pdf_filename}")
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression de la lettre d'acceptation: {e}")
    
    # Supprimer les rapports de candidat (FR et AR) s'ils existent
    reports_dir = os.path.join('static', 'reports')
    if os.path.exists(reports_dir):
        import glob
        app_id = application.get('id')
        # Rechercher tous les fichiers de rapport pour cette candidature (FR et AR)
        # Pattern: Rapport_Candidature_*_<app_id>_*.pdf
        report_pattern = os.path.join(reports_dir, f"Rapport_Candidature_*_{app_id}_*.pdf")
        report_files = glob.glob(report_pattern)
        
        for report_file in report_files:
            try:
                os.remove(report_file)
                deleted_count += 1
                print(f"📊 Rapport de candidat supprimé: {os.path.basename(report_file)}")
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression du rapport: {e}")
    
    return deleted_count

# ==================== EMPLOYEES ====================

def get_all_employees():
    """Récupérer tous les employés"""
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees ORDER BY id').fetchall()
    conn.close()
    return [dict(emp) for emp in employees]

def get_employee_by_id(emp_id):
    """Récupérer un employé par son ID"""
    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (emp_id,)).fetchone()
    conn.close()
    return dict(employee) if employee else None

def get_employee_by_username(username):
    """Récupérer un employé par son nom d'utilisateur"""
    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE username = ?', (username,)).fetchone()
    conn.close()
    return dict(employee) if employee else None

def create_employee(username, password, prenom, nom, email, role, status='actif'):
    """Créer un nouvel employé"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO employees (username, password, prenom, nom, email, role, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, password, prenom, nom, email, role, status))
    conn.commit()
    emp_id = cursor.lastrowid
    conn.close()
    return emp_id

def update_employee(emp_id, username, prenom, nom, email, role, status):
    """Mettre à jour un employé"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE employees 
        SET username = ?, prenom = ?, nom = ?, email = ?, role = ?, status = ?
        WHERE id = ?
    ''', (username, prenom, nom, email, role, status, emp_id))
    conn.commit()
    conn.close()

def update_employee_profile(emp_id, username, prenom, nom, email):
    """Mettre à jour le profil d'un employé"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE employees 
        SET username = ?, prenom = ?, nom = ?, email = ?
        WHERE id = ?
    ''', (username, prenom, nom, email, emp_id))
    conn.commit()
    conn.close()

def update_employee_password(emp_id, new_password):
    """Mettre à jour le mot de passe d'un employé"""
    conn = get_db_connection()
    conn.execute('UPDATE employees SET password = ? WHERE id = ?', (new_password, emp_id))
    conn.commit()
    conn.close()

def toggle_employee_status(emp_id):
    """Activer/Désactiver un employé"""
    conn = get_db_connection()
    employee = conn.execute('SELECT status FROM employees WHERE id = ?', (emp_id,)).fetchone()
    new_status = 'inactif' if employee['status'] == 'actif' else 'actif'
    conn.execute('UPDATE employees SET status = ? WHERE id = ?', (new_status, emp_id))
    conn.commit()
    conn.close()
    return new_status

def delete_employee(emp_id):
    """Supprimer un employé"""
    conn = get_db_connection()
    conn.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
    conn.commit()
    conn.close()

# ==================== JOBS ====================

def get_all_jobs():
    """Récupérer tous les jobs avec support bilingue"""
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs ORDER BY id DESC').fetchall()
    conn.close()
    # Convertir en dict et mapper les champs pour compatibilité avec les templates
    result = []
    for job in jobs:
        job_dict = dict(job)
        # Mapper les champs de la base de données vers les noms utilisés dans les templates
        job_dict['title'] = job_dict.get('titre', '')
        job_dict['location'] = job_dict.get('lieu', '')
        job_dict['deadline'] = job_dict.pop('date_limite')
        job_dict['posted_date'] = job_dict.get('date_publication', '')
        # Si department existe dans la BDD, l'utiliser, sinon utiliser type comme fallback
        if not job_dict.get('department'):
            job_dict['department'] = job_dict.get('type', 'Non spécifié')
        # Parser les requirements (stockées comme texte avec \n comme séparateur)
        req_text = job_dict.get('requirements', '')
        if req_text:
            job_dict['requirements'] = [r.strip() for r in req_text.split('\n') if r.strip()]
        else:
            job_dict['requirements'] = []
        
        # Parser les requirements arabes
        req_text_ar = job_dict.get('requirements_ar', '')
        if req_text_ar:
            job_dict['requirements_ar'] = [r.strip() for r in req_text_ar.split('\n') if r.strip()]
        else:
            job_dict['requirements_ar'] = []
        
        result.append(job_dict)
    return result

def get_job_by_id(job_id):
    """Récupérer un job par son ID avec support bilingue"""
    conn = get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    conn.close()
    if job:
        job_dict = dict(job)
        # Mapper les champs de la base de données vers les noms utilisés dans les templates
        job_dict['title'] = job_dict.get('titre', '')
        job_dict['location'] = job_dict.get('lieu', '')
        job_dict['deadline'] = job_dict.pop('date_limite')
        job_dict['posted_date'] = job_dict.get('date_publication', '')
        # Si department existe dans la BDD, l'utiliser, sinon utiliser type comme fallback
        if not job_dict.get('department'):
            job_dict['department'] = job_dict.get('type', 'Non spécifié')
        # Parser les requirements
        req_text = job_dict.get('requirements', '')
        if req_text:
            job_dict['requirements'] = [r.strip() for r in req_text.split('\n') if r.strip()]
        else:
            job_dict['requirements'] = []
        
        # Parser les requirements arabes
        req_text_ar = job_dict.get('requirements_ar', '')
        if req_text_ar:
            job_dict['requirements_ar'] = [r.strip() for r in req_text_ar.split('\n') if r.strip()]
        else:
            job_dict['requirements_ar'] = []
        
        return job_dict
    return None

def create_job(titre, type_job, lieu, description, date_limite, requirements=None, department=None, langues_requises=None,
               titre_ar=None, lieu_ar=None, description_ar=None, requirements_ar=None, department_ar=None):
    """Créer un nouveau job avec support bilingue (FR + AR)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Enregistrer la date de publication avec heure (format ISO local)
    date_publication = get_comoros_time().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO jobs (titre, titre_ar, type, lieu, lieu_ar, description, description_ar, 
                         requirements, requirements_ar, department, department_ar, date_limite, 
                         date_publication, langues_requises)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (titre, titre_ar, type_job, lieu, lieu_ar, description, description_ar, 
          requirements, requirements_ar, department, department_ar, date_limite, 
          date_publication, langues_requises))
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    return job_id

def update_job(job_id, titre, type_job, lieu, description, date_limite, requirements=None, department=None, langues_requises=None,
               titre_ar=None, lieu_ar=None, description_ar=None, requirements_ar=None, department_ar=None):
    """Mettre à jour un job avec support bilingue (FR + AR)"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE jobs 
        SET titre = ?, titre_ar = ?, type = ?, lieu = ?, lieu_ar = ?, 
            description = ?, description_ar = ?, requirements = ?, requirements_ar = ?, 
            department = ?, department_ar = ?, date_limite = ?, langues_requises = ?
        WHERE id = ?
    ''', (titre, titre_ar, type_job, lieu, lieu_ar, description, description_ar, 
          requirements, requirements_ar, department, department_ar, date_limite, 
          langues_requises, job_id))
    conn.commit()
    conn.close()

def delete_job(job_id):
    """Supprimer un job et toutes les candidatures associées avec leurs fichiers"""
    # Récupérer toutes les candidatures pour ce job
    applications = get_applications_by_job(job_id)
    
    # Supprimer les fichiers de chaque candidature
    total_files_deleted = 0
    for app in applications:
        deleted_files = delete_application_files(app)
        total_files_deleted += deleted_files
    
    if total_files_deleted > 0:
        print(f"📁 {total_files_deleted} fichier(s) supprimé(s) pour {len(applications)} candidature(s)")
    
    # Supprimer les codes de vérification et les candidatures de la base de données
    conn = get_db_connection()
    
    # Supprimer les codes de vérification pour toutes les candidatures de ce job
    verification_count = conn.execute(
        'SELECT COUNT(*) as count FROM document_verifications WHERE application_id IN (SELECT id FROM applications WHERE job_id = ?)', 
        (job_id,)
    ).fetchone()['count']
    
    if verification_count > 0:
        conn.execute(
            'DELETE FROM document_verifications WHERE application_id IN (SELECT id FROM applications WHERE job_id = ?)', 
            (job_id,)
        )
        print(f"🔐 {verification_count} code(s) de vérification supprimé(s)")
    
    # Supprimer les candidatures et le job
    conn.execute('DELETE FROM applications WHERE job_id = ?', (job_id,))
    conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()

# ==================== APPLICATIONS ====================

def get_all_applications():
    """Récupérer toutes les candidatures"""
    conn = get_db_connection()
    applications = conn.execute('SELECT * FROM applications ORDER BY id DESC').fetchall()
    conn.close()
    return [dict(app) for app in applications]

def get_application_by_id(app_id):
    """Récupérer une candidature par son ID"""
    conn = get_db_connection()
    application = conn.execute('SELECT * FROM applications WHERE id = ?', (app_id,)).fetchone()
    conn.close()
    return dict(application) if application else None

def get_applications_by_job(job_id):
    """Récupérer toutes les candidatures pour un job"""
    conn = get_db_connection()
    applications = conn.execute('SELECT * FROM applications WHERE job_id = ? ORDER BY id DESC', (job_id,)).fetchall()
    conn.close()
    return [dict(app) for app in applications]

def create_application(job_id, job_title, prenom, nom, email, telephone, adresse, pays, region,
                      sexe, lieu_naissance, date_naissance, nationalite, etat_civil,
                      travaille_actuellement, dernier_lieu_travail, raison_depart,
                      niveau_instruction, specialisation, specialisation_autre,
                      langue_arabe, langue_anglaise, langue_francaise,
                      autre_langue_nom, autre_langue_niveau,
                      problemes_sante, nature_maladie,
                      choix_travail,
                      photo, cv, lettre_demande, carte_id, lettre_recommandation, 
                      casier_judiciaire, diplome, form_language='fr'):
    """Créer une nouvelle candidature"""
    try:
        # Convertir job_id=0 en None pour les candidatures spontanées
        if job_id == 0:
            job_id = None
            print("   🔄 Candidature spontanée détectée: job_id converti en NULL")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        # Enregistrer la date de soumission avec heure (format ISO local)
        date_soumission = get_comoros_time().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"   💾 Exécution de la requête SQL INSERT... (langue formulaire: {form_language})")
        
        # Utiliser le placeholder approprié
        ph = get_placeholder()
        query = f'''
            INSERT INTO applications 
            (job_id, job_title, prenom, nom, email, telephone, adresse, pays, region,
             sexe, lieu_naissance, date_naissance, nationalite, etat_civil,
             travaille_actuellement, dernier_lieu_travail, raison_depart,
             niveau_instruction, specialisation, specialisation_autre,
             langue_arabe, langue_anglaise, langue_francaise,
             autre_langue_nom, autre_langue_niveau,
             problemes_sante, nature_maladie,
             choix_travail,
             photo, cv, lettre_demande, carte_id, lettre_recommandation, 
             casier_judiciaire, diplome, status, date_soumission, form_language)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
        '''
        
        cursor.execute(query, (job_id, job_title, prenom, nom, email, telephone, adresse, pays, region,
              sexe, lieu_naissance, date_naissance, nationalite, etat_civil,
              travaille_actuellement, dernier_lieu_travail, raison_depart,
              niveau_instruction, specialisation, specialisation_autre,
              langue_arabe, langue_anglaise, langue_francaise,
              autre_langue_nom, autre_langue_niveau,
              problemes_sante, nature_maladie,
              choix_travail,
              photo, cv, lettre_demande, carte_id, lettre_recommandation,
              casier_judiciaire, diplome, 'en attente', date_soumission, form_language))
        
        conn.commit()
        app_id = cursor.lastrowid
        conn.close()
        
        print(f"   ✅ Candidature insérée dans la BDD avec ID: {app_id}")
        return app_id
        
    except Exception as e:
        print(f"   ❌ ERREUR SQL lors de la création de la candidature:")
        print(f"      Type: {type(e).__name__}")
        print(f"      Message: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        raise  # Re-lever l'exception pour que app.py puisse la gérer

def update_application_status(app_id, status):
    """Mettre à jour le statut d'une candidature"""
    conn = get_db_connection()
    conn.execute('UPDATE applications SET status = ? WHERE id = ?', (status, app_id))
    conn.commit()
    conn.close()

def delete_application(app_id):
    """Supprimer une candidature et tous ses fichiers associés"""
    # Récupérer d'abord les informations de la candidature
    application = get_application_by_id(app_id)
    
    if application:
        # Supprimer les fichiers physiques
        deleted_files = delete_application_files(application)
        print(f"📁 {deleted_files} fichier(s) supprimé(s) du système de fichiers")
    
    # Supprimer l'enregistrement de la base de données
    conn = get_db_connection()
    
    # Supprimer les codes de vérification associés
    verification_count = conn.execute(
        'SELECT COUNT(*) as count FROM document_verifications WHERE application_id = ?', 
        (app_id,)
    ).fetchone()['count']
    
    if verification_count > 0:
        conn.execute('DELETE FROM document_verifications WHERE application_id = ?', (app_id,))
        print(f"🔐 {verification_count} code(s) de vérification supprimé(s)")
    
    # Supprimer la candidature
    conn.execute('DELETE FROM applications WHERE id = ?', (app_id,))
    conn.commit()
    conn.close()

# ==================== STATISTIQUES ====================

def get_stats():
    """Récupérer les statistiques générales"""
    conn = get_db_connection()
    
    total_jobs = conn.execute('SELECT COUNT(*) as count FROM jobs').fetchone()['count']
    total_apps = conn.execute('SELECT COUNT(*) as count FROM applications').fetchone()['count']
    pending_apps = conn.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'en attente'").fetchone()['count']
    accepted_apps = conn.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'acceptée'").fetchone()['count']
    rejected_apps = conn.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'rejetée'").fetchone()['count']
    
    conn.close()
    
    return {
        'total_jobs': total_jobs,
        'total_applications': total_apps,
        'pending_applications': pending_apps,
        'accepted_applications': accepted_apps,
        'rejected_applications': rejected_apps
    }

# ============================================================================
# FONCTIONS DE WORKFLOW (2 PHASES)
# ============================================================================

def update_phase1_status(app_id, decision, interview_date=None, rejection_reason=None):
    """
    Mettre à jour le statut de la Phase 1
    
    Args:
        app_id: ID de la candidature
        decision: 'selected_for_interview' ou 'rejected'
        interview_date: Date de l'entretien (si sélectionné)
        rejection_reason: Raison du rejet (si rejeté)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    from datetime import datetime
    current_date = get_comoros_time().strftime('%Y-%m-%d %H:%M:%S')
    
    if decision == 'selected_for_interview':
        cursor.execute('''
            UPDATE applications 
            SET phase1_status = ?,
                phase1_date = ?,
                interview_date = ?,
                workflow_phase = 'phase1',
                status = 'interview programmé'
            WHERE id = ?
        ''', (decision, current_date, interview_date, app_id))
        
        # Générer le PDF de convocation à l'entretien
        try:
            import os
            from pdf_generator import generate_interview_invitation_pdf, generate_verification_code
            
            # Récupérer les données de la candidature
            application = cursor.execute('SELECT * FROM applications WHERE id = ?', (app_id,)).fetchone()
            
            if application:
                # Créer le dossier convocations s'il n'existe pas
                convocations_dir = os.path.join('static', 'convocations')
                os.makedirs(convocations_dir, exist_ok=True)
                
                # Nom du fichier PDF
                pdf_filename = f"convocation_{app_id}_{get_comoros_time().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_path = os.path.join(convocations_dir, pdf_filename)
                
                # Générer le code de vérification sécurisé (16 caractères hexadécimaux)
                verification_code = generate_verification_code(app_id, 'convocation')
                
                # Obtenir l'URL de base (à adapter selon votre déploiement)
                base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
                
                # Convertir application en dictionnaire si nécessaire
                if hasattr(application, 'keys'):
                    # C'est déjà un dict-like object (sqlite3.Row)
                    app_data = {key: application[key] for key in application.keys()}
                else:
                    # C'est un tuple, on doit récupérer les colonnes
                    columns = [description[0] for description in cursor.description]
                    app_data = dict(zip(columns, application))
                
                # Générer le PDF
                generate_interview_invitation_pdf(
                    application_data=app_data,
                    interview_date=interview_date,
                    output_path=pdf_path,
                    verification_code=verification_code,
                    base_url=base_url
                )
                
                # Sauvegarder le nom du fichier dans la base de données
                cursor.execute('UPDATE applications SET interview_invitation_pdf = ? WHERE id = ?', 
                             (pdf_filename, app_id))
                
                # ✅ ENREGISTRER LE CODE DE VÉRIFICATION DANS LA TABLE
                cursor.execute('''
                    INSERT INTO document_verifications 
                    (verification_code, application_id, document_type, candidate_name, job_title, issue_date, pdf_path, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    verification_code,
                    app_id,
                    'convocation',
                    f"{app_data['prenom']} {app_data['nom']}",
                    app_data.get('selected_job_title') or app_data['job_title'],
                    get_comoros_time().strftime('%d/%m/%Y'),
                    pdf_path,
                    'valide'
                ))
                
                conn.commit()
                
        except Exception as e:
            print(f"⚠️ Erreur lors de la génération du PDF de convocation: {e}")
            import traceback
            traceback.print_exc()
        
    elif decision == 'rejected':
        cursor.execute('''
            UPDATE applications 
            SET phase1_status = ?,
                phase1_date = ?,
                rejection_reason = ?,
                workflow_phase = 'completed',
                status = 'rejetée'
            WHERE id = ?
        ''', (decision, current_date, rejection_reason, app_id))
    
    conn.commit()
    conn.close()

def update_phase2_status(app_id, decision, work_start_date=None, rejection_reason=None):
    """
    Mettre à jour le statut de la Phase 2 (après interview)
    
    Args:
        app_id: ID de la candidature
        decision: 'accepted' ou 'rejected'
        work_start_date: Date de début de travail (si accepté)
        rejection_reason: Raison du rejet (si rejeté)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    from datetime import datetime
    current_date = get_comoros_time().strftime('%Y-%m-%d %H:%M:%S')
    
    if decision == 'accepted':
        cursor.execute('''
            UPDATE applications 
            SET phase2_status = ?,
                phase2_date = ?,
                work_start_date = ?,
                workflow_phase = 'completed',
                status = 'acceptée'
            WHERE id = ?
        ''', (decision, current_date, work_start_date, app_id))
    elif decision == 'rejected':
        cursor.execute('''
            UPDATE applications 
            SET phase2_status = ?,
                phase2_date = ?,
                rejection_reason = ?,
                workflow_phase = 'completed',
                status = 'rejetée'
            WHERE id = ?
        ''', (decision, current_date, rejection_reason, app_id))
    
    conn.commit()
    conn.close()

def mark_notification_sent(app_id, phase):
    """Marquer qu'une notification a été envoyée"""
    conn = get_db_connection()
    
    if phase == 1:
        conn.execute('UPDATE applications SET phase1_notification_sent = 1 WHERE id = ?', (app_id,))
    elif phase == 2:
        conn.execute('UPDATE applications SET phase2_notification_sent = 1 WHERE id = ?', (app_id,))
    
    conn.commit()
    conn.close()

def add_interview_notes(app_id, notes):
    """Ajouter des notes d'entretien"""
    conn = get_db_connection()
    conn.execute('UPDATE applications SET interview_notes = ? WHERE id = ?', (notes, app_id))
    conn.commit()
    conn.close()

def save_interview_invitation_pdf(app_id, pdf_filename_fr, pdf_filename_ar=None):
    """Sauvegarder les chemins des PDFs de convocation (FR + AR)"""
    conn = get_db_connection()
    if pdf_filename_ar:
        conn.execute('''
            UPDATE applications 
            SET interview_invitation_pdf = ?, interview_invitation_pdf_ar = ? 
            WHERE id = ?
        ''', (pdf_filename_fr, pdf_filename_ar, app_id))
    else:
        conn.execute('UPDATE applications SET interview_invitation_pdf = ? WHERE id = ?', (pdf_filename_fr, app_id))
    conn.commit()
    conn.close()

def get_interview_invitation_pdf(app_id, lang='fr'):
    """Récupérer le chemin du PDF de convocation (FR ou AR)"""
    conn = get_db_connection()
    if lang == 'ar':
        result = conn.execute('SELECT interview_invitation_pdf_ar FROM applications WHERE id = ?', (app_id,)).fetchone()
        conn.close()
        return result['interview_invitation_pdf_ar'] if result else None
    else:
        result = conn.execute('SELECT interview_invitation_pdf FROM applications WHERE id = ?', (app_id,)).fetchone()
        conn.close()
        return result['interview_invitation_pdf'] if result else None

def save_acceptance_letter_pdf(app_id, pdf_filename_fr, pdf_filename_ar=None):
    """Sauvegarder les chemins des PDFs de lettre d'acceptation (FR + AR)"""
    conn = get_db_connection()
    if pdf_filename_ar:
        conn.execute('''
            UPDATE applications 
            SET acceptance_letter_pdf = ?, acceptance_letter_pdf_ar = ? 
            WHERE id = ?
        ''', (pdf_filename_fr, pdf_filename_ar, app_id))
    else:
        conn.execute('UPDATE applications SET acceptance_letter_pdf = ? WHERE id = ?', (pdf_filename_fr, app_id))
    conn.commit()
    conn.close()

def get_acceptance_letter_pdf(app_id, lang='fr'):
    """Récupérer le chemin du PDF de lettre d'acceptation (FR ou AR)"""
    conn = get_db_connection()
    if lang == 'ar':
        result = conn.execute('SELECT acceptance_letter_pdf_ar FROM applications WHERE id = ?', (app_id,)).fetchone()
        conn.close()
        return result['acceptance_letter_pdf_ar'] if result else None
    else:
        result = conn.execute('SELECT acceptance_letter_pdf FROM applications WHERE id = ?', (app_id,)).fetchone()
        conn.close()
        return result['acceptance_letter_pdf'] if result else None
    conn = get_db_connection()
    result = conn.execute('SELECT acceptance_letter_pdf FROM applications WHERE id = ?', (app_id,)).fetchone()
    conn.close()
    return result['acceptance_letter_pdf'] if result else None

# ==================== FAVORIS ====================

def toggle_favorite(app_id):
    """Basculer le statut favori d'une candidature spontanée"""
    conn = get_db_connection()
    # Récupérer l'état actuel
    result = conn.execute('SELECT is_favorite, job_id FROM applications WHERE id = ?', (app_id,)).fetchone()
    
    if result:
        current_status = result['is_favorite']
        job_id = result['job_id']
        
        # Vérifier que c'est une candidature spontanée (job_id = NULL ou 0)
        if job_id is None or job_id == 0:
            new_status = 0 if current_status == 1 else 1
            conn.execute('UPDATE applications SET is_favorite = ? WHERE id = ?', (new_status, app_id))
            conn.commit()
            conn.close()
            return new_status
        else:
            conn.close()
            return None  # Ne pas permettre les favoris pour les candidatures normales
    
    conn.close()
    return None

def is_favorite(app_id):
    """Vérifier si une candidature est marquée comme favorite"""
    conn = get_db_connection()
    result = conn.execute('SELECT is_favorite FROM applications WHERE id = ?', (app_id,)).fetchone()
    conn.close()
    return result['is_favorite'] == 1 if result else False

def get_favorite_applications():
    """Récupérer toutes les candidatures spontanées favorites"""
    conn = get_db_connection()
    applications = conn.execute('''
        SELECT * FROM applications 
        WHERE (job_id IS NULL OR job_id = 0) AND is_favorite = 1 
        ORDER BY date_soumission DESC
    ''').fetchall()
    conn.close()
    return [dict(app) for app in applications]


# ==================== SYSTEM SETTINGS ====================

def are_spontaneous_applications_open():
    """Vérifier si les candidatures spontanées sont ouvertes"""
    conn = get_db_connection()
    try:
        result = conn.execute('''
            SELECT setting_value FROM system_settings 
            WHERE setting_key = 'spontaneous_applications_open'
        ''').fetchone()
        conn.close()
        
        if result:
            value = result['setting_value'] if isinstance(result, dict) else result[0]
            return value == 'true'
        return True  # Par défaut, ouvert
    except:
        conn.close()
        return True  # En cas d'erreur, considérer comme ouvert

def toggle_spontaneous_applications():
    """Activer/désactiver les candidatures spontanées"""
    conn = get_db_connection()
    current_status = are_spontaneous_applications_open()
    new_status = 'false' if current_status else 'true'
    
    conn.execute('''
        UPDATE system_settings 
        SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE setting_key = 'spontaneous_applications_open'
    ''', (new_status,))
    
    conn.commit()
    conn.close()
    
    return new_status == 'true'

def get_spontaneous_status_message(lang='fr'):
    """Obtenir le message de statut pour les candidatures spontanées"""
    is_open = are_spontaneous_applications_open()
    
    if is_open:
        return None  # Pas de message si ouvert
    
    messages = {
        'fr': {
            'title': '📋 Candidatures Spontanées Temporairement Fermées',
            'message': 'Suite à un grand nombre de candidatures reçues, nous avons temporairement suspendu les candidatures spontanées afin de traiter l\'ensemble des dossiers en attente.',
            'info': 'Les candidatures spontanées seront rouvertes prochainement. Merci de votre compréhension.'
        },
        'ar': {
            'title': '📋 الطلبات العفوية مغلقة مؤقتاً',
            'message': 'نظراً للعدد الكبير من الطلبات المستلمة، قمنا بتعليق الطلبات العفوية مؤقتاً من أجل معالجة جميع الملفات المعلقة.',
            'info': 'سيتم إعادة فتح الطلبات العفوية قريباً. شكراً لتفهمكم.'
        }
    }
    
    return messages.get(lang, messages['fr'])
