import os
import sqlite3
from django.shortcuts import render
from django.utils.timezone import localdate
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from datetime import date
from datetime import datetime
import requests
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required

from xhtml2pdf import pisa
from io import BytesIO
import unicodedata

# Charge les variables d'environnement depuis .env
load_dotenv(os.path.join(settings.BASE_DIR, ".env"))

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_ID = os.environ.get("AIRTABLE_TABLE_ID")

# Chemin vers ta base SQLite
db_path = os.path.join(settings.BASE_DIR, "Data", "Caplogy.db")

def normalize_key(input_str):
    # Supprimer les accents
    no_accents = ''.join(
        c for c in unicodedata.normalize('NFKD', input_str)
        if not unicodedata.combining(c)
    )
    # Remplacer les espaces et apostrophes par des underscores
    cleaned = no_accents.replace(" ", "_").replace("'", "_")
    return cleaned.lower()

def download_image_to_static(url, fallback_path, filename="logo.png"):
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            tmp_path = os.path.join(settings.BASE_DIR, "static", "logo")
            os.makedirs(tmp_path, exist_ok=True)
            file_path = os.path.join(tmp_path, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_path  # chemin local utilisable par xhtml2pdf
    except Exception as e:
        print(f"[ERROR] Impossible de télécharger l'image Airtable: {e}")
    return fallback_path  # fallback si problème




def airtable(prenom, nom):
    # Récupère les données d'un utilisateur depuis Airtable en fonction du prénom et du nom.
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    }
    params = {
        "filterByFormula": f"AND(FIND('{prenom}', {{Prénom}}), FIND('{nom}', {{NOM}}))",
        "maxRecords": 1
    }
    response = requests.get(url, headers=headers, params=params)
    # print(f"[DEBUG] Airtable response status: {response.status_code}")
    # print(f"[DEBUG] Airtable response text: {response.text}")
    if response.status_code == 200:
        records = response.json().get("records", [])
        if records:
            return records[0]["fields"]
    return None

def airtable_all_names():
    # Récupère tous les prénoms et noms depuis Airtable.
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    }
    prenoms = set()
    noms = set()
    offset = None

    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            break

        data = response.json()
        records = data.get("records", [])
        for record in records:
            fields = record.get("fields", {})
            p = fields.get("Prénom")
            n = fields.get("NOM")
            if p:
                prenoms.add(p.strip())
            if n:
                noms.add(n.strip())

        offset = data.get("offset")
        if not offset:
            break

    return prenoms, noms

def airtable_entreprise(nom_entreprise):
    AIRTABLE_ENTREPRISE_API_KEY = "patRPkOrCjXiNQOXP.da78f4d42d6a81c684a447eaa4d285a5357552412041ef96dab6332a659c662d"
    AIRTABLE_ENTREPRISE_BASE_ID = "appLM1DpaOp09sL9Z"
    AIRTABLE_ENTREPRISE_TABLE_ID = "tblceZYcqVFJOlmDQ"

    url = f"https://api.airtable.com/v0/{AIRTABLE_ENTREPRISE_BASE_ID}/{AIRTABLE_ENTREPRISE_TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_ENTREPRISE_API_KEY}",
    }
    params = {
        "filterByFormula": f"Name = '{nom_entreprise}'",
        "maxRecords": 1
    }

    response = requests.get(url, headers=headers, params=params)
    # print(f"[DEBUG] Airtable response status: {response.status_code}")
    # print(f"[DEBUG] Airtable response text: {response.text}")

    if response.status_code == 200:
        records = response.json().get("records", [])
        if records:
            return records[0]["fields"]
    return None


