#!/bin/bash
# Lance l'application Notes Informatique
cd "$(dirname "$0")"
echo "Installation des dépendances si nécessaire..."
pip install -q -r requirements.txt 2>/dev/null || true
echo "Lancement de l'application Streamlit..."
echo "Ouvrez votre navigateur à l'adresse affichée (généralement http://localhost:8501)"
streamlit run app.py --server.headless true
