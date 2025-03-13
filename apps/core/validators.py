from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Validateur pour numéro de téléphone camerounais
phone_regex = RegexValidator(
    regex=r'^\+?237?6[5-9][0-9]{7}$',
    message="Le numéro de téléphone doit être au format: '+237xxxxxxxxx'. 9 chiffres autorisés."
)

def validate_file_size(value):
    """Valide la taille du fichier (limite à 5MB)"""
    filesize = value.size
    
    if filesize > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("La taille maximale du fichier est de 5MB.")
    return value

def validate_event_dates(start_date, end_date, registration_deadline=None):
    """Valide les dates d'un événement"""
    from django.utils import timezone
    
    # Vérifier que la date de début est dans le futur
    if start_date <= timezone.now():
        raise ValidationError(_("La date de début doit être dans le futur."))
    
    # Vérifier que la date de fin est après la date de début
    if end_date <= start_date:
        raise ValidationError(_("La date de fin doit être après la date de début."))
    
    # Vérifier que la date limite d'inscription est avant la date de début
    if registration_deadline and registration_deadline >= start_date:
        raise ValidationError(_("La date limite d'inscription doit être avant la date de début."))