"""
Système de traduction pour les valeurs des formulaires
Permet de traduire les valeurs enregistrées en français vers l'arabe
"""

# Traductions des valeurs de formulaire FR -> AR
TRANSLATIONS = {
    # Genre / Sexe
    'Masculin': 'ذكر',
    'Féminin': 'أنثى',
    
    # Oui / Non
    'Oui': 'نعم',
    'Non': 'لا',
    
    # État civil
    'Célibataire': 'أعزب / عزباء',
    'Marié(e)': 'متزوج / متزوجة',
    'Divorcé(e)': 'مطلق / مطلقة',
    'Veuf(ve)': 'أرمل / أرملة',
    
    # Niveau d\'instruction
    'Sans diplôme': 'بدون شهادة',
    'Certificat d\'études primaires': 'شهادة الدراسة الابتدائية',
    'Brevet des collèges': 'شهادة التعليم المتوسط',
    'CAP / BEP': 'شهادة مهنية',
    'Baccalauréat': 'البكالوريا',
    'Diplôme d\'institut': 'دبلوم معهد',
    'Licence / Bachelor': 'ليسانس / بكالوريوس',
    'Master': 'ماجستير',
    'Doctorat / PhD': 'دكتوراه',
    'Autre': 'أخرى',
    
    # Spécialisations
    'Comptabilité / Finance': 'المحاسبة / المالية',
    'Ressources Humaines': 'الموارد البشرية',
    'Marketing / Communication': 'التسويق / الاتصال',
    'Informatique / IT': 'المعلوماتية / تكنولوجيا المعلومات',
    'Ingénierie': 'الهندسة',
    'Droit': 'القانون',
    'Médecine / Santé': 'الطب / الصحة',
    'Éducation / Enseignement': 'التربية / التعليم',
    'Hôtellerie / Restauration': 'الفندقة / المطاعم',
    'Commerce / Vente': 'التجارة / المبيعات',
    'Logistique / Transport': 'اللوجستيات / النقل',
    'Agriculture / Pêche': 'الزراعة / الصيد',
    'Arts / Culture': 'الفنون / الثقافة',
    'BTP / Construction': 'البناء والأشغال العامة',
    'Sciences': 'العلوم',
    'Sciences informatiques': 'علوم الحاسوب',
    'Tourisme': 'السياحة',
    
    # Niveaux de langue
    'Faible': 'ضعيف',
    'A1 / A2 : Débutant': 'مبتدئ (A1 / A2)',
    'B1 / B2 : Intermédiaire': 'متوسط (B1 / B2)',
    'C1 / C2 : Avancé': 'متقدم (C1 / C2)',
    'Langue maternelle': 'اللغة الأم',
    
    # Pays (Îles des Comores)
    'Grande Comore': 'القمر الكبرى (نجازيجا)',
    'Anjouan': 'أنجوان (نزواني)',
    'Mohéli': 'موهيلي (موالي)',
    'Mayotte': 'مايوت (ماوري)',
    'Autre': 'أخرى',
    
    # Types de contrat
    'CDI': 'عقد دائم',
    'CDD': 'عقد محدد المدة',
    'Stage': 'تدريب',
    'Freelance': 'مستقل',
    'Temps partiel': 'دوام جزئي',
    'Temps plein': 'دوام كامل',
    
    # Choix de travail (candidature spontanée)
    'Service Client / Accueil': 'خدمة العملاء / الاستقبال',
    'Vente / Commerce': 'المبيعات / التجارة',
    'Production / Fabrication': 'الإنتاج / التصنيع',
    'Gestion / Administration': 'الإدارة / التسيير',
    'Technique / Maintenance': 'التقنية / الصيانة',
    'Informatique / IT': 'المعلوماتية / تكنولوجيا المعلومات',
    'Comptabilité / Finance': 'المحاسبة / المالية',
    'Ressources Humaines': 'الموارد البشرية',
    'Logistique / Magasinage': 'اللوجستيات / التخزين',
    'Qualité / Sécurité': 'الجودة / السلامة',
    # Postes spécifiques (traductions ajoutées)
    'Chef du département de production': 'رئيس قسم الإنتاج',
    'Responsable de production': 'مسؤول الإنتاج',
    "Superviseur de ligne de production": 'مشرف خط إنتاج',
    "Chef d'équipe de production": 'قائد فريق الإنتاج',
    'Opérateur de machine': 'مشغل آلة',
    'Technicien de production': 'فني إنتاج',
    'Ouvrier de production': 'عامل إنتاج',
    'Contrôleur de production': 'مراقب إنتاج',
    'Responsable des entrepôts': 'مدير المستودعات',
    'Chef magasinier': 'رئيس المخزن',
    'Magasinier / Gestionnaire de stock': 'عامل مخزن / مدير المخزون',
    'Opérateur logistique': 'مشغل لوجستي',
    'Cariste / Conducteur de chariot élévateur': 'سائق رافعة شوكية',
    'Préparateur de commandes': 'معد الطلبات',
    "Agent d'expédition / réception": 'وكيل الشحن / الاستلام',
    'Superviseur des achats': 'مشرف المشتريات',
    'Responsable des achats locaux': 'مسؤول المشتريات المحلية',
    'Responsable des achats locaux et administratifs': 'مسؤول المشتريات المحلية والإدارية',
    'Agent de suivi des livraisons': 'وكيل متابعة التسليمات',
    'Contrôleur ou analyste des achats': 'مراقب / محلل المشتريات',
    'Comptable': 'محاسب',
    'Assistant comptable': 'مساعد محاسب',
    'Contrôleur financier': 'مراقب مالي',
    'Secrétaire / Assistant administratif': 'كاتب / مساعد إداري',
    'Gestionnaire de paie': 'مسؤول الرواتب',
    'Responsable des ressources humaines (RH)': 'مسؤول الموارد البشرية',
    'Directeur santé et sécurité au travail': 'مدير الصحة والسلامة المهنية',
    'Responsable hygiène, sécurité et environnement (HSE)': 'مسؤول النظافة والسلامة والبيئة (HSE)',
    'Chef HSE': 'رئيس HSE',
    'Agent HSE': 'موظف HSE',
    'Ingénieur sécurité': 'مهندس السلامة',
    'Technicien en hygiène et sécurité': 'فني النظافة والسلامة',
    'Responsable qualité': 'مسؤول الجودة',
    'Auditeur qualité interne': 'مدقق جودة داخلي',
    'Contrôleur de sécurité': 'مراقب السلامة',
    'Secouriste industriel / Technicien de premiers secours': 'مسعف صناعي / فني إسعافات أولية',
    'Responsable marketing': 'مدير التسويق',
    'Chef de produit': 'مدير المنتج',
    'Chargé de communication': 'مندوب اتصال',
    'Commercial / Vendeur': 'مندوب مبيعات',
    'Assistant marketing': 'مساعد تسويق',
    'Responsable relations clients': 'مسؤول علاقات العملاء',
    'Responsable maintenance': 'مسؤول الصيانة',
    'Technicien de maintenance industrielle': 'فني صيانة صناعية',
    'Électricien industriel': 'فني كهرباء صناعي',
    'Mécanicien industriel': 'ميكانيكي صناعي',
    'Automaticien / Technicien en automatisme': 'فني أتمتة',
    'Technicien frigoriste': 'فني تبريد',
    'Soudeur industriel': 'لحام صناعي',
    'Plombier industriel': 'سباك صناعي',
    'Chaudronnier': 'صانع غلايات',
    'Technicien en instrumentation': 'فني أدوات قياس',
    "Technicien des pompes et systèmes d'eau": 'فني مضخات وأنظمة المياه',
    'Responsable contrôle qualité': 'مسؤول مراقبة الجودة',
    'Technicien de contrôle qualité': 'فني مراقبة الجودة',
    'Contrôleur qualité produits': 'مراقب جودة المنتجات',
    'Analyste qualité': 'محلل الجودة',
    'Spécialiste en sécurité alimentaire': 'أخصائي سلامة الغذاء',
    "Technicien de laboratoire (analyse de l'eau)": 'فني مختبر (تحليل المياه)',
    'Inspecteur qualité': 'مفتش جودة',
    "Responsable IT / Directeur des systèmes d'information": 'مسؤول تقنية المعلومات / مدير نظم المعلومات',
    'Développeur / Ingénieur logiciel': 'مطور / مهندس برمجيات',
    'Administrateur réseau et systèmes': 'مدير الشبكات والأنظمة',
    'Technicien support informatique': 'فني دعم تقني',
        'Spécialiste cybersécurité': 'أخصائي الأمن السيبراني',
    
    # Départements / Departments
    'Administration': 'الإدارة',
    'Ressources Humaines': 'الموارد البشرية',
    'Finance et Comptabilité': 'المالية والمحاسبة',
    'Informatique et Technologie': 'المعلوماتية والتكنولوجيا',
    'Marketing et Communication': 'التسويق والاتصال',
    'Ventes et Commerce': 'المبيعات والتجارة',
    'Production et Opérations': 'الإنتاج والعمليات',
    'Logistique et Supply Chain': 'اللوجستيات وسلسلة التوريد',
    'Qualité et Contrôle': 'الجودة والمراقبة',
    'Recherche et Développement': 'البحث والتطوير',
    'Service Client': 'خدمة العملاء',
    'Juridique': 'القانونية',
    'Santé et Sécurité': 'الصحة والسلامة',
    'Éducation et Formation': 'التعليم والتدريب',
    'Autres': 'أخرى',
    
    # Localisations / Locations
    'Moroni': 'موروني',
    'Itsandra': 'إتساندرا',
    'Hahaya': 'هاهايا',
    'Mvouni': 'مفوني',
    'Ikoni': 'إيكوني',
    'Oichili': 'أويشيلي',
    'Ivembeni': 'إيفيمبيني',
    'Mitsamiouli': 'متساميولي',
    'Mbeni': 'مبيني',
    'Nioumamilima': 'نيوماميليما',
    'Bangoi': 'بانغوي',
    'Foumbouni': 'فومبوني',
    'Mitsoudjé': 'متسودجي',
    'Dimadjou': 'ديمادجو',
    'Ourovéni': 'أوروفيني',
    'Séléa': 'سيليا',
    'Mbéni': 'مبيني',
    'Itsandzéni': 'إتسانديني',
    'Simboussa': 'سيمبوسا',
    'Télétravail': 'العمل عن بُعد',
    'Plusieurs sites': 'عدة مواقع',
    
    # Sous-catégories IT
    'Développeur / Ingénieur Logiciel': 'مطور / مهندس برمجيات',
    'Administrateur Réseau et Systèmes': 'مدير الشبكات والأنظمة',
    'Responsable IT / Directeur des Systèmes d\'Information': 'مسؤول تقنية المعلومات / مدير نظم المعلومات',
    'Support Technique / Help Desk': 'الدعم الفني / مكتب المساعدة',
    'Analyste de Données / Data Scientist': 'محلل البيانات / عالم البيانات',
    'Expert en Cybersécurité': 'خبير الأمن السيبراني',
    'Concepteur UI/UX / Designer Web': 'مصمم واجهات المستخدم / مصمم ويب',
    
    # Statuts
    'en attente': 'قيد الانتظار',
    'acceptée': 'مقبولة',
    'rejetée': 'مرفوضة',
    'interview programmé': 'مقابلة مجدولة'
}

