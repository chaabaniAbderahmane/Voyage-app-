# 🚌 Voyages en Bus — App de gestion de présences, places & fidélité

Application Streamlit pour organiser des sorties en bus : ajout des voyageurs (admin),
check-in nominatif, placement automatique dans le bus, QR codes personnels,
messagerie admin ↔ client, et programme de fidélité (10e voyage offert).

## Fonctionnalités

**Côté Admin**
- Créer un voyage et ses bus (nombre de rangées, sièges par rangée)
- Ajouter des voyageurs un par un (formulaire) ou en masse (texte collé/dicté)
- Identifiants générés automatiquement : `identifiant = nom-prenom`, `mot de passe = Nom` (1ère lettre en majuscule)
- Placement automatique des places (groupes/familles ensemble, solos regroupés par genre)
- Suivi des présences en temps réel + possibilité de confirmer à la place d'un client (personnes âgées, etc.)
- Génération des QR codes individuels (un par un ou tout un bus d'un coup)
- Messagerie privée avec chaque voyageur
- Suivi des points de fidélité

**Côté Client**
- Connexion par identifiant/mot de passe **ou** en scannant son QR code (connexion automatique)
- Voit son bus et sa place assignée
- Bouton unique "Je suis présent(e)" pour le check-in
- Chat privé avec l'organisateur
- Suivi de ses points de fidélité et alerte quand un voyage gratuit est débloqué

## Déploiement sur Streamlit Community Cloud

1. Créez un dépôt GitHub et poussez-y tout le contenu de ce dossier.
2. Sur [share.streamlit.io](https://share.streamlit.io), cliquez sur **New app**, sélectionnez
   le dépôt et indiquez `app.py` comme fichier principal.
3. Dans **Settings → Secrets**, collez :
   ```toml
   admin_password = "votre-mot-de-passe-admin"
   ```
4. Déployez. Une fois l'URL obtenue (ex : `https://mon-voyage.streamlit.app`), retournez
   dans l'onglet **Admin → Bus & lien de l'app** et collez-la : elle sert à générer des QR
   codes qui ouvrent directement le bon profil client.

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Mot de passe admin par défaut si aucun secret n'est configuré : `admin123`
(à changer absolument avant tout usage réel).

## Le flux "réservation en ligne → check-in QR le jour J"

1. Un client réserve par téléphone / Facebook / etc.
2. L'admin l'ajoute dans l'app (onglet **Ajouter des voyageurs**) → un identifiant et
   un mot de passe sont générés, et le point de fidélité précédent est automatiquement
   repris s'il a déjà voyagé avec vous.
3. Avant le départ, l'admin lance le **Placement automatique** pour le bus.
4. L'admin génère/imprime les QR codes (onglet **QR codes**).
5. Le jour J, le client scanne son QR code → l'app s'ouvre directement sur son profil,
   avec sa place et un bouton "Je suis présent(e)".
6. À chaque présence confirmée, 1 point est ajouté. Au 10e point, un voyage gratuit
   est débloqué automatiquement.

## Limites connues (MVP) & pistes d'amélioration

- **Base de données** : SQLite en fichier local. Sur Streamlit Community Cloud, le
  système de fichiers est réinitialisé à chaque redéploiement/redémarrage de l'app.
  Pour un usage en production avec plusieurs organisateurs ou beaucoup de voyages,
  remplacez `utils/db.py` par une base hébergée (Supabase/PostgreSQL, Turso, etc.) —
  la structure des fonctions reste la même, seule la connexion change.
- **Saisie vocale** : la reconnaissance vocale native (micro → texte) n'est pas fiable
  "out of the box" sur Streamlit Cloud (pas d'accès micro serveur). La solution простой
  et robuste retenue ici est d'utiliser le micro du clavier de votre téléphone/ordinateur
  (icône 🎤 du clavier) pour dicter directement dans les champs de texte — cela fonctionne
  partout sans dépendance supplémentaire. Pour une vraie transcription serveur, on peut
  ajouter `streamlit-mic-recorder` + un service de speech-to-text (Whisper API, Google STT).
- **Placement automatique** : algorithme "best fit" qui garde les groupes ensemble et
  rapproche les solos de même genre. Sur des configurations 2+2, un groupe de 3+ personnes
  ne peut pas toujours tenir dans un seul bloc de 2 sièges contigus (limite physique du bus,
  pas de l'algorithme) — il est alors réparti sur la rangée la plus proche possible.
- **Sécurité** : les mots de passe sont volontairement simples (nom de famille) pour rester
  accessibles à tous les âges, comme demandé. Pour plus de sécurité, on peut ajouter un
  code confidentiel à 4 chiffres envoyé par SMS en plus du mot de passe.

## Idées pour aller plus loin

- Notifications push/SMS automatiques (ex : Twilio) quand le bus est complet ou qu'un
  client n'a toujours pas confirmé sa présence 10 minutes avant le départ.
- Export PDF de la feuille de route du bus (liste + plan de places) pour le chauffeur.
- Tableau de bord multi-voyages avec statistiques (taux de présence, fidélité moyenne).
- Rôle "chauffeur" en lecture seule (juste la liste + présences, sans droits d'édition).
- Carte interactive de la place dans le bus (plan visuel cliquable) plutôt qu'un code texte.
