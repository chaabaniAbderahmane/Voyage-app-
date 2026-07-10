# 🚌 Voyages en Bus — v3

Structure à plat (aucun sous-dossier). Fichier principal à déployer sur
Streamlit Cloud : `app.py`. Mot de passe admin par défaut : `admin123`
(à changer via `admin_password` dans Settings → Secrets).

## Nouveautés de cette version

- **Groupes en liste déroulante** : créez d'abord vos groupes (famille / couple /
  amis) dans l'onglet « Groupes », puis choisissez-les dans une liste (plus de
  texte libre) au moment d'ajouter chaque voyageur — formulaire simple ou
  tableau éditable pour ajouter plusieurs personnes d'un coup.
- **Algorithme de placement amélioré** : les groupes plus grands que la largeur
  d'une rangée (ex : famille de 4 dans un bus 2+2) restent regroupés en
  s'étendant sur les rangées voisines du même côté du bus, au lieu d'être
  éclatés. Priorité : famille > couple > amis > solos regroupés par genre.
- **Lien public codé en dur** : `https://checkbus.streamlit.app` est fixé dans
  `config.py` et n'apparaît plus dans l'interface — il est utilisé automatiquement
  pour générer tous les QR codes.
- **Voyage et bus modifiables** : renommer/changer la date du voyage, éditer ou
  supprimer un bus (rangées, sièges par rangée), avec confirmation.
- **Interface repensée** : bannière dégradée, cartes, badges de statut, thème
  cohérent (`styles.py`), navigation par onglets horizontaux avec tableau de
  bord (statistiques + graphique d'occupation par bus).
- **Messagerie façon vraie appli de chat** : bulles avec avatars (`st.chat_message`),
  liste des conversations triée « non lues d'abord », et surtout une **bannière
  de notification permanente en haut de l'espace admin** (« 🔔 X nouveaux
  messages ») avec un bouton qui ouvre directement la messagerie — plus besoin
  de chercher. Côté client, la même bannière fait remonter le chat tout en haut
  de la page s'il y a un nouveau message de l'organisateur.
- **Autres ajouts utiles** :
  - Recherche de voyageur par nom, export CSV de la liste.
  - Modifier ou supprimer un voyageur, régénérer son identifiant/mot de passe.
  - Marquer un voyage gratuit comme utilisé (remet les points à 0).
  - Tableau de bord avec graphique d'occupation des bus.

## Déploiement

1. Poussez tout le contenu de ce dossier à la **racine** d'un dépôt GitHub.
2. Streamlit Cloud → New app → fichier principal `app.py`.
3. Secrets : `admin_password = "votre-mot-de-passe"`.
4. C'est tout — l'URL des QR codes est déjà fixée sur `https://checkbus.streamlit.app`.
   Si vous redéployez sous une autre URL, changez `APP_URL` dans `config.py`.
