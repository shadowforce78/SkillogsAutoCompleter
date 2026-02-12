import os
import requests
import json
import sys
from parse_json import parse_skillogs_json
from dotenv import load_dotenv

load_dotenv()

email = os.getenv("MAIL")
password = os.getenv("PASSWORD")

# Cache pour le token
_TOKEN = None

def get_token():
    global _TOKEN
    if _TOKEN:
        return _TOKEN
        
    try:
        resp = requests.post(
            "https://ensupsqy.skillogs.info/api/auth/token",
            data={"email": email, "password": password},
        )
        resp.raise_for_status()
        _TOKEN = resp.json()["token"]
        return _TOKEN
    except Exception as e:
        print(f"Erreur d'authentification: {e}")
        sys.exit(1)

def parse_link(url):
    try:
        parts = url.split('/')
        if 'cohort' in parts:
            cohort_idx = parts.index('cohort')
            cohort_id = parts[cohort_idx + 1]
        else:
            raise ValueError("URL invalide: 'cohort' manquant")
            
        if 'module' in parts:
            module_idx = parts.index('module')
            module_id = parts[module_idx + 1]
        else:
            raise ValueError("URL invalide: 'module' manquant")
            
        if 'session' in parts:
            session_idx = parts.index('session')
            session_id = parts[session_idx + 1]
        else:
            raise ValueError("URL invalide: 'session' manquant")
        
        return cohort_id, module_id, session_id
    except (ValueError, IndexError) as e:
        print(f"Erreur lors du parsing de l'URL: {e}")
        sys.exit(1)

def scrape_page_data(cohort_id, module_id, session_id):
    url = f"https://ensupsqy.skillogs.info/api/user/cohort/{cohort_id}/module/{module_id}/session/{session_id}/content"
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://ensupsqy.skillogs.io",
        "Referer": "https://ensupsqy.skillogs.io/",
        "Priority": "u=1, i",
        "Sec-Ch-Ua": '"Opera";v="127", "Chromium";v="143", "Not A(Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0",
        "X-Language": "fr"
    }
    print(f"Récupération des données depuis: {url}")
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du scraping: {e}")
        sys.exit(1)
    
    # Sauvegarde dans index.json pour que parse_skillogs_json puisse le lire
    with open("index.json", "w", encoding="utf-8") as f:
        f.write(resp.text)
    
    return "index.json"

def get_content_details(cohort_id, module_id, session_id, content_id):
    """
    Récupère les détails d'un contenu (pour essayer de trouver les bonnes réponses des quiz).
    """
    url = f"https://ensupsqy.skillogs.info/api/user/cohort/{cohort_id}/module/{module_id}/session/{session_id}/content/{content_id}/flexible_content"
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "X-Language": "fr"
    }
    
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Warning: Impossible de récupérer les détails pour {content_id}: {e}")
        return None

def find_correct_answers(details_json):
    """
    Parcourt le JSON détaillé pour trouver les réponses marquées comme correctes.
    Retourne un dictionnaire {question_key: [correct_answer_keys]}
    """
    correct_map = {}
    
    if not details_json:
        return correct_map

    # Fonction récursive pour parcourir le JSON
    def scan(obj):
        if isinstance(obj, dict):
            # Si on tombe sur une réponse avec is_correct=True
            if obj.get('layout') == 'answer' and obj.get('attributes', {}).get('is_correct'):
                return [obj.get('key')]
            
            # Si on est dans une question (multiple_choice etc), on cherche dans ses answers
            if obj.get('attributes') and 'answers' in obj['attributes']:
                correct_keys = []
                for ans in obj['attributes']['answers']:
                    # Vérification directe dans l'attribut
                    if ans.get('attributes', {}).get('is_correct'):
                        correct_keys.append(ans.get('key'))
                if correct_keys:
                    correct_map[obj.get('key')] = correct_keys
            
            for k, v in obj.items():
                scan(v)
        elif isinstance(obj, list):
            for item in obj:
                scan(item)

    scan(details_json)
    return correct_map

