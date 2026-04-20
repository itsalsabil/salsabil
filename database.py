import sqlite3
import psycopg2
import psycopg2.extras
from datetime import datetime
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.environ.get('DATABASE_URL')  # PostgreSQL sur Render
SQLITE_DATABASE = 'salsabil.db'  # Fallback pour développement local

class DatabaseConnection:
    """Wrapper pour gérer automatiquement les différences SQLite/PostgreSQL"""
    def __init__(self, conn):
        self.conn = conn
        self._cursor = None
        self._is_postgres = is_postgresql()
    
    def execute(self, query, params=None):
        """Execute avec conversion automatique des placeholders"""
        if self._is_postgres:
            query = query.replace('?', '%s')
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Retourner un wrapper qui convertit les résultats
        if self._is_postgres:
            return PostgresCursorResult(cursor)
        return cursor
    
    def cursor(self):
        """Retourne un cursor wrappé"""
        if is_postgresql():
            return PostgresCursor(self.conn.cursor())
        return self.conn.cursor()
    
    def commit(self):
        return self.conn.commit()
    
    def close(self):
        return self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        self.close()

class PostgresCursorResult:
    """Wrapper pour les résultats d'un simple execute (conn.execute)"""
    def __init__(self, cursor):
        self.cursor = cursor
    
    def fetchone(self):
        result = self.cursor.fetchone()
        if result and self.cursor.description:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, result))
        return result
    
    def fetchall(self):
        results = self.cursor.fetchall()
        if results and self.cursor.description:
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in results]
        return results

class PostgresCursor:
    """Wrapper pour cursor PostgreSQL qui convertit les placeholders"""
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None
    
    def execute(self, query, params=None):
        """Execute avec conversion automatique des placeholders"""
        query = query.replace('?', '%s')
        
        # PostgreSQL: Ajouter RETURNING id pour les INSERT
        if 'INSERT INTO' in query.upper() and 'RETURNING' not in query.upper():
            # Trouver la fin de la requête et ajouter RETURNING id
            query = query.rstrip().rstrip(';') + ' RETURNING id'
        
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        
        # Récupérer le lastrowid pour PostgreSQL
        if 'INSERT INTO' in query.upper() and 'RETURNING' in query.upper():
            try:
                result = self.cursor.fetchone()
                self.lastrowid = result[0] if result else None
            except:
                self.lastrowid = None
        
        return self.cursor
    
    def executemany(self, query, params_list):
        """Execute many avec conversion automatique"""
        query = query.replace('?', '%s')
        return self.cursor.executemany(query, params_list)
    
    def fetchone(self):
        result = self.cursor.fetchone()
        if result and is_postgresql():
            # Convertir tuple en dict pour compatibilité avec sqlite3.Row
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, result))
        return result
    
    def fetchall(self):
        results = self.cursor.fetchall()
        if results and is_postgresql():
            # Convertir tuples en dicts
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in results]
        return results
    
    @property
    def rowcount(self):
        return self.cursor.rowcount
    
    @property
    def description(self):
        return self.cursor.description

def get_db_connection():
    """Créer une connexion à la base de données (PostgreSQL si DATABASE_URL existe, sinon SQLite)"""
    if DATABASE_URL:
        # Mode Production: PostgreSQL sur Render
        conn = psycopg2.connect(DATABASE_URL)
        return DatabaseConnection(conn)
    else:
        # Mode Développement: SQLite local
        conn = sqlite3.connect(SQLITE_DATABASE)
        conn.row_factory = sqlite3.Row
        return DatabaseConnection(conn)

def is_postgresql():
    """Vérifier si on utilise PostgreSQL ou SQLite"""
    return DATABASE_URL is not None

