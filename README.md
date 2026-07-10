# 🚌 Voyages en Bus — App de gestion de présences, places & fidélité

Application Streamlit à **structure plate** : tous les fichiers `.py` sont au même
niveau (pas de dossier `pages/` ni `utils/`). Une seule page s'affiche à l'écran,
et son contenu change selon le rôle connecté (Admin ou Client).

## Fichiers

```
app.py            → point d'entrée unique (routage par rôle uniquement)
auth.py           → connexion (onglet Admin / onglet Client) + QR auto-login
admin_view.py      → tout le code de l'espace admin (importé seulement si role="admin")
client_view.py     → tout le code de l'espace client (importé seulement si role="client")
db.py             → base de données SQLite
seating.py        → algorithme de placement automatique dans le bus
qr_utils.py       → génération des QR codes
requirements.txt
```

## Cloisonnement des privilèges (important)

- Une seule variable contrôle l'accès : `st.session_state["role"]`, qui vaut
  `"admin"` ou `"client"` — jamais les deux à la fois.
- Tant qu'aucun rôle n'est défini, seul l'écran de connexion (`auth.login_screen`)
  s'affiche : aucune fonction admin ni aucun profil client n'est accessible.
- `admin_view.py` n'est **importé** que si `role == "admin"` ; `client_view.py`
  n'est importé que si `role == "client"`. Un client ne peut donc jamais exécuter
  de code admin (et inversement), même en modifiant l'URL.
- Chaque vue vérifie aussi son rôle en interne (`if st.session_state.get("role") != ...`)
  comme double sécurité.
- Le bouton "Se déconnecter" efface le rôle et renvoie à l'écran de connexion.

## Déploiement sur Streamlit Community Cloud

1. Créez un dépôt GitHub et poussez-y **tout le contenu de ce dossier** (fichiers
   à la racine du dépôt, pas dans un sous-dossier).
2. Sur [share.streamlit.io](https://share.streamlit.io) → **New app** → sélectionnez
   le dépôt → fichier principal : `app.py`.
3. Dans **Settings → Secrets**, collez :
   ```toml
   admin_password = "votre-mot-de-passe-admin"
   ```
4. Déployez. Une fois l'URL obtenue (ex : `https://mon-voyage.streamlit.app`),
   retournez dans **Espace Admin → Bus & lien de l'app** et collez-la : elle sert
   à générer des QR codes qui ouvrent directement le bon profil client.

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Mot de passe admin par défaut si aucun secret n'est configuré : `admin123`
(à changer avant tout usage réel).

## Le flux "réservation en ligne → check-in QR le jour J"

1. Un client réserve par téléphone / Facebook / etc.
2. L'admin l'ajoute dans l'app → un identifiant et un mot de passe sont générés
   automatiquement (`identifiant = nom-prenom`, `mot de passe = Nom`), et ses
   points de fidélité sont repris s'il a déjà voyagé avec vous.
3. Avant le départ, l'admin lance le **Placement automatique** pour le bus.
4. L'admin génère/imprime les QR codes.
5. Le jour J, le client scanne son QR code → l'app s'ouvre directement sur son
   profil (rôle "client" uniquement), avec sa place et un bouton "Je suis présent(e)".
6. Chaque présence confirmée ajoute 1 point. Au 10e point, un voyage gratuit est
   débloqué automatiquement.

## Limites connues & pistes d'amélioration

- **Base de données** : SQLite en fichier local (`voyages.db`, créé automatiquement).
  Sur Streamlit Community Cloud, le système de fichiers est réinitialisé à chaque
  redéploiement/redémarrage. Pour un usage récurrent en production, remplacez le
  contenu de `db.py` par une base hébergée (Supabase/PostgreSQL, Turso...) — la
  signature des fonctions reste la même, seule la connexion change.
- **Saisie vocale** : utilisez le micro 🎤 du clavier de votre téléphone/ordinateur
  pour dicter directement dans les champs de texte (fiable partout, sans dépendance
  supplémentaire). Une vraie transcription serveur nécessiterait un service externe
  (Whisper API, Google STT).
- **Placement automatique** : un groupe de 3+ personnes ne peut pas toujours tenir
  dans un seul bloc de 2 sièges contigus sur une configuration 2+2 (limite physique
  du bus) — il est alors réparti sur la rangée la plus proche possible.
- **Sécurité** : mots de passe volontairement simples (nom de famille) pour rester
  accessibles à tous les âges. On peut ajouter un code confidentiel envoyé par SMS
  pour plus de sécurité.

## Idées pour aller plus loin

- Notifications SMS automatiques (Twilio) si un client n'a pas confirmé sa présence
  quelques minutes avant le départ.
- Export PDF de la feuille de route du bus (liste + plan de places) pour le chauffeur.
- Rôle "chauffeur" en lecture seule.
- Plan de bus visuel cliquable plutôt qu'un code de siège textuel.
