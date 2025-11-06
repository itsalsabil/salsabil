"""
Configuration et fonctions utilitaires pour Cloudinary
"""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from werkzeug.utils import secure_filename

def is_cloudinary_configured():
    """
    Vérifie si Cloudinary est configuré avec les variables d'environnement
    Returns:
        bool: True si toutes les variables Cloudinary sont présentes
    """
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
    
    return all([cloud_name, api_key, api_secret])

def configure_cloudinary():
    """
    Configure Cloudinary avec les variables d'environnement
    """
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True
    )

def upload_file_to_cloudinary(file, folder="salsabil_uploads"):
    """
    Upload un fichier vers Cloudinary avec optimisations et timeout
    
    Args:
        file: Fichier Flask (request.files)
        folder: Dossier de destination sur Cloudinary
        
    Returns:
        dict: {'success': bool, 'url': str, 'public_id': str, 'error': str}
    """
    try:
        # Configurer Cloudinary si nécessaire
        if not cloudinary.config().cloud_name:
            configure_cloudinary()
        
        # Sécuriser le nom de fichier
        filename = secure_filename(file.filename)
        
        # Lire le fichier en mémoire pour éviter les problèmes de pointeur
        file.seek(0)
        file_content = file.read()
        file.seek(0)  # Reset pour usage ultérieur si nécessaire
        
        # Upload vers Cloudinary avec timeout et optimisations
        result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            resource_type="auto",  # Détection automatique (image, pdf, etc.)
            use_filename=True,
            unique_filename=True,
            overwrite=False,
            timeout=60,  # Timeout de 60 secondes par fichier
            chunk_size=6000000,  # 6MB chunks pour uploads plus rapides
            eager_async=True  # Upload asynchrone des transformations
        )
        
        return {
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id']
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erreur upload Cloudinary: {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }

def delete_file_from_cloudinary(public_id):
    """
    Supprime un fichier de Cloudinary
    
    Args:
        public_id: L'identifiant public du fichier sur Cloudinary
        
    Returns:
        bool: True si la suppression a réussi
    """
    try:
        # Configurer Cloudinary si nécessaire
        if not cloudinary.config().cloud_name:
            configure_cloudinary()
        
        # Supprimer le fichier
        result = cloudinary.uploader.destroy(public_id)
        
        if result.get('result') == 'ok':
            print(f"☁️ Fichier Cloudinary supprimé: {public_id}")
            return True
        else:
            print(f"⚠️ Cloudinary: {public_id} - {result.get('result', 'not found')}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur suppression Cloudinary: {str(e)}")
        return False

def get_cloudinary_url(public_id, resource_type="image"):
    """
    Génère l'URL Cloudinary pour un fichier
    
    Args:
        public_id: L'identifiant public du fichier
        resource_type: Type de ressource (image, raw, video, auto)
        
    Returns:
        str: URL complète du fichier
    """
    try:
        if not cloudinary.config().cloud_name:
            configure_cloudinary()
        
        url, options = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type=resource_type,
            secure=True
        )
        return url
        
    except Exception as e:
        print(f"❌ Erreur génération URL Cloudinary: {str(e)}")
        return None
