from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Crée les groupes de rôles nécessaires pour l’intranet'

    def handle(self, *args, **options):
        roles = ['admin', 'moodle', 'rh', 'aucun_acces']
        for role in roles:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Groupe '{role}' créé."))
            else:
<<<<<<< HEAD
                self.stdout.write(f"Groupe '{role}' déjà existant.")
=======
                self.stdout.write(f"Groupe '{role}' déjà existant.")
>>>>>>> 3ad199c281336707a407058fbea28b11bfd12acb
