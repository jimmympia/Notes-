# 📚 Notes d'Informatique — Collège Saint Thomas de Manjo

Application web pour gérer les notes d'Informatique et produire les statistiques par classe.

**Accessible depuis un téléphone** une fois publiée en ligne.

---

## Utilisation depuis un téléphone (recommandé)

### Option A — Publication gratuite sur Streamlit Cloud (la meilleure)

1. Créez un compte gratuit sur [GitHub](https://github.com)
2. Créez un **nouveau dépôt** (repository)
3. Téléversez les fichiers de ce dossier (`app.py`, `database.py`, `requirements.txt`, dossier `.streamlit`)
4. Allez sur [https://share.streamlit.io](https://share.streamlit.io)
5. Connectez votre compte GitHub
6. Cliquez sur **New app**, choisissez votre dépôt et le fichier `app.py`
7. Cliquez sur **Deploy**

Vous obtiendrez une adresse publique du type :
```
https://notes-informatique-manjo.streamlit.app
```
Ouvrez cette adresse dans le navigateur de votre téléphone.

> **Note importante** : Sur la version gratuite de Streamlit Cloud, les données sont temporaires (elles peuvent être effacées quand l'application se met en veille). Utilisez le bouton **Télécharger Excel** régulièrement pour sauvegarder vos notes.

### Option B — Même réseau Wi-Fi

1. Lancez l'application sur un ordinateur : `streamlit run app.py`
2. Notez l'adresse **Network URL** affichée (ex. `http://192.168.1.25:8501`)
3. Ouvrez cette adresse dans le navigateur du téléphone (même Wi-Fi)

---

## Lancement en local (ordinateur)

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Fonctionnalités

- Gestion des élèves par classe
- Saisie des notes (6 évaluations / 3 trimestres)
- Calcul automatique des moyennes et rangs
- Statistiques et graphiques
- Export Excel
- 17 classes du collège

---

## Seuil de réussite

Note ≥ 10 / 20