@login_required
def index(request):
    context = None
    type_doc = None
    select_prenom = ""
    select_nom = ""
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'autodocs', 'logo.png')
    cachet_path = os.path.join(settings.BASE_DIR, 'static', 'autodocs', 'logo.png')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    ip = request.META.get('REMOTE_ADDR', '')
    ville = "Inconnue"
    try:
        response = requests.get(f"https://ipapi.co/{ip}/city/")
        if response.status_code == 200:
            ville = response.text.strip()
    except Exception as e:
        print(f"[ERROR] Impossible de récupérer la ville via IP: {e}")

    context = context or {}
    context.update({
        "date_document": date.today().strftime("%d/%m/%Y"),
        "ville": ville,
    })
    

    # Récupere les prénoms de SQLite
    cursor.execute("SELECT DISTINCT prenom FROM user ORDER BY LOWER(prenom)")
    prenoms_sqlite = {row[0] for row in cursor.fetchall()}

    prenoms_airtable, noms_airtable = airtable_all_names()

    # 3Fusion des prénoms et tri alphabétique
    prenoms = sorted(prenoms_sqlite.union(prenoms_airtable), key=str.lower)

    # Récupere noms en fonction du prénom sélectionné
    noms = []
    if request.method == "POST":
        select_prenom = request.POST.get("prenom", "").strip()
        select_nom = request.POST.get("nom", "").strip()
        type_doc = request.POST.get("type_doc", "").strip()
        generate = request.POST.get("generate", "")

        cursor.execute(
            "SELECT DISTINCT nom FROM user WHERE LOWER(prenom) = LOWER(?) ORDER BY LOWER(nom)",
            (select_prenom,)
        )
        noms_sqlite = {row[0] for row in cursor.fetchall()}

        noms_airtable_filtered = set()
        
        # print("Prenoms SQLite:", prenoms_sqlite)
        print("Prenoms Airtable:", prenoms_airtable)

        if select_prenom and not noms_sqlite:
            url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
            headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
            offset = None
            formula = f"FIND(LOWER('{select_prenom.lower()}'), LOWER({{Prénom}}))"
            while True:
                params = {"pageSize": 100, "filterByFormula": formula}
                if offset:
                    params["offset"] = offset
                response = requests.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    print("Erreur Airtable:", response.text)
                    break
                data = response.json()
                records = data.get("records", [])
                
                for rec in records:
                    nom_val = rec.get("fields", {}).get("NOM") or rec.get("fields", {}).get("nom")

                    if isinstance(nom_val, list):
                        nom_val = " ".join([n.strip() for n in nom_val if isinstance(n, str)])
                    elif isinstance(nom_val, str):
                        nom_val = nom_val.strip()
                    else:
                        nom_val = None

                    if nom_val:
                        noms_airtable_filtered.add(nom_val.strip())
                print("Nom récupéré dans Airtable:", nom_val)
                offset = data.get("offset")
                if not offset:
                    break
        
        print("Tous les noms filtrés Airtable:", noms_airtable_filtered)


        # Fusion
        noms = sorted(noms_sqlite.union(noms_airtable_filtered), key=str.lower)
        action = request.POST.get("action", "")
        is_generate = (action == "generate" or generate == "1")

        if (action == "preview" or is_generate) and select_prenom and select_nom and type_doc:

            # Recherche utilisateur SQLite
            cursor.execute("""
                SELECT * FROM user WHERE LOWER(prenom) = LOWER(?) AND LOWER(nom) = LOWER(?)
            """, (select_prenom, select_nom))
            user_row = cursor.fetchone()

            user_data = {}
            if user_row:
                user_cols = [column[0] for column in cursor.description]
                user_data = dict(zip(user_cols, user_row))

            
            # Recherche utilisateur Airtable
            airtable_data = airtable(select_prenom, select_nom)
            # print(f"[DEBUG] Airtable data pour {select_prenom} {select_nom} :", airtable_data)
            if airtable_data:
                airtable_to_context_mapping = {
                    "sexe": "civilite",
                    "entite": "entreprise_nom",
                    "fonction": "fonction",
                    "salaire_brute": "salaire_brut",
                    "intitule_du_poste": "poste",
                    "date_d_entree": "date_poste",
                    "adresse": "adresse_maison",
                    "localisation": "lieu_de_travail",
                    "nationnalite": "nationalite",
                    "date_de_naissance": "date_de_naissance",
                    "cachet": "cachet",
                    "logo": "logo",
                }

                for key, value in airtable_data.items():
                    key_normalized = normalize_key(key)
                    mapped_key = airtable_to_context_mapping.get(key_normalized, key_normalized)
                    if mapped_key == "civilite":
                        sexe_value = str(value).strip().lower()
                        if sexe_value == "femme":
                            user_data[mapped_key] = "Madame"
                        elif sexe_value == "homme":
                            user_data[mapped_key] = "Monsieur"
                        else:
                            user_data[mapped_key] = value
                    else:
                        user_data[mapped_key] = value
                # print("[DEBUG] Airtable utilisé pour pré-remplir :", user_data)

                # Correction : extraire l'URL de la photo si c'est un champ attachment (liste de dicts)
                photo_field = user_data.get("photo") or user_data.get("Photo")
                if isinstance(photo_field, list) and photo_field and isinstance(photo_field[0], dict):
                    user_data["photo"] = photo_field[0].get("url", "")
                elif isinstance(photo_field, str):
                    user_data["photo"] = photo_field
                else:
                    user_data["photo"] = ""

                            
            if not user_data:
                conn.close()
                return render(request, "index.html", {
                    "prenoms": prenoms,
                    "noms": noms,
                    "select_prenom": select_prenom,
                    "select_nom": select_nom,
                    "file_generated": None,
                    "logo": logo_path,
                    "cachet": cachet_path,
                    "preview": None,
                    "type_doc": type_doc,
                    "error_message": "Aucune donnée trouvée pour l'utilisateur."
                })


            # Récupération entreprise SQLite (avec id entreprise)
            entreprise_id = user_data.get("entreprise")
            entreprise_data = {}

            nom_entreprise = user_data.get("entreprise_nom")
            if nom_entreprise:
                airtable_entreprise_data = airtable_entreprise(nom_entreprise)
                if airtable_entreprise_data:
                    airtable_to_context_mapping_entreprise = {
                        "name": "entreprise_nom",
                        "adresse": "adresse_localisation",
                        "capital": "capital",
                        "numero_siret": "num_siret",
                        "numero_siren": "num_siren",
                        "rcs_d_immatriculation": "rcs_immatriculation",
                        "logo": "logo",
                        "cachet": "cachet",
                        "test_signature": "test_signature",
                        "code_ape": "ape",
                        "numero_tva": "tva",
                    }

                    for key, value in airtable_entreprise_data.items():
                        key_normalized = normalize_key(key)
                        final_key = airtable_to_context_mapping_entreprise.get(key_normalized, key_normalized)
                        if isinstance(value, list) and value and isinstance(value[0], dict):
                            entreprise_data[final_key] = value[0].get("url", "")
                        else:
                            entreprise_data[final_key] = value
                        print(f"Mapping clé: '{key}' → Normalisée: '{key_normalized}' → Contexte: '{final_key}' → Valeur Airtable: '{entreprise_data[final_key]}'")


            # Compléter avec la base SQLite pour les champs manquants
            if not entreprise_data or any(not v for v in entreprise_data.values()):
                entreprise_id = user_data.get("entreprise")
                if entreprise_id:
                    cursor.execute("SELECT * FROM entreprise WHERE id = ?", (entreprise_id,))
                    entreprise_row = cursor.fetchone()
                    if entreprise_row:
                        entreprise_cols = [column[0] for column in cursor.description]
                        sqlite_entreprise_data = dict(zip(entreprise_cols, entreprise_row))
                        # Compléter uniquement les champs vides dans entreprise_data
                        for k, v in sqlite_entreprise_data.items():
                            if not entreprise_data.get(k) and v:
                                entreprise_data[k] = v


            # Récupération matériel SQLite
            materiel_data = {}
            cursor.execute("SELECT * FROM materiel WHERE user_id = ?", (user_data.get("id"),))
            materiel_row = cursor.fetchone()
            if materiel_row:
                materiel_cols = [column[0] for column in cursor.description]
                materiel_data = dict(zip(materiel_cols, materiel_row))

            # Choix template + dossier
            if type_doc == "contrat_cdi":
                template_name = "templates_docs/contrat_cdi.html"
                dossier = os.path.join(settings.BASE_DIR, "Contrat", "CDI")
            elif type_doc == "attestation_de_remise_de_materiel":
                template_name = "templates_docs/attestation_de_remise_de_materiel.html"
                dossier = os.path.join(settings.BASE_DIR, "Attestation", "Remise")
            elif type_doc == "attestation_employeur":
                template_name = "templates_docs/attestation_employeur.html"
                dossier = os.path.join(settings.BASE_DIR, "Attestation", "Employeur")
            else:
                template_name = "templates_docs/default.html"
                dossier = os.path.join(settings.BASE_DIR, "Autres")

            os.makedirs(dossier, exist_ok=True)

            # Préparation contexte template
            context = {
                # User
                "prenom": user_data.get("prenom", ""),
                "nom": user_data.get("nom", ""),
                "civilite": user_data.get("civilite", ""),
                "date_de_naissance": user_data.get("date_de_naissance", ""),
                "lieu_de_naissance": user_data.get("lieu_de_naissance", ""),
                "nationalite": user_data.get("nationalite", ""),
                "adresse_maison": user_data.get("adresse_maison", ""),
                "num_secu": user_data.get("num_secu", ""),
                "titre_sejour": user_data.get("titre_sejour", ""),
                "num_sejour": user_data.get("num_sejour", ""),
                "date_valable_sejour": user_data.get("date_valable_sejour", ""),
                "poste": user_data.get("poste", ""),
                "date_poste": user_data.get("date_poste", ""),
                "position": user_data.get("position", ""),
                "coefficient": user_data.get("coefficient", ""),
                "salaire_net": user_data.get("salaire_net", ""),
                "salaire_brut": user_data.get("salaire_brut", ""),
                "salaire_brut_mois": user_data.get("salaire_brut_mois", ""),
                "lieu_de_travail": user_data.get("lieu_de_travail", ""),
                "limit_geo_region": user_data.get("limit_geo_region", ""),

                # Entreprise
                "entreprise_nom": entreprise_data.get("entreprise_nom", "") or user_data.get("entreprise_nom", ""),
                "adresse_localisation": entreprise_data.get("adresse_localisation", "") or user_data.get("adresse_localisation", ""),
                # "ville": entreprise_data.get("ville", "") or user_data.get("ville", ""),
                "num_siret": entreprise_data.get("num_siret", "") or user_data.get("num_siret", ""),
                "num_siren": entreprise_data.get("num_siren", "") or user_data.get("num_siren", ""),
                "rcs_immatriculation": entreprise_data.get("rcs_immatriculation", "") or user_data.get("rcs_immatriculation", ""),
                "ape": entreprise_data.get("ape", "") or user_data.get("ape", ""),
                "tva": entreprise_data.get("tva", "") or user_data.get("tva", ""),
                "test_signature": entreprise_data.get("test_signature", "") or user_data.get("test_signature", ""),


                # Materiel
                "marque": materiel_data.get("marque", ""),
                "cpu": materiel_data.get("cpu", ""),
                "numero_serie": materiel_data.get("numero_serie", ""),
                "ram": materiel_data.get("ram", ""),
                "ssd": materiel_data.get("ssd", ""),
                "valeur_neuf": materiel_data.get("valeur_neuf", ""),


                # logo

                # Sécurisation : ne jamais passer une liste à download_image_to_static
                "logo": download_image_to_static(
                    (entreprise_data.get("logo", "") if isinstance(entreprise_data.get("logo", ""), str) else "")
                    or (user_data.get("logo", "") if isinstance(user_data.get("logo", ""), str) else ""),
                    logo_path
                ),
                "cachet": download_image_to_static(
                    (entreprise_data.get("cachet", "") if isinstance(entreprise_data.get("cachet", ""), str) else "")
                    or (user_data.get("cachet", "") if isinstance(user_data.get("cachet", ""), str) else ""),
                    cachet_path
                ),

                # date
                "date_document": date.today().strftime("%d/%m/%Y"),
                "ville": ville,
            }

            # Générer PDF
            if is_generate:
                html_string = render_to_string(template_name, context)
                result = BytesIO()
                pisa_status = pisa.CreatePDF(html_string, dest=result)

                if pisa_status.err:
                    conn.close()
                    return HttpResponse("Erreur lors de la génération du PDF", status=500)

                pdf_file = result.getvalue()
                filename = f"{type_doc}_{select_prenom}_{select_nom}.pdf"
                file_path = os.path.join(dossier, filename)
                with open(file_path, "wb") as f:
                    f.write(pdf_file)

                conn.close()
                response = HttpResponse(pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

    else:
        # GET initial → liste tous les noms de SQLite
        cursor.execute("SELECT DISTINCT nom FROM user ORDER BY LOWER(nom)")
        noms_sqlite = {row[0] for row in cursor.fetchall()}
        # Fusion noms SQLite + Airtable
        noms = sorted(noms_sqlite.union(noms_airtable))

    conn.close()

    return render(request, "index.html", {
        "prenoms": prenoms,
        "noms": noms,
        "select_prenom": select_prenom,
        "select_nom": select_nom,
        "file_generated": None,
        "logo": logo_path,
        "cachet": cachet_path,
        "preview": context if 'context' in locals() else None,
        "type_doc": type_doc if 'type_doc' in locals() else None,
    })

@login_required
def creer_employer(request):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, entreprise_nom FROM entreprise ORDER BY entreprise_nom")
    entreprises = cursor.fetchall()  # Liste de tuples (id, nom)
    conn.close()

    if request.method == "POST":
        # Récupérer les données du formulaire
        prenom = request.POST.get('prenom', '').strip()
        nom = request.POST.get('nom', '').strip()
        
        # Vérification simple des champs obligatoires (à adapter)
        if prenom and nom:
            # Au lieu de rendre la page, on appelle directement la fonction de génération PDF
            return generer_contrat_cdi(request)
        else:
            form_data = {
                'prenom': prenom,
                'nom': nom,
            }
            success_message = None
            return render(request, "templates_docs/creer_employer.html", {
                "success_message": success_message,
                "form_data": form_data,
                "entreprises": entreprises,
                "year": localdate().year,
                "today": localdate().isoformat(),
            })

    # GET : affichage simple
    return render(request, "templates_docs/creer_employer.html", {
        "form_data": {},
        "year": localdate().year,
        "today": localdate().isoformat(),
        "entreprises": entreprises,
    })


@login_required
def generer_contrat_cdi(request):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # ip = request.META.get('REMOTE_ADDR', '')
    # ville = "Versailles"
    # try:
    #     response = requests.get(f"https://ipapi.co/{ip}/city/")
    #     if response.status_code == 200:
    #         ville = response.text.strip()
    # except Exception as e:
    #     print(f"[ERROR] Impossible de récupérer la ville via IP: {e}")

    cursor.execute("SELECT id, entreprise_nom FROM entreprise ORDER BY entreprise_nom")

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'autodocs', 'logo.png')
    cachet_path = os.path.join(settings.BASE_DIR, 'static', 'autodocs', 'logo.png')

    if request.method != "POST":
        return HttpResponse("Méthode non autorisée", status=405)

    # Récupération des données formulaire (salarié)
    civilite = request.POST.get("civilite", "")
    prenom = request.POST.get("prenom", "")
    nom = request.POST.get("nom", "")
    date_de_naissance = request.POST.get("date_de_naissance", "")
    lieu_de_naissance = request.POST.get("lieu_de_naissance", "")
    nationalite = request.POST.get("nationalite", "")
    adresse_maison = request.POST.get("adresse_maison", "")
    num_secu = request.POST.get("num_secu", "")
    titre_sejour = request.POST.get("titre_sejour", "")
    num_sejour = request.POST.get("num_sejour", "")
    date_valable_sejour = request.POST.get("date_valable_sejour", "")
    poste = request.POST.get("poste", "")
    date_poste = request.POST.get("date_poste", "")
    coefficient = request.POST.get("coefficient", "")
    position = request.POST.get("position", "")
    lieu_de_travail = request.POST.get("lieu_de_travail", "")
    limit_geo_region = request.POST.get("limit_geo_region", "")
    email = request.POST.get("email", "")
    photo = request.POST.get("photo", "")
    create_by = request.POST.get("create_by", "")
    fonction = request.POST.get("fonction", "")
    salaire_brut = request.POST.get("salaire_brut", "")
    salaire_brut_mois = request.POST.get("salaire_brut_mois", "")
    salaire_net = request.POST.get("salaire_net", "")
    date_sortie = request.POST.get("date_sortie", "")
    mutation = request.POST.get("mutation", "")
    equipe_manageriale = request.POST.get("equipe_manageriale", "")
    statut = request.POST.get("statut", "")
    etat = request.POST.get("etat", "")
    statut_pe = request.POST.get("statut_pe", "")
    last_seen_date = request.POST.get("last_seen_date", "")
    departement = request.POST.get("departement", "")
    type_contrat = request.POST.get("type_contrat", "")
    specialite = request.POST.get("specialite", "")
    nom_complet = f"{prenom} {nom}"

    if date_de_naissance:
        try:
            date_obj = datetime.strptime(date_de_naissance, "%Y-%m-%d")
            date_naissance_formatee = date_obj.strftime("%d/%m/%Y")
            date_naissance_iso = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            date_naissance_formatee = date_de_naissance
            date_naissance_iso = ""
    else:
        date_naissance_formatee = ""
        date_naissance_iso = ""

    if date_sortie:
        try:
            date_obj = datetime.strptime(date_sortie, "%Y-%m-%d")
            date_sortie_formatee = date_obj.strftime("%d/%m/%Y")
            date_sortie_iso = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            date_sortie_formatee = date_sortie
            date_sortie_iso = ""
    else:
        date_sortie_formatee = ""
        date_sortie_iso = ""

    if date_poste:
        try:
            date_obj = datetime.strptime(date_poste, "%Y-%m-%d")
            date_poste_formatee = date_obj.strftime("%d/%m/%Y")
            date_poste_iso = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            date_poste_formatee = date_poste
            date_poste_iso = ""
    else:
        date_poste_formatee = ""
        date_poste_iso = ""

    if last_seen_date:
        try:
            date_obj = datetime.strptime(last_seen_date, "%Y-%m-%d")
            last_seen_date_formatee = date_obj.strftime("%d/%m/%Y")
            date_last_seen_date_iso = date_obj.strftime("%Y-%m-%d")  # <-- ici, dans le try
        except ValueError:
            last_seen_date_formatee = last_seen_date
            date_last_seen_date_iso = ""  # si la conversion échoue
    else:
        last_seen_date_formatee = ""
        date_last_seen_date_iso = ""

    if date_valable_sejour:
        try:
            date_obj = datetime.strptime(date_valable_sejour, "%Y-%m-%d")
            date_valable_sejour_formatee = date_obj.strftime("%d/%m/%Y")
            date_valable_sejour_iso = date_obj.strftime("%Y-%m-%d")  # <-- ici, dans le try
        except ValueError:
            date_valable_sejour_formatee = date_valable_sejour
            date_valable_sejour_iso = ""  # si la conversion échoue
    else:
        date_valable_sejour_formatee = ""
        date_valable_sejour_iso = ""

    # Récupération entreprise sélectionnée
    entreprise_id = request.POST.get("entreprise_id", None)
    entreprise_data = {}
    if entreprise_id:
        cursor.execute("SELECT * FROM entreprise WHERE id = ?", (entreprise_id,))
        entreprise_row = cursor.fetchone()
        if entreprise_row:
            entreprise_cols = [column[0] for column in cursor.description]
            entreprise_data = dict(zip(entreprise_cols, entreprise_row))

    # Détermination du type de document (ex: contrat_cdi_manuel, contrat_cdi_automatisation)
    type_doc = request.POST.get("type_doc", "contrat_cdi")

    # Choix template et dossier selon type_doc
    if type_doc == "contrat_cdi":
        template_name = "templates_docs/contrat_cdi.html"
        dossier = os.path.join(settings.BASE_DIR, "Contrat", "CDI")
    else:
        template_name = "templates_docs/default.html"
        dossier = os.path.join(settings.BASE_DIR, "Autres")

    os.makedirs(dossier, exist_ok=True)

    logo_url = entreprise_data.get("logo", "")
    cachet_url = entreprise_data.get("cachet", "")

    context = {
        # Données salarié
        "civilite": civilite,
        "prenom": prenom,
        "nom": nom,
        "date_de_naissance": date_naissance_formatee,
        "lieu_de_naissance": lieu_de_naissance,
        "nationalite": nationalite,
        "adresse_maison": adresse_maison,
        "num_secu": num_secu,
        "titre_sejour": titre_sejour,
        "num_sejour": num_sejour,
        "date_valable_sejour": date_valable_sejour_formatee,
        "poste": poste,
        "date_poste": date_poste_formatee,
        "position": position,
        "coefficient": coefficient,
        "lieu_de_travail": lieu_de_travail,
        "limit_geo_region": limit_geo_region,

        # Données entreprise
        "entreprise_nom": entreprise_data.get("entreprise_nom", ""),
        "adresse_localisation": entreprise_data.get("adresse_localisation", ""),
        "ville": entreprise_data.get("ville", ""),
        "num_societe": entreprise_data.get("num_societe", ""),
        "ape": entreprise_data.get("ape", ""),

        # Logo & cachet
        "logo": download_image_to_static(entreprise_data.get("logo", ""), logo_path),
        "cachet": download_image_to_static(entreprise_data.get("cachet", ""), cachet_path),


        # Date du document
        "date_document": date.today().strftime("%d/%m/%Y"),
        # "ville": ville,
    }

     # ✨ ENVOI DES DONNÉES VERS AIRTABLE
    AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    AIRTABLE_HEADERS = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    print("[DEBUG] Logo:", logo_url)
    print("[DEBUG] Cachet:", cachet_url)
    print("[DEBUG] entreprise data:", entreprise_data)

    airtable_payload = {
        "fields": {
            "NOM et Prénom": nom_complet,
            "Créé par": create_by,
            "Prénom": prenom,
            "NOM": nom,
            "Photo": photo,
            "Entité": entreprise_data.get("entreprise_nom", ""),
            "Email": email,
            "Nationnalité": nationalite,
            "Type de contrat": type_contrat,
            "Mutation?": mutation,
            "Equipe Manageriale": equipe_manageriale,
            "Adresse": adresse_maison,
            "Lieu de naissance": lieu_de_naissance,
            "Numéro de sécurité sociale": num_secu,
            "Titre de séjour": titre_sejour,
            "Numéro du titre de séjour": num_sejour,
            "Fonction": fonction,
            "Sexe": "Homme" if civilite == "Monsieur" else "Femme",
            "Statut": statut,
            "Etat": etat,
            "Localisation": lieu_de_travail,
            "Statut PE": statut_pe,
            "Départements": departement,
            "Intitulé du poste": poste,
            "Salaire brute": salaire_brut,
            "Position": position,
            "Coefficient": coefficient,
            "Limite géographique de la région": limit_geo_region,
            "Salaire brute mensuel": salaire_brut_mois,
            "Salaire net": salaire_net,
            "Spécialité": specialite,
        }
    }
    fields = airtable_payload["fields"]

    if logo_url:
        fields["Logo"] = [{"url": logo_url}]
        
    if cachet_url:
        fields["Cachet"] = [{"url": cachet_url}]


    if date_poste_iso:
        airtable_payload["fields"]["Date d'entrée"] = date_poste_iso
    
    if date_sortie_iso:
        airtable_payload["fields"]["Date de sortie"] = date_sortie_iso

    if date_naissance_iso:
        airtable_payload["fields"]["Date de Naissance"] = date_naissance_iso 

    if date_last_seen_date_iso:
        airtable_payload["fields"]["Last seen date"] = date_last_seen_date_iso 

    if date_valable_sejour_iso:
        airtable_payload["fields"]["Date de validité du titre de séjour"] = date_valable_sejour_iso

    # Filtrer pour enlever les clés avec valeur None ou ""
    fields = {k: v for k, v in fields.items() if v not in (None, "")}

    # Remettre dans le payload
    airtable_payload["fields"] = fields

    try:
        airtable_response = requests.post(
            AIRTABLE_API_URL,
            headers=AIRTABLE_HEADERS,
            json=airtable_payload
        )
        if airtable_response.status_code not in [200, 201]:
            print("[ERREUR Airtable]", airtable_response.text)
        else:
            print("[✅ Airtable] Données bien envoyées")
    except Exception as e:
        print("[EXCEPTION Airtable]", str(e))

    # Génération HTML et PDF
    html_string = render_to_string(template_name, context)
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=result)

    if pisa_status.err:
        return HttpResponse("Erreur lors de la génération du PDF", status=500)

    pdf_file = result.getvalue()

    # Nom fichier clair
    filename = f"{type_doc}_{prenom}_{nom}.pdf"
    file_path = os.path.join(dossier, filename)

    # Sauvegarde fichier PDF sur disque
    with open(file_path, "wb") as f:
        f.write(pdf_file)
    conn.close()

    # Retour fichier PDF en réponse HTTP
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # return response
    return redirect('/')