def migrate_add_bilingual_columns():
    """Ajouter les colonnes bilingues à la table jobs si elles n'existent pas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgresql():
            # PostgreSQL - vérifier et ajouter les colonnes
            cursor.execute('''
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='jobs' AND column_name='titre_ar'
            ''')
            if not cursor.fetchone():
                cursor.execute('ALTER TABLE jobs ADD COLUMN titre_ar VARCHAR(500)')
                print("✅ Colonne titre_ar ajoutée")
            
            cursor.execute('''
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='jobs' AND column_name='lieu_ar'
            ''')
            if not cursor.fetchone():
                cursor.execute('ALTER TABLE jobs ADD COLUMN lieu_ar VARCHAR(255)')
                print("✅ Colonne lieu_ar ajoutée")
            
            cursor.execute('''
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='jobs' AND column_name='description_ar'
            ''')
            if not cursor.fetchone():
                cursor.execute('ALTER TABLE jobs ADD COLUMN description_ar TEXT')
                print("✅ Colonne description_ar ajoutée")
            
            cursor.execute('''
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='jobs' AND column_name='requirements_ar'
            ''')
            if not cursor.fetchone():
                cursor.execute('ALTER TABLE jobs ADD COLUMN requirements_ar TEXT')
                print("✅ Colonne requirements_ar ajoutée")
            
            cursor.execute('''
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='jobs' AND column_name='department_ar'
            ''')
            if not cursor.fetchone():
                cursor.execute('ALTER TABLE jobs ADD COLUMN department_ar VARCHAR(255)')
                print("✅ Colonne department_ar ajoutée")
            
            cursor.execute('''
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='jobs' AND column_name='langues_requises'
            ''')
            if not cursor.fetchone():
                cursor.execute('ALTER TABLE jobs ADD COLUMN langues_requises VARCHAR(255)')
                print("✅ Colonne langues_requises ajoutée")
        else:
            # SQLite - vérifier et ajouter les colonnes
            cursor.execute('PRAGMA table_info(jobs)')
            columns = {row[1] for row in cursor.fetchall()}
            
            if 'titre_ar' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN titre_ar TEXT')
                print("✅ Colonne titre_ar ajoutée")
            
            if 'lieu_ar' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN lieu_ar TEXT')
                print("✅ Colonne lieu_ar ajoutée")
            
            if 'description_ar' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN description_ar TEXT')
                print("✅ Colonne description_ar ajoutée")
            
            if 'requirements_ar' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN requirements_ar TEXT')
                print("✅ Colonne requirements_ar ajoutée")
            
            if 'department_ar' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN department_ar TEXT')
                print("✅ Colonne department_ar ajoutée")
            
            if 'langues_requises' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN langues_requises TEXT')
                print("✅ Colonne langues_requises ajoutée")
        
        conn.commit()
        conn.close()
        print("✅ Migration des colonnes bilingues complétée")
    except Exception as e:
        print(f"⚠️  Erreur lors de la migration: {e}")
        conn.close()

def init_db():
    """Initialiser la base de données avec les tables nécessaires"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Déterminer le type de base de données
    if is_postgresql():
        # PostgreSQL - Utiliser SERIAL au lieu de AUTOINCREMENT
        # Table des employés
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                prenom VARCHAR(255) NOT NULL,
                nom VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                role VARCHAR(50) NOT NULL,
                status VARCHAR(50) DEFAULT 'actif',
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        # SQLite - Utiliser AUTOINCREMENT
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                prenom TEXT NOT NULL,
                nom TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'actif',
                date_creation TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    # Table des jobs
    if is_postgresql():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                titre VARCHAR(500) NOT NULL,
                titre_ar VARCHAR(500),
                type VARCHAR(100) NOT NULL,
                lieu VARCHAR(255) NOT NULL,
                lieu_ar VARCHAR(255),
                description TEXT NOT NULL,
                description_ar TEXT,
                requirements TEXT,
                requirements_ar TEXT,
                department VARCHAR(255),
                department_ar VARCHAR(255),
                langues_requises VARCHAR(255),
                date_limite DATE NOT NULL,
                date_publication TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL,
                titre_ar TEXT,
                type TEXT NOT NULL,
                lieu TEXT NOT NULL,
                lieu_ar TEXT,
                description TEXT NOT NULL,
                description_ar TEXT,
                requirements TEXT,
                requirements_ar TEXT,
                department TEXT,
                department_ar TEXT,
                date_limite TEXT NOT NULL,
                date_publication TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    # Table des candidatures
    if is_postgresql():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id SERIAL PRIMARY KEY,
                job_id INTEGER,
                job_title VARCHAR(500) NOT NULL,
                prenom VARCHAR(255) NOT NULL,
                nom VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                telephone VARCHAR(50) NOT NULL,
                adresse TEXT NOT NULL,
                pays VARCHAR(100),
                region VARCHAR(255),
                sexe VARCHAR(20),
                lieu_naissance VARCHAR(255),
                date_naissance DATE,
                nationalite VARCHAR(100),
                etat_civil VARCHAR(50),
                travaille_actuellement VARCHAR(50),
                dernier_lieu_travail VARCHAR(500),
                raison_depart TEXT,
                niveau_instruction VARCHAR(100),
                specialisation VARCHAR(255),
                specialisation_autre VARCHAR(255),
                langue_arabe VARCHAR(50),
                langue_anglaise VARCHAR(50),
                langue_francaise VARCHAR(50),
                autre_langue_nom VARCHAR(100),
                autre_langue_niveau VARCHAR(50),
                problemes_sante VARCHAR(50),
                nature_maladie TEXT,
                choix_travail TEXT,
                photo VARCHAR(500),
                cv VARCHAR(500) NOT NULL,
                lettre_demande TEXT,
                carte_id VARCHAR(500) NOT NULL,
                lettre_recommandation VARCHAR(500),
                casier_judiciaire VARCHAR(500),
                diplome VARCHAR(500),
                certificat_travail VARCHAR(500),
                status VARCHAR(50) DEFAULT 'en attente',
                date_soumission TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                workflow_phase VARCHAR(50) DEFAULT 'phase1',
                phase1_status VARCHAR(50) DEFAULT 'pending',
                phase1_date DATE,
                phase1_notification_sent INTEGER DEFAULT 0,
                interview_date DATE,
                interview_notes TEXT,
                interview_invitation_pdf VARCHAR(500),
                interview_invitation_pdf_ar VARCHAR(500),
                phase2_status VARCHAR(50),
                phase2_date DATE,
                phase2_notification_sent INTEGER DEFAULT 0,
                work_start_date DATE,
                rejection_reason TEXT,
                selected_job_title VARCHAR(500),
                is_favorite INTEGER DEFAULT 0,
                acceptance_letter_pdf VARCHAR(500),
                acceptance_letter_pdf_ar VARCHAR(500),
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE SET NULL
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                job_title TEXT NOT NULL,
                prenom TEXT NOT NULL,
                nom TEXT NOT NULL,
                email TEXT NOT NULL,
                telephone TEXT NOT NULL,
                adresse TEXT NOT NULL,
                date_naissance TEXT,
                nationalite TEXT,
                photo TEXT,
                cv TEXT NOT NULL,
                lettre_demande TEXT,
                carte_id TEXT NOT NULL,
                lettre_recommandation TEXT,
                casier_judiciaire TEXT,
                diplome TEXT,
                status TEXT DEFAULT 'en attente',
                date_soumission TEXT DEFAULT CURRENT_TIMESTAMP,
                workflow_phase TEXT DEFAULT 'phase1',
                phase1_status TEXT DEFAULT 'pending',
                phase1_date TEXT,
                phase1_notification_sent INTEGER DEFAULT 0,
                interview_date TEXT,
                interview_notes TEXT,
                interview_invitation_pdf TEXT,
                interview_invitation_pdf_ar TEXT,
                phase2_status TEXT,
                phase2_date TEXT,
                phase2_notification_sent INTEGER DEFAULT 0,
                work_start_date TEXT,
                rejection_reason TEXT,
                acceptance_letter_pdf TEXT,
                acceptance_letter_pdf_ar TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
        ''')
    
    # Table des codes de vérification des documents
    if is_postgresql():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_verifications (
                id SERIAL PRIMARY KEY,
                verification_code VARCHAR(255) UNIQUE NOT NULL,
                application_id INTEGER NOT NULL,
                document_type VARCHAR(50) NOT NULL,
                candidate_name VARCHAR(500) NOT NULL,
                job_title VARCHAR(500) NOT NULL,
                issue_date VARCHAR(50) NOT NULL,
                pdf_path VARCHAR(500),
                status VARCHAR(50) DEFAULT 'valide',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications (id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verification_code TEXT UNIQUE NOT NULL,
                application_id INTEGER NOT NULL,
                document_type TEXT NOT NULL,
                candidate_name TEXT NOT NULL,
                job_title TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                pdf_path TEXT,
                status TEXT DEFAULT 'valide',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications (id)
            )
        ''')
        
    # Fin du bloc SQLite document_verifications

    # Table pour les paramètres système (créée pour les deux SGBD)
    if is_postgresql():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id SERIAL PRIMARY KEY,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    conn.commit()
    
    # Initialiser le paramètre des candidatures spontanées
    # PostgreSQL compatible syntax
    cursor.execute('''
        INSERT INTO system_settings (setting_key, setting_value)
        VALUES ('spontaneous_applications_open', 'true')
        ON CONFLICT (setting_key) DO NOTHING
    ''')
    
    conn.commit()
    
    # Exécuter les migrations pour ajouter les colonnes bilingues manquantes
    migrate_add_bilingual_columns()
    
    # Insérer les employés par défaut s'ils n'existent pas
    cursor.execute('SELECT COUNT(*) as count FROM employees')
    count_result = cursor.fetchone()
    
    # Gérer le résultat selon le type (dict pour PostgreSQL, tuple pour SQLite via wrapper)
    if isinstance(count_result, dict):
        employee_count = count_result.get('count', 0)
    else:
        employee_count = count_result[0] if count_result else 0
    
    # Déterminer le placeholder à utiliser
    if is_postgresql():
        placeholder = '%s'
    else:
        placeholder = '?'
    
    if employee_count == 0:
        default_employees = [
            ('admin', 'admin123', 'Super', 'Admin', 'admin@salsabil.com', 'admin', 'actif'),
            ('hr', 'hr123', 'Sarah', 'Martin', 'hr@salsabil.com', 'hr', 'actif'),
            ('recruteur', 'rec123', 'Pierre', 'Dupont', 'recruteur@salsabil.com', 'recruteur', 'actif')
        ]
        
        cursor.executemany(f'''
            INSERT INTO employees (username, password, prenom, nom, email, role, status)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        ''', default_employees)
        
        conn.commit()
        print("✅ Employés par défaut créés")
    
    # Créer un job fictif avec id=0 pour les candidatures spontanées (nécessaire pour PostgreSQL FK)
    cursor.execute('SELECT COUNT(*) as count FROM jobs WHERE id = 0')
    count_result = cursor.fetchone()
    
    if isinstance(count_result, dict):
        job_exists = count_result.get('count', 0) > 0
    else:
        job_exists = (count_result[0] if count_result else 0) > 0
    
    # Note: Les candidatures spontanées utilisent job_id = NULL, pas besoin de job placeholder
    
    conn.close()
    print("✅ Base de données initialisée avec succès!")

def reset_db():
    """Réinitialiser complètement la base de données"""
    if not DATABASE_URL and os.path.exists(SQLITE_DATABASE):
        os.remove(SQLITE_DATABASE)
        print("🗑️  Ancienne base de données SQLite supprimée")
    elif DATABASE_URL:
        print("⚠️  La réinitialisation de PostgreSQL doit être faite manuellement")
        return
    init_db()

if __name__ == '__main__':
    print("Initialisation de la base de données...")
    init_db()
