"""
Module de notifications pour le workflow de recrutement
Gère l'envoi d'emails et de messages WhatsApp
"""

import urllib.parse
from datetime import datetime

# ============================================================================
# TEMPLATES DE MESSAGES
# ============================================================================

def get_phase1_selected_message(candidate_name, job_title, interview_date, has_pdf=False):
    """Message pour candidat sélectionné pour interview"""
    email_subject = f"🎉 Félicitations {candidate_name} - Entretien pour {job_title}"
    
    pdf_note = """
⚠️ IMPORTANT : Vous trouverez en pièce jointe votre CONVOCATION OFFICIELLE.
Ce document est OBLIGATOIRE pour accéder à nos locaux. Veuillez le présenter à l'accueil le jour de l'entretien.
""" if has_pdf else ""
    
    email_body = f"""
Bonjour {candidate_name},

Nous avons le plaisir de vous informer que votre candidature pour le poste de {job_title} a retenu notre attention.

Nous souhaitons vous rencontrer pour un entretien qui aura lieu le {interview_date}.
{pdf_note}
Merci de confirmer votre présence en répondant à ce message.

Cordialement,
L'équipe de recrutement
Salsabil
"""
    
    whatsapp_pdf_note = """

⚠️ IMPORTANT : Vous recevrez également par email votre CONVOCATION OFFICIELLE (PDF).
Ce document est OBLIGATOIRE pour accéder à nos locaux le jour de l'entretien.""" if has_pdf else ""
    
    whatsapp_message = f"""Bonjour {candidate_name}, 

Félicitations ! Nous avons le plaisir de vous informer que votre candidature pour le poste de {job_title} a été retenue.

Nous souhaitons vous rencontrer pour un entretien le {interview_date}.{whatsapp_pdf_note}

Merci de confirmer votre présence.

Cordialement,
L'équipe Salsabil"""
    
    return {
        'email_subject': email_subject,
        'email_body': email_body,
        'whatsapp_message': whatsapp_message
    }

def get_phase1_rejected_message(candidate_name, job_title, rejection_reason=None):
    """Message pour candidat rejeté en Phase 1"""
    email_subject = f"Candidature pour {job_title}"
    
    email_body = f"""
Bonjour {candidate_name},

Nous vous remercions pour l'intérêt que vous portez à notre entreprise et pour le temps consacré à votre candidature pour le poste de {job_title}.

Après avoir étudié attentivement votre profil, nous sommes au regret de vous informer que nous ne pouvons pas donner suite à votre candidature pour ce poste.

{'Raison : ' + rejection_reason if rejection_reason else 'Cette décision ne remet pas en question vos qualités professionnelles.'}

Nous conservons votre candidature dans notre base de données et n'hésiterons pas à vous recontacter si une opportunité correspondant à votre profil se présente.

Nous vous souhaitons plein succès dans vos recherches.

Cordialement,
L'équipe de recrutement
Salsabil
"""
    
    whatsapp_message = f"""Bonjour {candidate_name},

Nous vous remercions pour votre candidature au poste de {job_title}.

Après étude de votre profil, nous ne pouvons malheureusement pas donner suite à votre candidature pour ce poste.

Nous conservons votre CV et vous recontacterons si une opportunité correspondant à votre profil se présente.

Cordialement,
L'équipe Salsabil"""
    
    return {
        'email_subject': email_subject,
        'email_body': email_body,
        'whatsapp_message': whatsapp_message
    }

def get_phase2_accepted_message(candidate_name, job_title):
    """Message pour candidat accepté après interview"""
    email_subject = f"🎊 Bienvenue dans l'équipe Salsabil - {job_title}"
    
    email_body = f"""
Bonjour {candidate_name},

Nous sommes ravis de vous informer que suite à votre entretien, nous avons le plaisir de vous proposer le poste de {job_title} au sein de notre entreprise.

Votre profil, vos compétences et votre motivation nous ont convaincus que vous serez un excellent ajout à notre équipe.

Nous prendrons contact avec vous très prochainement pour discuter des détails de votre intégration (date de début, contrat, etc.).

Bienvenue dans l'équipe Salsabil ! 🎉

Cordialement,
L'équipe de recrutement
Salsabil
"""
    
    whatsapp_message = f"""Bonjour {candidate_name},

Excellente nouvelle ! 🎊

Nous sommes ravis de vous proposer le poste de {job_title} au sein de Salsabil.

Nous prendrons contact avec vous très prochainement pour finaliser les détails.

Bienvenue dans l'équipe ! 🎉

Cordialement,
L'équipe Salsabil"""
    
    return {
        'email_subject': email_subject,
        'email_body': email_body,
        'whatsapp_message': whatsapp_message
    }

