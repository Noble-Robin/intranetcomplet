import os
import requests

def test_nextcloud_connection():
    """
    Teste la connexion WebDAV à Nextcloud et liste le dossier 'Cours Test'.
    """
    # Récupérer les variables d'environnement
    nc_webdav = os.getenv('NEXTCLOUD_WEBDAV_URL')
    nc_user = os.getenv('NEXTCLOUD_USER')
    nc_password = os.getenv('NEXTCLOUD_PASSWORD')

    if not all([nc_webdav, nc_user, nc_password]):
        print("Variables d'environnement Nextcloud manquantes.")
        print(f"NEXTCLOUD_WEBDAV_URL: {nc_webdav}")
        print(f"NEXTCLOUD_USER: {nc_user}")
        print(f"NEXTCLOUD_PASSWORD: {'***' if nc_password else None}")
        return

    # Construire l'URL WebDAV pour le dossier 'Cours Test'
    folder_path = 'Cours Test/'
    if not nc_webdav.endswith('/'):
        nc_webdav += '/'
    url = nc_webdav + folder_path

    print(f"Test de connexion à Nextcloud WebDAV: {url}")
    try:
        response = requests.request(
            method='PROPFIND',
            url=url,
            auth=(nc_user, nc_password),
            timeout=30
        )
        print(f"Statut HTTP: {response.status_code}")
        if response.status_code in [200, 207]:
            print("Connexion réussie. Réponse:")
            print(response.text[:1000])  # Affiche les 1000 premiers caractères
        else:
            print(f"Erreur HTTP: {response.status_code}")
            print(response.text)
    except requests.exceptions.Timeout:
        print("Timeout: Le serveur Nextcloud ne répond pas (30s)")
    except requests.exceptions.ConnectionError as e:
        print(f"Erreur de connexion: {e}")
    except Exception as e:
        print(f"Erreur inattendue: {e}")

if __name__ == "__main__":
    test_nextcloud_connection()
