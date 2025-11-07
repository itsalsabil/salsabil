"""
Module de génération de documents PDF pour le recrutement
Génère des convocations d'entretien officielles avec QR code de vérification
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import qrcode
from io import BytesIO
import hashlib
import hashlib
import secrets

# Bibliothèques pour le reshape de l'arabe
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
    print("✅ Support arabe activé (arabic-reshaper + python-bidi)")
except ImportError:
    ARABIC_SUPPORT = False
    print("⚠️ Bibliothèques arabe manquantes. Installez: pip install arabic-reshaper python-bidi")

# Enregistrer les polices Unicode qui supportent l'arabe
FONT_NAME = 'Helvetica'
FONT_NAME_BOLD = 'Helvetica-Bold'

try:
    # Essayer d'utiliser Amiri (police dédiée à l'arabe) dans le dossier local
    amiri_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Amiri-Regular.ttf')
    amiri_bold_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Amiri-Bold.ttf')
    
    if os.path.exists(amiri_path):
        pdfmetrics.registerFont(TTFont('Amiri', amiri_path))
        if os.path.exists(amiri_bold_path):
            pdfmetrics.registerFont(TTFont('Amiri-Bold', amiri_bold_path))
            FONT_NAME_BOLD = 'Amiri-Bold'
        else:
            FONT_NAME_BOLD = 'Amiri'
        FONT_NAME = 'Amiri'
        print("✅ Police Amiri chargée (excellent support de l'arabe)")
    else:
        raise FileNotFoundError("Amiri non trouvée localement")
except Exception as e:
    try:
        # Fallback 1: Arial Unicode (macOS)
        pdfmetrics.registerFont(TTFont('ArialUnicode', '/Library/Fonts/Arial Unicode.ttf'))
        FONT_NAME = 'ArialUnicode'
        FONT_NAME_BOLD = 'ArialUnicode'
        print("✅ Police Arial Unicode chargée (support de l'arabe)")
    except Exception as e2:
        try:
            # Fallback 2: DejaVu Sans (macOS)
            pdfmetrics.registerFont(TTFont('DejaVu', '/System/Library/Fonts/Supplemental/DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', '/System/Library/Fonts/Supplemental/DejaVuSans-Bold.ttf'))
            FONT_NAME = 'DejaVu'
            FONT_NAME_BOLD = 'DejaVu-Bold'
            print("✅ Police DejaVu chargée (support de l'arabe)")
        except Exception as e3:
            # Dernier recours: Helvetica (pas d'arabe)
            FONT_NAME = 'Helvetica'
            FONT_NAME_BOLD = 'Helvetica-Bold'
            print("⚠️ ATTENTION: Aucune police Unicode trouvée!")
            print("   Les caractères arabes s'afficheront comme des carrés ■")
            print(f"   Erreurs: Amiri={e}, Arial={e2}, DejaVu={e3}")


# ============================================================================
# DICTIONNAIRES DE TRADUCTION POUR LES PDF
# ============================================================================

INVITATION_TEXTS = {
    'fr': {
        'issued': 'Émis le',
        'title': 'CONVOCATION À UN ENTRETIEN',
        'company_name': 'SALSABIL',
        'company_subtitle': 'Entreprise de Recrutement',
        'attention': 'À l\'attention de :',
        'greeting': 'Madame, Monsieur',
        'intro_1': 'Suite à votre candidature pour le poste de',
        'intro_2': 'nous avons le plaisir de vous informer que votre profil a retenu notre attention.',
        'convocation': 'Nous souhaitons vous rencontrer afin d\'échanger sur votre parcours, vos compétences et vos motivations.',
        'please_present': 'Nous vous prions de bien vouloir vous présenter à notre siège aux date et heure suivantes :',
        'interview_info': 'Informations de l\'entretien',
        'date': 'Date',
        'time': 'Heure',
        'address': 'Adresse',
        'position': 'Poste',
        'contact': 'Contact',
        'instructions': 'Veuillez vous présenter muni(e) de cette convocation et d\'une pièce d\'identité.',
        'closing': 'Nous comptons sur votre présence et restons à votre disposition pour toute information complémentaire.',
        'signature': 'Cordialement,',
        'hr_team': 'L\'équipe Ressources Humaines',
        'verification_title': 'Vérification du document',
        'verification_text': 'Ce document est authentique. Scannez le QR code pour vérifier en ligne.',
        'verification_code': 'Code de vérification'
    },
    'ar': {
        'issued': 'صدر في',
        'title': 'دعوة لإجراء مقابلة',
        'company_name': 'السلسبيل',
        'company_subtitle': 'شركة التوظيف',
        'attention': 'إلى عناية:',
        'greeting': 'السيدة، السيد',
        'intro_1': 'بعد تقديمكم لطلب التوظيف لمنصب',
        'intro_2': 'يسعدنا أن نعلمكم بأن ملفكم الشخصي قد نال اهتمامنا.',
        'convocation': 'نود أن نلتقي بكم لمناقشة مسيرتكم المهنية ومهاراتكم ودوافعكم.',
        'please_present': 'يرجى التفضل بالحضور إلى مقرنا في التاريخ والوقت التاليين:',
        'interview_info': 'معلومات المقابلة',
        'date': 'التاريخ',
        'time': 'الوقت',
        'address': 'العنوان',
        'position': 'المنصب',
        'contact': 'الاتصال',
        'instructions': 'يرجى الحضور مع هذه الدعوة وبطاقة الهوية.',
        'closing': 'نتطلع إلى حضوركم ونبقى تحت تصرفكم لأي معلومات إضافية.',
        'signature': 'مع خالص التحيات،',
        'hr_team': 'فريق الموارد البشرية',
        'verification_title': 'التحقق من الوثيقة',
        'verification_text': 'هذه الوثيقة أصلية. امسح رمز الاستجابة السريعة للتحقق عبر الإنترنت.',
        'verification_code': 'رمز التحقق'
    }
}

ACCEPTANCE_TEXTS = {
    'fr': {
        'issued': 'Émis le',
        'title': 'LETTRE D\'ACCEPTATION',
        'company_name': 'SALSABIL',
        'company_subtitle': 'Entreprise de Recrutement',
        'attention': 'À l\'attention de :',
        'congratulations': 'Félicitations !',
        'greeting': 'Madame, Monsieur',
        'acceptance_msg_1': 'Nous avons le grand plaisir de vous informer que votre candidature pour le poste de',
        'acceptance_msg_2': 'a été retenue.',
        'integration': 'Nous vous souhaitons la bienvenue au sein de notre équipe et sommes impatients de collaborer avec vous.',
        'contract_details': 'Détails du contrat',
        'position': 'Poste',
        'start_date': 'Date de début',
        'contract_type': 'Type de contrat',
        'salary': 'Salaire',
        'next_steps': 'Prochaines étapes',
        'documents': 'Veuillez nous fournir les documents suivants avant votre prise de poste :',
        'id_copy': 'Copie de pièce d\'identité',
        'cv': 'CV actualisé',
        'diploma_copies': 'Copies des diplômes',
        'photos': 'Photos d\'identité',
        'medical_cert': 'Certificat médical',
        'closing': 'Nous sommes convaincus que votre intégration sera une réussite et nous réjouissons de vous compter parmi nous.',
        'signature': 'Cordialement,',
        'hr_team': 'L\'équipe Ressources Humaines',
        'verification_title': 'Vérification du document',
        'verification_text': 'Ce document est authentique. Scannez le QR code pour vérifier en ligne.',
        'verification_code': 'Code de vérification'
    },
    'ar': {
        'issued': 'صدر في',
        'title': 'خطاب القبول',
        'company_name': 'السلسبيل',
        'company_subtitle': 'شركة التوظيف',
        'attention': 'إلى عناية:',
        'congratulations': 'تهانينا!',
        'greeting': 'السيدة، السيد',
        'acceptance_msg_1': 'يسعدنا أن نعلمكم بأنه تم قبول طلبكم لمنصب',
        'acceptance_msg_2': 'مع تهانينا الحارة.',
        'integration': 'نرحب بكم في فريقنا ونتطلع إلى التعاون معكم.',
        'contract_details': 'تفاصيل العقد',
        'position': 'المنصب',
        'start_date': 'تاريخ البداية',
        'contract_type': 'نوع العقد',
        'salary': 'الراتب',
        'next_steps': 'الخطوات القادمة',
        'documents': 'يرجى تزويدنا بالوثائق التالية قبل تاريخ البداية:',
        'id_copy': 'نسخة من بطاقة الهوية',
        'cv': 'السيرة الذاتية محدثة',
        'diploma_copies': 'نسخ من الشهادات',
        'photos': 'صور شخصية',
        'medical_cert': 'شهادة طبية',
        'closing': 'نحن واثقون من أن انضمامكم سيكون ناجحاً ونتطلع إلى العمل معكم.',
        'signature': 'مع خالص التحيات،',
        'hr_team': 'فريق الموارد البشرية',
        'verification_title': 'التحقق من الوثيقة',
        'verification_text': 'هذه الوثيقة أصلية. امسح رمز الاستجابة السريعة للتحقق عبر الإنترنت.',
        'verification_code': 'رمز التحقق'
    }
}


def generate_verification_code(application_id, document_type):
    """
    Générer un code de vérification unique et sécurisé
    
    Args:
        application_id: ID de la candidature
        document_type: Type de document (convocation ou acceptation)
    
    Returns:
        str: Code de vérification unique
    """
    # Créer une chaîne unique basée sur l'ID, le type et un sel aléatoire
    timestamp = datetime.now().isoformat()
    random_salt = secrets.token_hex(16)
    data = f"{application_id}-{document_type}-{timestamp}-{random_salt}"
    
    # Générer un hash SHA256
    verification_hash = hashlib.sha256(data.encode()).hexdigest()
    
    # Retourner les 16 premiers caractères du hash (suffisant et plus lisible)
    return verification_hash[:16].upper()


def create_qr_code(verification_url):
    """
    Créer un QR code pour l'URL de vérification
    
    Args:
        verification_url: URL complète de vérification du document
    
    Returns:
        BytesIO: Image du QR code en mémoire
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    # Créer l'image du QR code
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir en BytesIO pour ReportLab
    img_buffer = BytesIO()
    qr_image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer


