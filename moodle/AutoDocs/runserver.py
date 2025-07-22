import os
import sys
import webbrowser

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    from django.core.management import execute_from_command_line

    sys.argv = ['manage.py', 'runserver', '127.0.0.1:8000', '--noreload']  # Arguments forcés

    # Ouvre le navigateur juste avant de lancer le serveur
    webbrowser.open('http://127.0.0.1:8000/')

    try:
        execute_from_command_line(sys.argv)
    except Exception as e:
        print("\n❌ Une erreur s'est produite :")
        print(e)
    finally:
        input("\n✅ Appuyez sur Entrée pour fermer...")

if __name__ == '__main__':
    main()
