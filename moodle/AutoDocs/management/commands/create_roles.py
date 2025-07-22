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
                self.stdout.write(f"Groupe '{role}' déjà existant.")
