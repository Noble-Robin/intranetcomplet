from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def group_required(*group_names):
    """
    Decorator for views that checks whether a user is in at least one of the required groups.
    Usage: @group_required('admin', 'moodle')
    """
    def in_groups(u):
        if u.is_authenticated:
            if u.is_superuser:
                return True
            if bool(u.groups.filter(name__in=group_names)):
                return True
        raise PermissionDenied
    return user_passes_test(in_groups)