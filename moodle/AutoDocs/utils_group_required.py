from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def group_required(*group_names):
    """
    Decorator for views that checks whether a user is in at least one of the required groups
    OR has a userprofile.role matching one of the group_names.
    Usage: @group_required('admin', 'moodle')
    """
    def in_groups(u):
        if u.is_authenticated:
            if u.is_superuser:
                return True
            # Vérifie l'appartenance au groupe Django
            if bool(u.groups.filter(name__in=group_names)):
                return True
            # Vérifie le champ userprofile.role si présent
            profile = getattr(u, 'userprofile', None)
            if profile and hasattr(profile, 'role') and profile.role in group_names:
                return True
        raise PermissionDenied
<<<<<<< HEAD
    return user_passes_test(in_groups)
=======
    return user_passes_test(in_groups)
>>>>>>> 3ad199c281336707a407058fbea28b11bfd12acb
