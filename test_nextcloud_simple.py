import os
import requests

def test_nextcloud_connection():
    """
    Teste la connexion WebDAV à Nextcloud et liste le dossier 'Cours Test'.
    """


    # Variables de connexion
    nc_user = "r.noble"
    nc_password = "aCX^qz9W5G19LT"

    # Liste de chemins à tester
    paths = [
        "https://capdrive.caplogy.com:4443/remote.php/dav/files/r.noble/",  # chemin standard utilisateur
        "https://capdrive.caplogy.com/remote.php/dav/files/r.noble",   # sans slash final
        "https://capdrive.caplogy.com/remote.php/dav/files/DC89BA57-E31B-401B-81EB-B01276E0B218/", # chemin ID
        "https://capdrive.caplogy.com/remote.php/dav/files/DC89BA57-E31B-401B-81EB-B01276E0B218",  # ID sans slash
    ]

    for url in paths:
        print(f"\nTest de connexion à Nextcloud WebDAV: {url}")
        try:
            response = requests.request(
                method='PROPFIND',
                url=url,
                auth=(nc_user, nc_password),
                timeout=15,
                verify=False  # Ignore la vérification du certificat SSL
            )
            print(f"Statut HTTP: {response.status_code}")
            if response.status_code in [200, 207]:
                print("Connexion réussie. Réponse (1000 premiers caractères):")
                print(response.text[:1000])
                import re
                folder_names = re.findall(r'<d:displayname>(.*?)</d:displayname>', response.text)
                print("Dossiers trouvés :")
                for name in folder_names:
                    print(f"- {name}")
            else:
                print(f"Erreur HTTP: {response.status_code}")
                print(response.text[:500])
        except requests.exceptions.Timeout:
            print("Timeout: Le serveur Nextcloud ne répond pas (15s)")
        except requests.exceptions.ConnectionError as e:
            print(f"Erreur de connexion: {e}")
        except Exception as e:
            print(f"Erreur inattendue: {e}")

if __name__ == "__main__":
    test_nextcloud_connection()