def reshape_arabic_text(text, lang='fr'):
    """
    Reshape le texte arabe pour qu'il s'affiche correctement dans les PDFs
    
    Args:
        text: Le texte à reshaper
        lang: La langue ('ar' pour arabe, 'fr' pour français)
    
    Returns:
        str: Le texte reshaped (pour l'arabe) ou original (pour le français)
    """
    if lang != 'ar' or not ARABIC_SUPPORT or not text:
        return text
    
    try:
        # Reshaper le texte arabe (connecter les lettres)
        reshaped_text = arabic_reshaper.reshape(text)
        # Appliquer l'algorithme bidi (right-to-left)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception as e:
        print(f"⚠️ Erreur reshape arabe: {e}")
        return text


def generate_interview_invitation_pdf(application_data, interview_date, output_path, verification_code=None, base_url="http://localhost:5000", lang='fr'):
    """
    Générer un PDF de convocation à l'entretien (français ou arabe)
    
    Args:
        application_data: Dictionnaire contenant les infos du candidat
        interview_date: Date et heure de l'entretien (format: "2025-10-15 14:00")
        output_path: Chemin où sauvegarder le PDF
        verification_code: Code de vérification du document
        base_url: URL de base pour le QR code
        lang: Langue du document ('fr' ou 'ar')
    
    Returns:
        str: Chemin du fichier PDF généré
    """
    
    # Récupérer les traductions
    print(f"🌍 Génération PDF avec langue: {lang}")
    print(f"🔍 Clés disponibles dans INVITATION_TEXTS: {list(INVITATION_TEXTS.keys())}")
    
    # S'assurer que lang est bien une chaîne et enlever les espaces
    lang = str(lang).strip().lower()
    print(f"🔍 Langue normalisée: '{lang}'")
    
    if lang == 'ar':
        t = INVITATION_TEXTS['ar']
        print(f"✅ Utilisation du dictionnaire ARABE")
    else:
        t = INVITATION_TEXTS['fr']
        print(f"✅ Utilisation du dictionnaire FRANÇAIS")
    
    print(f"📝 Titre utilisé: {t['title']}")
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Container pour les éléments du document
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Alignement selon la langue (RTL pour arabe)
    text_alignment = TA_RIGHT if lang == 'ar' else TA_JUSTIFY
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24 if lang == 'ar' else 22,  # Arabe: 24, Français: 22
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        alignment=TA_CENTER,  # Titre toujours centré
        fontName=FONT_NAME_BOLD
    )
    
    # Style pour le sous-titre
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=15 if lang == 'ar' else 14,  # Arabe: 15, Français: 14
        textColor=colors.HexColor('#3498db'),
        spaceAfter=10,
        alignment=TA_CENTER,  # Sous-titre toujours centré
        fontName=FONT_NAME_BOLD
    )
    
    # Style pour le corps
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=13 if lang == 'ar' else 12,  # Arabe: 13, Français: 12
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        alignment=text_alignment,  # RTL pour arabe
        fontName=FONT_NAME,
        leading=18 if lang == 'ar' else 16  # Arabe: 18, Français: 16
    )
    
    # Style pour les informations importantes
    info_style = ParagraphStyle(
        'CustomInfo',
        parent=styles['BodyText'],
        fontSize=13 if lang == 'ar' else 12,  # Arabe: 13, Français: 12
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        alignment=text_alignment,  # RTL pour arabe
        fontName=FONT_NAME_BOLD
    )
    
    # Style pour la date en haut à droite
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12 if lang == 'ar' else 11,  # Arabe: 12, Français: 11
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_RIGHT,  # Toujours à droite
        fontName=FONT_NAME
    )
    
    # ========================================================================
    # En-tête : Logo et informations de l'entreprise
    # ========================================================================
    
    # Date d'émission
    emission_date = datetime.now().strftime('%d/%m/%Y')
    issued_text = reshape_arabic_text(f"{t['issued']} {emission_date}", lang)
    elements.append(Paragraph(issued_text, date_style))
    elements.append(Spacer(1, 0.3*cm))  # Réduit de 0.5 à 0.3
    
    # Logo de l'entreprise
    logo_path = os.path.join('static', 'img', 'logo.jpeg')
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=3.5*cm, height=3.5*cm, kind='proportional')  # Réduit de 4 à 3.5
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.2*cm))  # Réduit de 0.3 à 0.2
        except Exception as e:
            print(f"Erreur lors du chargement du logo: {e}")
            # Fallback au texte si le logo ne peut pas être chargé
            company_name = reshape_arabic_text(t['company_name'], lang)
            company_subtitle = reshape_arabic_text(t['company_subtitle'], lang)
            elements.append(Paragraph(company_name, title_style))
            elements.append(Paragraph(company_subtitle, subtitle_style))
            elements.append(Spacer(1, 0.2*cm))  # Réduit de 0.3 à 0.2
    else:
        # Si le logo n'existe pas, utiliser le texte
        company_name = reshape_arabic_text(t['company_name'], lang)
        company_subtitle = reshape_arabic_text(t['company_subtitle'], lang)
        elements.append(Paragraph(company_name, title_style))
        elements.append(Paragraph(company_subtitle, subtitle_style))
        elements.append(Spacer(1, 0.2*cm))  # Réduit de 0.3 à 0.2
    
    # ========================================================================
    # Titre du document
    # ========================================================================
    
    title_text = reshape_arabic_text(t['title'], lang)
    title = Paragraph(title_text, title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*cm))  # Réduit de 0.3 à 0.2
    
    # ========================================================================
    # Destinataire
    # ========================================================================
    
    attention_text = reshape_arabic_text(t['attention'], lang)
    recipient = f"""
    <b>{attention_text}</b><br/>
    <b>{application_data['prenom']} {application_data['nom']}</b><br/>
    {application_data['email']}<br/>
    {application_data['telephone']}<br/>
    {application_data['adresse']}
    """
    elements.append(Paragraph(recipient, body_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # ========================================================================
    # Corps de la lettre
    # ========================================================================
    
    # Salutation - ordre différent pour l'arabe
    greeting_text = reshape_arabic_text(t['greeting'], lang)
    if lang == 'ar':
        # En arabe : Nom + Salutation (ex: "محمد السيدة، السيد")
        salutation = f"{application_data['nom']} {greeting_text}،"
    else:
        # En français : Salutation + Nom (ex: "Madame, Monsieur Dupont,")
        salutation = f"{greeting_text} {application_data['nom']},"
    elements.append(Paragraph(salutation, body_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # Introduction
    # For spontaneous applications, use the selected job title if available
    job_title_display = application_data.get('selected_job_title') or application_data['job_title']
    
    intro_1 = reshape_arabic_text(t['intro_1'], lang)
    intro_2 = reshape_arabic_text(t['intro_2'], lang)
    intro = f"""
    {intro_1} <b>{job_title_display}</b>, 
    {intro_2}
    """
    elements.append(Paragraph(intro, body_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # Convocation
    convocation_text = reshape_arabic_text(t['convocation'], lang)
    please_present_text = reshape_arabic_text(t['please_present'], lang)
    convocation = f"""
    {convocation_text} {please_present_text}
    """
    elements.append(Paragraph(convocation, body_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # ========================================================================
    # Informations de l'entretien (Encadré)
    # ========================================================================
    
    # Parser la date de l'entretien
    try:
        interview_dt = datetime.strptime(interview_date, '%Y-%m-%dT%H:%M')
        formatted_date = interview_dt.strftime('%A %d %B %Y à %H:%M')
        formatted_day = interview_dt.strftime('%d/%m/%Y')
        formatted_time = interview_dt.strftime('%H:%M')
    except:
        # Si le parsing échoue, s'assurer que tout est en chaîne
        formatted_date = str(interview_date)
        formatted_day = str(interview_date)
        to_confirm_text = "À confirmer" if lang == 'fr' else "يتم التأكيد"
        formatted_time = reshape_arabic_text(to_confirm_text, lang)
    
    # Traduction des jours et mois selon la langue (seulement si c'est une chaîne)
    if isinstance(formatted_date, str):
        if lang == 'ar':
            # Traduction en arabe
            days_ar = {
                'Monday': 'الإثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء',
                'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'
            }
            months_ar = {
                'January': 'يناير', 'February': 'فبراير', 'March': 'مارس', 'April': 'أبريل',
                'May': 'مايو', 'June': 'يونيو', 'July': 'يوليو', 'August': 'أغسطس',
                'September': 'سبتمبر', 'October': 'أكتوبر', 'November': 'نوفمبر', 'December': 'ديسمبر'
            }
            
            for eng, ar in days_ar.items():
                formatted_date = formatted_date.replace(eng, ar)
            for eng, ar in months_ar.items():
                formatted_date = formatted_date.replace(eng, ar)
            formatted_date = formatted_date.replace(' à ', ' في الساعة ')
            # Reshaper le texte arabe après les remplacements
            formatted_date = reshape_arabic_text(formatted_date, lang)
        else:
            # Traduction en français
            days_fr = {
                'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
                'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
            }
            months_fr = {
                'January': 'janvier', 'February': 'février', 'March': 'mars', 'April': 'avril',
                'May': 'mai', 'June': 'juin', 'July': 'juillet', 'August': 'août',
                'September': 'septembre', 'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
            }
            
            for eng, fr in days_fr.items():
                formatted_date = formatted_date.replace(eng, fr)
            for eng, fr in months_fr.items():
                formatted_date = formatted_date.replace(eng, fr)
    
    # Créer un tableau pour les informations
    date_label = reshape_arabic_text(t["date"], lang)
    time_label = reshape_arabic_text(t["time"], lang)
    address_label = reshape_arabic_text(t["address"], lang)
    position_label = reshape_arabic_text(t["position"], lang)
    address_value = reshape_arabic_text('Siège de SALSABIL' if lang == 'fr' else 'مقر السلسبيل', lang)
    
    # Inverser les colonnes pour l'arabe (valeur à gauche, label à droite)
    if lang == 'ar':
        interview_info = [
            [formatted_day, f'📅 {date_label}'],
            [formatted_time, f'🕐 {time_label}'],
            [address_value, f'📍 {address_label}'],
            [job_title_display, f'💼 {position_label}'],
        ]
        # Pour l'arabe : valeur (large) puis label (étroit)
        col_widths = [10*cm, 5*cm]
    else:
        interview_info = [
            [f'📅 {date_label}', formatted_day],
            [f'🕐 {time_label}', formatted_time],
            [f'📍 {address_label}', address_value],
            [f'💼 {position_label}', job_title_display],
        ]
        # Pour le français : label (étroit) puis valeur (large)
        col_widths = [5*cm, 10*cm]
    
    # Alignement du tableau selon la langue
    table_alignment = 'RIGHT' if lang == 'ar' else 'LEFT'
    
    interview_table = Table(interview_info, colWidths=col_widths)
    interview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), table_alignment),
        ('FONTNAME', (0, 0), (0, -1), FONT_NAME_BOLD if lang == 'fr' else FONT_NAME),
        ('FONTNAME', (1, 0), (1, -1), FONT_NAME if lang == 'fr' else FONT_NAME_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 13 if lang == 'ar' else 12),  # Arabe: 13, Français: 12
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),  # Augmenté de 8 à 10
        ('TOPPADDING', (0, 0), (-1, -1), 10),  # Augmenté de 8 à 10
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
    ]))
    
    elements.append(interview_table)
    elements.append(Spacer(1, 0.2*cm))
    
    # ========================================================================
    # Instructions importantes
    # ========================================================================
    
    instructions_text = reshape_arabic_text(t['instructions'], lang)
    important_title = Paragraph(f"<b>⚠️ {instructions_text}</b>", info_style)
    elements.append(important_title)
    elements.append(Spacer(1, 0.2*cm))  # Réduit de 0.3 à 0.2
    
    # ========================================================================
    # Conclusion et signature
    # ========================================================================
    
    closing_text = reshape_arabic_text(t['closing'], lang)
    closing = Paragraph(closing_text, body_style)
    elements.append(closing)
    elements.append(Spacer(1, 0.2*cm))  # Réduit de 0.3 à 0.2
    
    signature_text = reshape_arabic_text(t['signature'], lang)
    hr_team_text = reshape_arabic_text(t['hr_team'], lang)
    signature = f"""
    {signature_text}<br/>
    <b>{hr_team_text}</b>
    """
    elements.append(Paragraph(signature, body_style))
    # Supprimé le Spacer final avant la construction du PDF
    
    # ========================================================================
    # QR Code en haut à gauche et texte code en bas de page
    # ========================================================================
    
    def add_qr_and_code(canvas, doc):
        if verification_code:
            # QR en haut à gauche
            verification_url = f"{base_url}/verify/{verification_code}"
            qr_buffer = create_qr_code(verification_url)
            from reportlab.lib.utils import ImageReader
            qr_img = ImageReader(qr_buffer)
            canvas.saveState()
            canvas.drawImage(qr_img, x=1.2*cm, y=A4[1]-4*cm, width=3*cm, height=3*cm, mask='auto')
            canvas.restoreState()
            # Texte code en bas centré
            verification_code_text = reshape_arabic_text(t['verification_code'], lang)
            # Inverser l'ordre pour l'arabe : code avant le texte
            if lang == 'ar':
                code_text = f"{verification_code} : {verification_code_text}"
            else:
                code_text = f"{verification_code_text} : {verification_code}"
            canvas.saveState()
            canvas.setFont(FONT_NAME_BOLD, 13)  # Augmenté de 12 à 13
            canvas.setFillColor(colors.HexColor('#2c3e50'))
            canvas.drawCentredString(A4[0]/2, 1.7*cm, code_text)
            canvas.restoreState()
    
    # ========================================================================
    
    # ========================================================================
    # Construire le PDF
    # ========================================================================
    
    doc.build(elements, onFirstPage=add_qr_and_code, onLaterPages=add_qr_and_code)
    
    return output_path


def generate_interview_invitation_filename(candidate_name, application_id):
    """
    Générer un nom de fichier standardisé pour la convocation
    
    Args:
        candidate_name: Nom complet du candidat
        application_id: ID de la candidature
    
    Returns:
        str: Nom de fichier formaté
    """
    # Nettoyer le nom (enlever les caractères spéciaux)
    import re
    clean_name = re.sub(r'[^\w\s-]', '', candidate_name)
    clean_name = re.sub(r'[-\s]+', '_', clean_name)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"Convocation_Entretien_{clean_name}_{application_id}_{timestamp}.pdf"


def generate_acceptance_letter_pdf(application_data, output_path, verification_code=None, base_url="http://localhost:5000", lang='fr'):
    """
    Générer un PDF de lettre d'acceptation finale après interview (français ou arabe)
    
    Args:
        application_data: Dictionnaire contenant les infos du candidat
        output_path: Chemin où sauvegarder le PDF
        verification_code: Code de vérification unique (optionnel)
        base_url: URL de base pour le QR code
        lang: Langue du document ('fr' ou 'ar')
    
    Returns:
        str: Chemin du fichier PDF généré
    """
    
    # Récupérer les traductions
    print(f"🌍 [ACCEPTANCE] Génération PDF avec langue: {lang}")
    print(f"🔍 [ACCEPTANCE] Clés disponibles dans ACCEPTANCE_TEXTS: {list(ACCEPTANCE_TEXTS.keys())}")
    
    # S'assurer que lang est bien une chaîne et enlever les espaces
    lang = str(lang).strip().lower()
    print(f"🔍 [ACCEPTANCE] Langue normalisée: '{lang}'")
    
    if lang == 'ar':
        t = ACCEPTANCE_TEXTS['ar']
        print(f"✅ [ACCEPTANCE] Utilisation du dictionnaire ARABE")
    else:
        t = ACCEPTANCE_TEXTS['fr']
        print(f"✅ [ACCEPTANCE] Utilisation du dictionnaire FRANÇAIS")
    
    print(f"📝 [ACCEPTANCE] Titre utilisé: {t['title']}")
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Container pour les éléments du document
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Alignement selon la langue (RTL pour arabe)
    text_alignment = TA_RIGHT if lang == 'ar' else TA_JUSTIFY
    
    # ========================================================================
    # En-tête avec logo
    # ========================================================================
    
    logo_path = "static/img/logo.jpeg"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2.5*cm, height=2.5*cm)  # Réduit de 3 à 2.5
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 0.3*cm))  # Réduit de 0.5 à 0.3
    
    # Style pour le titre
    # Titre
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=26 if lang == 'ar' else 24,  # Arabe: 26, Français: 24
        textColor=colors.HexColor('#2ecc71'),
        spaceAfter=14,
        alignment=TA_CENTER,  # Titre toujours centré
        fontName=FONT_NAME_BOLD
    )
    
    title_text = reshape_arabic_text(t['title'], lang)
    title = f"🎉 {title_text} 🎉"
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.2*cm))  # Réduit de 0.3 à 0.2
    
    # Sous-titre
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=15 if lang == 'ar' else 14,  # Arabe: 15, Français: 14
        textColor=colors.HexColor('#27ae60'),
        alignment=TA_CENTER,  # Sous-titre toujours centré
        fontName=FONT_NAME_BOLD
    )
    welcome_text = reshape_arabic_text("Bienvenue dans l'équipe SALSABIL !" if lang == 'fr' else "مرحباً بكم في فريق السلسبيل!", lang)
    elements.append(Paragraph(welcome_text, subtitle_style))
    elements.append(Spacer(1, 0.5*cm))  # Réduit de 1 à 0.5
    
    # ========================================================================
    # Date et lieu
    # ========================================================================
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12 if lang == 'ar' else 11,  # Arabe: 12, Français: 11
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#7f8c8d'),
        fontName=FONT_NAME
    )
    
    current_date = datetime.now().strftime('%d/%m/%Y')
    issued_text = reshape_arabic_text(t['issued'], lang)
    date_text = reshape_arabic_text(f"Salsabil, {issued_text} {current_date}" if lang == 'fr' else f"سالسبيل، {issued_text} {current_date}", lang)
    elements.append(Paragraph(date_text, date_style))
    elements.append(Spacer(1, 0.5*cm))  # Réduit de 1 à 0.5
    
    # ========================================================================
    # Destinataire
    # ========================================================================
    
    recipient_style = ParagraphStyle(
        'Recipient',
        parent=styles['Normal'],
        fontSize=13 if lang == 'ar' else 12,  # Arabe: 13, Français: 12
        textColor=colors.HexColor('#2c3e50'),
        alignment=text_alignment,  # RTL pour arabe
        fontName=FONT_NAME_BOLD
    )
    
    recipient = f"""
    <b>{reshape_arabic_text(t['attention'], lang)}</b><br/>
    {application_data.get('prenom', '')} {application_data.get('nom', '')}<br/>
    {application_data.get('adresse', 'Salsabil')}<br/>
    Email : {application_data.get('email', '')}<br/>
    Tél : {application_data.get('telephone', '')}
    """
    elements.append(Paragraph(recipient, recipient_style))
    elements.append(Spacer(1, 0.5*cm))  # Réduit de 1 à 0.5
    
    # ========================================================================
    # Corps de la lettre
    # ========================================================================
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=13 if lang == 'ar' else 12,  # Arabe: 13, Français: 12
        textColor=colors.HexColor('#2c3e50'),
        alignment=text_alignment,  # RTL pour arabe
        leading=20 if lang == 'ar' else 18,  # Arabe: 20, Français: 18
        fontName=FONT_NAME
    )
    
    # Objet
    object_style = ParagraphStyle(
        'Object',
        parent=styles['Normal'],
        fontSize=13 if lang == 'ar' else 12,  # Arabe: 13, Français: 12
        textColor=colors.HexColor('#2c3e50'),
        fontName=FONT_NAME_BOLD,
        alignment=TA_CENTER
    )
    
    job_title = application_data.get('job_title', 'le poste proposé')
    
    acceptance_msg = reshape_arabic_text("Acceptation de votre candidature" if lang == 'fr' else "قبول طلبكم", lang)
    job_title_reshaped = reshape_arabic_text(job_title, lang)
    object_text = f"{acceptance_msg} - {job_title_reshaped}"
    elements.append(Paragraph(f"<b>{object_text}</b>", object_style))
    elements.append(Spacer(1, 0.5*cm))  # Réduit de 0.8 à 0.5
    
    # Salutation - Inverser pour l'arabe
    greeting_text = reshape_arabic_text(t['greeting'], lang)
    if lang == 'ar':
        # En arabe : Nom + Salutation
        salutation = f"{application_data.get('nom', '')} {greeting_text}،"
    else:
        # En français : Salutation + Nom
        salutation = f"{greeting_text} {application_data.get('nom', '')},"
    elements.append(Paragraph(salutation, body_style))
    elements.append(Spacer(1, 0.3*cm))  # Réduit de 0.5 à 0.3
    
    # Paragraphe 1 : Félicitations
    acceptance_msg_1 = reshape_arabic_text(t['acceptance_msg_1'], lang)
    acceptance_msg_2 = reshape_arabic_text(t['acceptance_msg_2'], lang)
    para1 = f"""
    {acceptance_msg_1} <b>{job_title_reshaped}</b> {acceptance_msg_2}
    """
    elements.append(Paragraph(para1, body_style))
    elements.append(Spacer(1, 0.3*cm))  # Réduit de 0.5 à 0.3
    
    # Paragraphe 2 : Integration
    para2 = reshape_arabic_text(t['integration'], lang)
    elements.append(Paragraph(para2, body_style))
    elements.append(Spacer(1, 0.3*cm))  # Réduit de 0.5 à 0.3
    
    # Date de début de travail (si disponible)
    if application_data.get('work_start_date'):
        start_date_label = reshape_arabic_text(t['start_date'], lang)
        work_start_date = application_data.get('work_start_date')
        
        # Formater la date si c'est une chaîne de format ISO
        try:
            if isinstance(work_start_date, str) and 'T' not in work_start_date:
                # Format: YYYY-MM-DD
                date_obj = datetime.strptime(work_start_date, '%Y-%m-%d')
                formatted_start_date = date_obj.strftime('%d/%m/%Y')
            else:
                formatted_start_date = work_start_date
        except:
            formatted_start_date = work_start_date
        
        start_date_style = ParagraphStyle(
            'StartDate',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            fontName=FONT_NAME_BOLD,
            alignment=text_alignment
        )
        
        # Inverser pour l'arabe : date avant le label
        if lang == 'ar':
            start_date_text = f"<b>{formatted_start_date}</b> : 📅 <b>{start_date_label}</b>"
        else:
            start_date_text = f"📅 <b>{start_date_label}</b> : {formatted_start_date}"
        elements.append(Paragraph(start_date_text, start_date_style))
        elements.append(Spacer(1, 0.3*cm))  # Réduit de 0.5 à 0.3
    
    # Encadré avec informations de contact
    contact_label_phone = reshape_arabic_text('📞 Téléphone' if lang == 'fr' else '📞 الهاتف', lang)
    contact_label_email = reshape_arabic_text('📧 Email' if lang == 'fr' else '📧 البريد الإلكتروني', lang)
    contact_label_address = reshape_arabic_text('📍 Adresse' if lang == 'fr' else '📍 العنوان', lang)
    salsabil_address = reshape_arabic_text('SALSABIL, Selea' if lang == 'fr' else 'السلسبيل، سيليا', lang)
    
    # Inverser les colonnes pour l'arabe (valeur à gauche, label à droite)
    if lang == 'ar':
        contact_data = [
            ['+269 447 15 85', contact_label_phone],
            ['hr.usinesalsabil@gmail.com', contact_label_email],
            [salsabil_address, contact_label_address],
        ]
        # Pour l'arabe : valeur (large) puis label (étroit)
        col_widths = [10*cm, 5*cm]
    else:
        contact_data = [
            [contact_label_phone, '+269 447 15 85'],
            [contact_label_email, 'hr.usinesalsabil@gmail.com'],
            [contact_label_address, salsabil_address],
        ]
        # Pour le français : label (étroit) puis valeur (large)
        col_widths = [5*cm, 10*cm]
    
    # Alignement du tableau selon la langue
    table_alignment = 'RIGHT' if lang == 'ar' else 'LEFT'
    
    contact_table = Table(contact_data, colWidths=col_widths)
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), table_alignment),
        ('FONTNAME', (0, 0), (0, -1), FONT_NAME if lang == 'ar' else FONT_NAME_BOLD),
        ('FONTNAME', (1, 0), (1, -1), FONT_NAME_BOLD if lang == 'ar' else FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 13 if lang == 'ar' else 12),  # Arabe: 13, Français: 12
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),  # Augmenté de 8 à 10
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),  # Augmenté de 8 à 10
    ]))
    
    elements.append(Spacer(1, 0.3*cm))  # Réduit de 0.5 à 0.3
    elements.append(contact_table)
    elements.append(Spacer(1, 0.5*cm))  # Réduit de 0.8 à 0.5
    
    # Paragraphe 4 : Félicitations finales
    para4 = reshape_arabic_text(t['closing'], lang)
    elements.append(Paragraph(para4, body_style))
    elements.append(Spacer(1, 0.3*cm))  # Réduit de 0.5 à 0.3
    
    # Clôture
    signature_text = reshape_arabic_text(t['signature'], lang)
    hr_team_text = reshape_arabic_text(t['hr_team'], lang)
    closing_text = f"{signature_text}<br/><b>{hr_team_text}</b>"
    elements.append(Paragraph(closing_text, body_style))
    # Supprimé le Spacer final
    
    # ========================================================================
    # QR Code en haut à gauche et texte code en bas de page
    # ========================================================================
    def add_qr_and_code(canvas, doc):
        if verification_code:
            # QR en haut à gauche
            verification_url = f"{base_url}/verify/{verification_code}"
            qr_buffer = create_qr_code(verification_url)
            from reportlab.lib.utils import ImageReader
            qr_img = ImageReader(qr_buffer)
            canvas.saveState()
            canvas.drawImage(qr_img, x=1.2*cm, y=A4[1]-4*cm, width=3*cm, height=3*cm, mask='auto')
            canvas.restoreState()
            # Texte code en bas centré
            verification_code_text = reshape_arabic_text(t.get('verification_code', 'Code de vérification'), lang)
            # Inverser l'ordre pour l'arabe : code avant le texte
            if lang == 'ar':
                code_text = f"{verification_code} : {verification_code_text}"
            else:
                code_text = f"{verification_code_text} : {verification_code}"
            canvas.saveState()
            canvas.setFont(FONT_NAME_BOLD, 13)  # Augmenté de 12 à 13
            canvas.setFillColor(colors.HexColor('#2c3e50'))
            canvas.drawCentredString(A4[0]/2, 1.7*cm, code_text)
            canvas.restoreState()
    # ========================================================================
    
    # ========================================================================
    # Construire le PDF
    # ========================================================================
    
    doc.build(elements, onFirstPage=add_qr_and_code, onLaterPages=add_qr_and_code)
    
    return output_path


def generate_acceptance_letter_filename(candidate_name, application_id):
    """
    Générer un nom de fichier standardisé pour la lettre d'acceptation
    
    Args:
        candidate_name: Nom complet du candidat
        application_id: ID de la candidature
    
    Returns:
        str: Nom de fichier formaté
    """
    import re
    clean_name = re.sub(r'[^\w\s-]', '', candidate_name)
    clean_name = re.sub(r'[-\s]+', '_', clean_name)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"Lettre_Acceptation_{clean_name}_{application_id}_{timestamp}.pdf"