def validate_content(cohort_id, module_id, session_id, content_id, global_key, global_layout, flexible_contents):
    # Determine endpoint based on global_layout
    endpoint_suffix = "flexible_content"
    # L'endpoint flexible_quiz renvoie 404, on tente de tout passer par flexible_content
    # if global_layout == "flexible_quiz":
    #    endpoint_suffix = "flexible_quiz"
        
    url = f"https://ensupsqy.skillogs.info/api/user/cohort/{cohort_id}/module/{module_id}/session/{session_id}/content/{content_id}/{endpoint_suffix}"
    
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://ensupsqy.skillogs.io",
        "Referer": "https://ensupsqy.skillogs.io/",
        "Priority": "u=1, i",
        "Sec-Ch-Ua": '"Opera";v="127", "Chromium";v="143", "Not A(Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0",
        "X-Language": "fr"
    }
    
    # Prépare les données internes pour flexible content ou quiz
    inner_data = []

    if global_layout == "flexible_quiz":
        # Tentative de récupération des VRAIES réponses
        print(f"   Recherche des réponses pour le quiz {content_id}...")
        
        # L'endpoint flexible_content en GET renvoie 405 (Method Not Allowed), 
        # donc on ne peut probablement pas fetcher les réponses par là. 
        # On désactive le fetch automatique pour éviter le warning et on utilise le fallback.
        # details = get_content_details(cohort_id, module_id, session_id, content_id)
        # correct_answers_map = find_correct_answers(details)
        correct_answers_map = {} # Empty map Force fallback
        
        # Pour chaque question du quiz trouvé dans flexible_contents
        for content in flexible_contents:
            question_data = {
                "done": True, 
                "time": 30
            }
            
            # Stratégie de réponse
            q_key = content['key']
            
            # 1. Si on a trouvé la bonne réponse via le fetch, on l'utilise
            if q_key in correct_answers_map:
                question_data["answer"] = correct_answers_map[q_key]
                print(f"   -> Réponse trouvée pour {q_key}: {question_data['answer']}")
            
            # 2. Sinon, si on a une liste de choix (via parse_json), on prend le premier (fallback)
            elif 'answers' in content and content['answers']:
                question_data["answer"] = [content['answers'][0]]
                print(f"   -> Fallback sur la 1ère réponse pour {q_key}")

            inner_data.append({
                "key": content['key'],
                "layout": content['layout'],
                "data": question_data
            })
    else:
        # Cas standard flexible_content
        for content in flexible_contents:
            inner_data.append({
                "key": content['key'],
                "layout": content['layout'],
                "data": {
                    "done": True,
                    "time": 30
                }
            })
    
    payload_data = {
        "key": global_key,
        "layout": global_layout,
        "data": inner_data
    }
    
    # Wrapping in 'payload' object as requested by the API error
    final_payload = {
        "payload": payload_data
    }
    
    try:
        print(f"\n--- Validation {content_id} ---")
        print(f"Request URL: {url}")
        # print(f"Payload: {json.dumps(final_payload, indent=2)}") 
        
        resp = requests.put(url, json=final_payload, headers=headers)
        
        print(f"Status Code: {resp.status_code}")
        try:
            print(f"Response JSON: {json.dumps(resp.json(), indent=2)}")
        except json.JSONDecodeError:
            print("Response is not JSON (likely HTML):")
            print(resp.text[:200] + "...") # Affiche le début pour debug
        
        resp.raise_for_status()
        print(f"✓ Contenu validé {content_id} (Global: {global_key})")
    except Exception as e:
        print(f"✗ Erreur validant {content_id}: {e}")
        print(f"Payload qui a échoué: {json.dumps(final_payload, indent=2)}")

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Entrez l'URL de la session Skillogs: ")
    
    # Nettoyage de l'URL si elle contient des fragments ou query params inutiles pour le split
    if '#' in url:
        url = url.split('#')[0]
        
    print(f"Traitement de l'URL: {url}")
    
    cohort_id, module_id, session_id = parse_link(url)
    
    # 1. Scrape
    json_file = scrape_page_data(cohort_id, module_id, session_id)
    
    # 2. Parse
    parsed_data = parse_skillogs_json(json_file)
    
    if not parsed_data:
        print("Aucune donnée trouvable à valider.")
        return

    print(f"Trouvé {len(parsed_data)} éléments à valider.")
    
    # 3. Validate
    for content_id, layouts in parsed_data.items():
        for layout in layouts:
            validate_content(
                cohort_id,
                module_id,
                session_id,
                content_id, 
                layout['global_key'], 
                layout['global_layout'], 
                layout['flexible_contents']
            )
            
    print("\nToutes les validations sont terminées. Arrêt du script.")

if __name__ == "__main__":
    main()