@login_required
def modifier_employer(request):
    # Récupérer les paramètres (par exemple via GET: prenom, nom)
    prenom = request.GET.get("prenom", "")
    nom = request.GET.get("nom", "")

    # Récupérer les données existantes (SQLite + Airtable)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE LOWER(prenom)=LOWER(?) AND LOWER(nom)=LOWER(?)", (prenom, nom))
    user_row = cursor.fetchone()
    user_data = {}
    if user_row:
        user_cols = [column[0] for column in cursor.description]
        user_data = dict(zip(user_cols, user_row))
    airtable_data_raw = airtable(prenom, nom) or {}

    # Mapping Airtable -> formulaire
    airtable_to_form = {
        "Prénom": "prenom",
        "NOM": "nom",
        "Sexe": "civilite",
        "Date de Naissance": "date_de_naissance",
        "Lieu de naissance": "lieu_de_naissance",
        "Nationnalité": "nationalite",
        "Adresse": "adresse_maison",
        "Numéro de sécurité sociale": "num_secu",
        "Titre de séjour": "titre_sejour",
        "Numéro du titre de séjour": "num_sejour",
        "Date de validité": "date_valable_sejour",
        "Poste": "poste",
        "Date d'entrée": "date_poste",
        "Position": "position",
        "Coefficient": "coefficient",
        "Localisation": "lieu_de_travail",
        "Limite geographique de la region": "limit_geo_region",
        "Entité": "entreprise_nom",
        "Email": "email",
        "Fonction": "fonction",
        "Salaire brute": "salaire_brut",
        "Salaire brute mensuel": "salaire_brut_mois",
        "Salaire net": "salaire_net",
        "Mutation?": "mutation",
        "Equipe Manageriale": "equipe_manageriale",
        "Statut": "statut",
        "Etat": "etat",
        "Statut PE": "statut_pe",
        "Last seen date": "last_seen_date",
        "Responsable hiéarchique": "responsable_hierarchique",
        "Départements": "departement",
        "Type de contrat": "type_contrat",
        "Date de sortie": "date_sortie",
        "Matricule": "matricule",
        "Spécialité": "specialite",
        "Photo": "photo",
        "Cachet": "cachet",
        "Logo": "logo",
        "Email Responsable hiéarchique": "email_responsable_hierarchique",
    }

    # Transforme les données Airtable pour correspondre aux clés du formulaire
    airtable_data = {}
    for k, v in airtable_data_raw.items():
        mapped_key = airtable_to_form.get(k, None)
        if mapped_key:
            airtable_data[mapped_key] = v

    merged_data = user_data.copy()
    merged_data.update(airtable_data)

    # Ajout de valeurs par défaut pour tous les champs attendus
    for key in [
        "prenom", "nom", "civilite", "date_de_naissance", "lieu_de_naissance", "nationalite",
        "adresse_maison", "num_secu", "titre_sejour", "num_sejour", "date_valable_sejour",
        "poste", "date_poste", "position", "coefficient", "lieu_de_travail", "limit_geo_region",
        "entreprise_nom", "email", "fonction", "salaire_brut", "salaire_brut_mois", "salaire_net",
        "mutation", "equipe_manageriale", "statut", "etat", "statut_pe", "last_seen_date", 
        "responsable_hierarchique", "departement", "type_contrat", "date_sortie", "matricule", "specialite"
    ]:
        merged_data.setdefault(key, "")

    cursor.execute("SELECT id, entreprise_nom FROM entreprise ORDER BY entreprise_nom")
    entreprises = cursor.fetchall()
    conn.close()

    if request.method == "POST":
        # Récupérer les données du formulaire
        form_data = {k: request.POST.get(k, "") for k in request.POST}
        nom_complet = f"{form_data.get('prenom', '').strip()} {form_data.get('nom', '').strip()}"

        # --- Conversion des dates en format ISO (yyyy-mm-dd) ---
        date_de_naissance = form_data.get("date_de_naissance", "")
        date_sortie = form_data.get("date_sortie", "")
        date_poste = form_data.get("date_poste", "")
        last_seen_date = form_data.get("last_seen_date", "")
        date_valable_sejour = form_data.get("date_valable_sejour", "")

        def to_iso(date_str):
            # Accepte 'dd/mm/yyyy' ou 'yyyy-mm-dd', retourne 'yyyy-mm-dd' ou ""
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                except Exception:
                    continue
            return ""

        date_naissance_iso = to_iso(date_de_naissance)
        date_sortie_iso = to_iso(date_sortie)
        date_poste_iso = to_iso(date_poste)
        date_last_seen_date_iso = to_iso(last_seen_date)
        date_valable_sejour_iso = to_iso(date_valable_sejour)

        # Mettre à jour SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Met à jour les champs principaux (adapter selon vos colonnes)
        cursor.execute("""
            UPDATE user SET prenom=?, nom=?, civilite=?, date_de_naissance=?, lieu_de_naissance=?, nationalite=?, adresse_maison=?, num_secu=?, titre_sejour=?, num_sejour=?, date_valable_sejour=?, poste=?, date_poste=?, position=?, coefficient=?, lieu_de_travail=?, limit_geo_region=?, entreprise=?, email=?, fonction=?, salaire_brut=?, salaire_brut_mois=?, salaire_net=?, mutation=?, equipe_manageriale=?, statut=?, etat=?, statut_pe=?, last_seen_date=?, responsable_hierarchique=?, departement=?, type_contrat=?, date_sortie=?, matricule=?, specialite=?
            WHERE LOWER(prenom)=LOWER(?) AND LOWER(nom)=LOWER(?)
        """, (
            form_data.get("prenom"), form_data.get("nom"), form_data.get("civilite"), date_naissance_iso,
            form_data.get("lieu_de_naissance"), form_data.get("nationalite"), form_data.get("adresse_maison"),
            form_data.get("num_secu"), form_data.get("titre_sejour"), form_data.get("num_sejour"),
            date_valable_sejour_iso, date_poste_iso,
            form_data.get("position"), form_data.get("coefficient"), form_data.get("lieu_de_travail"),
            form_data.get("email"), form_data.get("poste"), form_data.get("entreprise"),
            form_data.get("fonction"), form_data.get("salaire_brut"),
            form_data.get("mutation"), form_data.get("equipe_manageriale"),
            form_data.get("statut"), form_data.get("etat"), form_data.get("statut_pe"),
            date_last_seen_date_iso, date_sortie_iso,
            form_data.get("responsable_hierarchique"),
            form_data.get("departement"), form_data.get("type_contrat"),
            form_data.get("salaire_net"), form_data.get("salaire_brut_mois"), form_data.get("limit_geo_region"),
            form_data.get("matricule"), form_data.get("specialite"),
            prenom, nom
        ))

        conn.commit()
        conn.close()

        # Mettre à jour Airtable (écraser l'ancien)
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
        headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
        params = {"filterByFormula": f"AND(FIND('{prenom}', {{Prénom}}), FIND('{nom}', {{NOM}}))"}
        response = requests.get(url, headers=headers, params=params)
        record_id = None
        if response.status_code == 200:
            records = response.json().get("records", [])
            if records:
                record_id = records[0]["id"]

        # 2. Construire le payload de mise à jour (adapter les champs selon vos besoins)
        airtable_fields = {
            "Prénom": form_data.get("prenom"),
            "NOM": form_data.get("nom"),
            "NOM et Prénom": nom_complet,
            "Créé par": form_data.get("create_by"),
            "Photo": form_data.get("photo"),
            "Cachet": [{"url": form_data.get("cachet")}] if form_data.get("cachet") else None,
            "Logo": [{"url": form_data.get("logo")}] if form_data.get("logo") else None,
            "Email": form_data.get("email"),
            "Email Responsable hiéarchique": form_data.get("email_responsable_hierarchique"),
            "Entité": form_data.get("entreprise_nom"),
            "Fonction": form_data.get("fonction"),
            "Salaire brute": form_data.get("salaire_brut"),
            "Salaire brute mensuel": form_data.get("salaire_brut_mois"),
            "Salaire net": form_data.get("salaire_net"),
            "Mutation?": form_data.get("mutation"),
            "Equipe Manageriale": form_data.get("equipe_manageriale"),
            "Statut": form_data.get("statut"),
            "Statut PE": form_data.get("statut_pe"),
            "Last seen date": date_last_seen_date_iso,
            "Responsable hiéarchique": form_data.get("responsable_hierarchique"),
            "Départements": form_data.get("departement"),
            "Etat": form_data.get("etat"),
            "Nationnalité": form_data.get("nationalite"),
            "Type de contrat": form_data.get("type_contrat"),
            "Sexe": "Homme" if form_data.get("civilite", "") == "Monsieur" else "Femme",
            "Date de Naissance": date_naissance_iso,
            "Lieu de naissance": form_data.get("lieu_de_naissance"),
            "Nationnalité": form_data.get("nationalite"),
            "Adresse": form_data.get("adresse_maison"),
            "Numéro de sécurité sociale": form_data.get("num_secu"),
            "Titre de séjour": form_data.get("titre_sejour"),
            "Numéro du titre de séjour": form_data.get("num_sejour"),
            "Date de validité du titre de séjour": date_valable_sejour_iso,
            "Intitulé du poste": form_data.get("poste"),
            "Date d'entrée": date_poste_iso,
            "Date de sortie": date_sortie_iso,
            "Position": form_data.get("position"),
            "Coefficient": form_data.get("coefficient"),
            "Localisation": form_data.get("lieu_de_travail"),
            "Matricule": form_data.get("matricule"),
            "Spécialité": form_data.get("specialite"),
            "Limite geographique de la region": form_data.get("limit_geo_region"),
        }
        # Nettoyer les champs vides
        airtable_fields = {k: v for k, v in airtable_fields.items() if v}

        if record_id:
            patch_url = f"{url}/{record_id}"
            patch_headers = headers.copy()
            patch_headers["Content-Type"] = "application/json"

            try:
                airtable_response = requests.patch(
                    patch_url,
                    headers=patch_headers,
                    json={"fields": airtable_fields}
                )
                if airtable_response.status_code not in [200, 201]:
                    print("[ERREUR Airtable]", airtable_response.text)
                else:
                    print("[✅ Airtable] Données bien mises à jour")
            except Exception as e:
                print("[EXCEPTION Airtable]", str(e))


        # Rediriger vers la page d'accueil ou la preview
        return redirect('/')

    # GET : afficher le formulaire pré-rempli
    return render(request, "templates_docs/modifier_employer.html", {
        "form_data": merged_data,
        "entreprises": entreprises,
        "year": localdate().year,
        "today": localdate().isoformat(),
    })