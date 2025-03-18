from rest_framework import permissions

class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Autoriser les organisateurs à créer des événements.
    Lecture seule pour tous les autres utilisateurs.
    """
    
    def has_permission(self, request, view):
        # Autoriser les méthodes GET, HEAD, OPTIONS pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Autoriser les créations/modifications uniquement pour les organisateurs
        return request.user.is_authenticated and request.user.role == 'organizer'

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Autoriser les propriétaires d'un objet à le modifier/supprimer.
    Lecture seule pour tous les autres utilisateurs.
    """
    
    def has_object_permission(self, request, view, obj):
        # Autoriser les méthodes GET, HEAD, OPTIONS pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Autoriser les administrateurs
        if request.user.is_staff:
            return True
        
        # Vérifier si l'objet a un attribut 'user' et s'il correspond à l'utilisateur actuel
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Vérifier si l'objet a un attribut 'organizer' et s'il correspond à l'utilisateur actuel
        if hasattr(obj, 'organizer'):
            return obj.organizer == request.user
        
        return False

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Autoriser uniquement les administrateurs à modifier/supprimer.
    Lecture seule pour tous les autres utilisateurs.
    """
    
    def has_permission(self, request, view):
        # Autoriser les méthodes GET, HEAD, OPTIONS pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Autoriser les modifications uniquement pour les administrateurs
        return request.user.is_authenticated and request.user.is_staff
    
class IsAdminOrOrganizer(permissions.BasePermission):
    """
    Autoriser uniquement les administrateurs ou les organisateurs.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Autoriser les administrateurs
        if request.user.is_staff:
            return True
            
        # Autoriser les organisateurs
        return request.user.role == 'organizer'
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # Autoriser les administrateurs
        if request.user.is_staff:
            return True
            
        # Autoriser les organisateurs pour leurs propres événements
        if hasattr(obj, 'organizer'):
            return obj.organizer == request.user
            
        # Pour les objets liés à un événement
        if hasattr(obj, 'event') and hasattr(obj.event, 'organizer'):
            return obj.event.organizer == request.user
            
        return False