def get_phase2_rejected_message(candidate_name, job_title, rejection_reason=None):
    """Message pour candidat rejeté après interview"""
    email_subject = f"Suite à votre entretien - {job_title}"
    
    email_body = f"""
Bonjour {candidate_name},

Nous vous remercions d'avoir pris le temps de participer à l'entretien pour le poste de {job_title}.

Après mûre réflexion, nous avons décidé de poursuivre avec un autre candidat dont le profil correspond davantage aux besoins spécifiques du poste.

{'Retour : ' + rejection_reason if rejection_reason else 'Nous avons apprécié notre échange et tenons à souligner vos qualités professionnelles.'}

Nous conservons votre candidature et n'hésiterons pas à vous recontacter pour de futures opportunités.

Nous vous souhaitons plein succès dans vos projets professionnels.

Cordialement,
L'équipe de recrutement
Salsabil
"""
    
    whatsapp_message = f"""Bonjour {candidate_name},

Merci d'avoir participé à l'entretien pour le poste de {job_title}.

Après réflexion, nous avons décidé de poursuivre avec un autre candidat.

Nous avons apprécié notre échange et conservons votre candidature pour de futures opportunités.

Cordialement,
L'équipe Salsabil"""
    
    return {
        'email_subject': email_subject,
        'email_body': email_body,
        'whatsapp_message': whatsapp_message
    }

# ============================================================================
# FONCTIONS DE GÉNÉRATION DE LIENS
# ============================================================================

def generate_email_link(to_email, subject, body):
    """Générer un lien mailto: avec sujet et corps pré-remplis"""
    encoded_subject = urllib.parse.quote(subject)
    encoded_body = urllib.parse.quote(body)
    return f"mailto:{to_email}?subject={encoded_subject}&body={encoded_body}"

def generate_whatsapp_link(phone, message):
    """Générer un lien WhatsApp avec message pré-rempli"""
    # Nettoyer le numéro de téléphone
    cleaned_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{cleaned_phone}?text={encoded_message}"

def format_phone_for_whatsapp(phone):
    """Formater un numéro de téléphone pour WhatsApp (avec indicatif pays si nécessaire)"""
    cleaned = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Si le numéro commence par 0, ajouter l'indicatif du Maroc (+212)
    if cleaned.startswith('0'):
        cleaned = '212' + cleaned[1:]
    elif not cleaned.startswith('+') and not cleaned.startswith('212'):
        cleaned = '212' + cleaned
    
    return cleaned

# ============================================================================
# FONCTION PRINCIPALE DE NOTIFICATION
# ============================================================================

def prepare_notification(application, phase, decision, interview_date=None, rejection_reason=None, pdf_path=None):
    """
    Préparer les notifications pour une décision de workflow
    
    Args:
        application: Dictionnaire contenant les infos du candidat
        phase: 1 ou 2
        decision: 'selected_for_interview', 'rejected', 'accepted'
        interview_date: Date de l'entretien (Phase 1, sélection)
        rejection_reason: Raison du rejet (optionnel)
        pdf_path: Chemin vers le PDF de convocation (Phase 1, sélection)
    
    Returns:
        dict: Contient les liens email et WhatsApp avec messages pré-remplis
    """
    candidate_name = f"{application['prenom']} {application['nom']}"
    job_title = application['job_title']
    email = application['email']
    phone = application['telephone']
    
    # Sélectionner le template approprié
    if phase == 1:
        if decision == 'selected_for_interview':
            has_pdf = pdf_path is not None
            messages = get_phase1_selected_message(candidate_name, job_title, interview_date, has_pdf)
        else:  # rejected
            messages = get_phase1_rejected_message(candidate_name, job_title, rejection_reason)
    else:  # phase == 2
        if decision == 'accepted':
            messages = get_phase2_accepted_message(candidate_name, job_title)
        else:  # rejected
            messages = get_phase2_rejected_message(candidate_name, job_title, rejection_reason)
    
    # Générer les liens
    email_link = generate_email_link(email, messages['email_subject'], messages['email_body'])
    whatsapp_link = generate_whatsapp_link(phone, messages['whatsapp_message'])
    
    result = {
        'email_link': email_link,
        'whatsapp_link': whatsapp_link,
        'email_subject': messages['email_subject'],
        'email_body': messages['email_body'],
        'whatsapp_message': messages['whatsapp_message']
    }
    
    # Ajouter le chemin du PDF si disponible
    if pdf_path:
        result['pdf_path'] = pdf_path
    
    return result
