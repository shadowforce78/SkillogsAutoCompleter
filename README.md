# Skillogs AutoCompleter

Ce projet permet d'automatiser la validation des contenus flexibles sur la plateforme Skillogs (ent.skillogs.io).

Il scrape les données d'une session, analyse la structure des cours (vidéos, HTML, quiz, images, etc.) et envoie automatiquement des requêtes de validation pour marquer chaque élément comme "complété" avec un temps de lecture simulé.

## Prérequis

*   Python 3.x
*   Un compte Skillogs valide

## Installation

1.  Clonez le dépôt :
    ```bash
    git clone https://github.com/shadowforce78/SkillogsAutoCompleter.git
    cd SkillogsAutoCompleter
    ```

2.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
    *(Si le fichier `requirements.txt` n'existe pas, installez manuellement `requests` et `python-dotenv`)*:
    ```bash
    pip install requests python-dotenv
    ```

3.  Configurez l'authentification :
    Créez un fichier `.env` à la racine du projet et ajoutez-y vos identifiants :
    ```env
    MAIL=votre.email@ecole.eu
    PASSWORD=votreMotDePasse
    ```

## Utilisation

Lancez le script en lui passant l'URL de la session Skillogs que vous souhaitez valider :

```bash
python3 script.py "https://ensupsqy.skillogs.io/cohort/XXXX/module/YYYY/session/ZZZZ/"
```

Si vous ne passez pas l'URL en argument, le script vous la demandera de manière interactive.

### Fonctionnement détaillé

1.  **Authentification** : Le script récupère un token Bearer via l'API de Skillogs.
2.  **Scraping** : Il télécharge le contenu JSON de la session spécifiée localement (`index.json`).
3.  **Parsing** : Il analyse ce JSON pour extraire tous les "flexible contents" (vidéos, quizs, textes) et leurs clés uniques (`global_key`, `key`).
4.  **Validation** : Il itère sur chaque élément et envoie une requête `PUT` à l'API pour le valider (`done: true`, `time: 30s`).

## Avertissement

Ce script est fourni à titre éducatif ou pour des tests. L'utilisation de bots ou de scripts automatisés peut être contraire aux conditions d'utilisation de la plateforme cible. Utilisez-le de manière responsable.

## Structure du projet

*   `script.py` : Point d'entrée principal. Gère l'auth, le scraping et la boucle de validation.
*   `parse_json.py` : Module utilitaire pour parser le JSON complexe de Skillogs et extraire les clés nécessaires.
*   `index.json` : Fichier temporaire stockant les données brutes de la session (créé automatiquement).