# Traductions inverses AR -> FR (pour recherche inverse si nécessaire)
REVERSE_TRANSLATIONS = {v: k for k, v in TRANSLATIONS.items()}


def translate_value(value, target_lang='ar'):
    """
    Traduire une valeur du français vers l'arabe
    
    Args:
        value: La valeur à traduire (str)
        target_lang: La langue cible ('ar' pour arabe, 'fr' pour français)
    
    Returns:
        str: La valeur traduite, ou la valeur originale si pas de traduction trouvée
    """
    if not value or target_lang == 'fr':
        return value
    
    # Si c'est une chaîne, essayer de traduire
    if isinstance(value, str):
        # Traduction exacte
        if value in TRANSLATIONS:
            return TRANSLATIONS[value]
        
        # Pour les listes séparées par virgules (ex: choix_travail)
        if ',' in value:
            parts = [part.strip() for part in value.split(',')]
            translated_parts = []
            for part in parts:
                # Vérifier si commence par "Autre:"
                if part.startswith('Autre:'):
                    # Garder "Autre:" traduit + la précision
                    precision = part[6:].strip()
                    translated_parts.append(f"أخرى: {precision}")
                else:
                    translated_parts.append(TRANSLATIONS.get(part, part))
            return '، '.join(translated_parts)  # Utiliser la virgule arabe
        
        # Pour les chaînes avec tiret (ex: "Master - Sciences informatiques")
        if ' - ' in value:
            parts = value.split(' - ')
            translated_parts = [TRANSLATIONS.get(part.strip(), part.strip()) for part in parts]
            return ' - '.join(translated_parts)
    
    return value


def translate_dict_values(data_dict, target_lang='ar', fields_to_translate=None):
    """
    Traduire les valeurs d'un dictionnaire
    
    Args:
        data_dict: Le dictionnaire contenant les données
        target_lang: La langue cible ('ar' pour arabe)
        fields_to_translate: Liste des champs à traduire (None = tous)
    
    Returns:
        dict: Nouveau dictionnaire avec les valeurs traduites
    """
    if target_lang == 'fr':
        return data_dict
    
    # Liste des champs à traduire par défaut
    default_fields = [
        'sexe', 'etat_civil', 'travaille_actuellement',
        'niveau_instruction', 'specialisation', 'specialisation_autre',
        'langue_arabe', 'langue_anglaise', 'langue_francaise',
        'autre_langue_niveau', 'problemes_sante', 'pays', 'region',
        'choix_travail', 'status'
    ]
    
    fields = fields_to_translate or default_fields
    
    result = dict(data_dict)
    for field in fields:
        if field in result and result[field]:
            result[field] = translate_value(result[field], target_lang)
    
    return result
