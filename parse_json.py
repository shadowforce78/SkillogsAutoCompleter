import json


def parse_skillogs_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)
    except FileNotFoundError:
        print(f"Erreur: Le fichier {file_path} n'a pas été trouvé.")
        return None
    except json.JSONDecodeError:
        print(f"Erreur: Impossible de décoder le fichier JSON {file_path}.")
        return None

    # 1. Lire la pagination et comparer avec le nombre d'IDs trouvés
    pagination = content.get("pagination", {})
    total_pagination = pagination.get("total", 0)

    data_items = content.get("data", [])
    count_ids = len(data_items)

    print(f"--- Vérification Pagination ---")
    print(f"Total indiqué dans pagination : {total_pagination}")
    print(f"Nombre d'éléments trouvés   : {count_ids}")

    if total_pagination != count_ids:
        print(
            "Attention : Le nombre d'éléments ne correspond pas au total de la pagination."
        )
    else:
        print("Succès : Les comptes correspondent.")
    print("-------------------------------")

    results = {}

    # 2. Pour chaque ID, extraire les données demandées
    for item in data_items:
        item_id = item.get("id")
        if not item_id:
            continue

        layout_data = item.get("flexible_content_layout_data", [])

        extracted_layouts = []

        for layout_item in layout_data:
            # Récupérer la key et le layout global
            global_key = layout_item.get("key")
            global_layout = layout_item.get("layout")

            attributes = layout_item.get("attributes", {})
            inner_flexible_content = attributes.get("flexible_content", [])

            inner_contents = []

            # Pour chaque flexible_content, key et layout associé
            for inner in inner_flexible_content:
                inner_key = inner.get("key")
                inner_layout = inner.get("layout")

                inner_contents.append({"key": inner_key, "layout": inner_layout})
            
            # Gestion des Quizs (qui sont dans 'flexible_quiz' au lieu de 'flexible_content')
            inner_flexible_quiz = attributes.get("flexible_quiz", [])
            for inner in inner_flexible_quiz:
                inner_key = inner.get("key")
                inner_layout = inner.get("layout")
                inner_contents.append({"key": inner_key, "layout": inner_layout})
            
            # Empêcher l'envoi de listes vides, qui provoquent des erreurs 422
            if not inner_contents:
                 continue

            extracted_layouts.append(
                {
                    "global_key": global_key,
                    "global_layout": global_layout,
                    "flexible_contents": inner_contents,
                }
            )

        results[item_id] = extracted_layouts

    return results


def parse_link(link):
    cohort_id = ""
    module_id = ""
    session_id = ""
    content_id = ""
    parts = link.split("/")
    for i in range(len(parts)):
        if parts[i] == "cohort":
            cohort_id = parts[i + 1]
        elif parts[i] == "module":
            module_id = parts[i + 1]
        elif parts[i] == "session":
            session_id = parts[i + 1]
        elif parts[i] == "content":
            content_id = parts[i + 1]
    return cohort_id, module_id, session_id, content_id