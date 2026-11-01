"""
Application Streamlit - Gestion des notes d'Informatique
Collège Saint Thomas de Manjo - Année scolaire 2025-2026
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from database import (
    CLASSES, CLASS_LABELS,
    get_eleves, ajouter_eleve, modifier_eleve, supprimer_eleve,
    update_notes, get_statistiques, calculer_moyennes_et_rangs,
    init_db
)

# Configuration de la page
st.set_page_config(
    page_title="Notes Informatique - Manjo",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1F4E79 0%, #2E75B6 100%);
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        color: white !important;
        margin: 0;
        font-size: 1.8rem;
    }
    .main-header p {
        color: #D6EAF8;
        margin: 0.3rem 0 0 0;
        font-size: 1rem;
    }
    .stat-card {
        background: #f8f9fa;
        border-left: 4px solid #1F4E79;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
    }
    .success-badge {
        background: #D5F5E3;
        color: #196F3D;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-weight: 600;
    }
    .fail-badge {
        background: #FADBD8;
        color: #C0392B;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
    }
    .stDataFrame {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def header():
    st.markdown("""
    <div class="main-header">
        <h1>📚 Notes d'Informatique</h1>
        <p>Collège Saint Thomas de Manjo — Année scolaire 2025-2026</p>
    </div>
    """, unsafe_allow_html=True)


def sidebar():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2436/2436874.png", width=80)
        st.title("Navigation")
        st.markdown("---")

        page = st.radio(
            "Menu",
            ["🏠 Accueil", "📝 Saisie des notes", "📊 Statistiques", "👥 Gestion des élèves", "ℹ️ Aide"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### Classe active")
        classe = st.selectbox(
            "Choisir la classe",
            CLASSES,
            format_func=lambda x: f"{x} — {CLASS_LABELS.get(x, x)}",
            key="classe_select"
        )
        st.session_state["classe"] = classe

        eleves = get_eleves(classe)
        st.metric("Effectif", len(eleves))

        st.markdown("---")
        st.markdown("### 📥 Exporter les données")
        if st.button("Télécharger Excel", use_container_width=True):
            st.session_state["do_export"] = True
        st.caption("Sauvegardez régulièrement vos données")
        st.markdown("---")
        st.caption("Collège Saint Thomas de Manjo")
        return page, classe


def page_accueil(classe: str):
    header()
    st.subheader(f"Classe : {CLASS_LABELS.get(classe, classe)}")

    eleves = get_eleves(classe)
    stats = get_statistiques(classe)

    if stats["effectif"] == 0:
        st.info("Aucun élève enregistré dans cette classe. Allez dans **Gestion des élèves** pour en ajouter.")
        return

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Effectif total", stats["effectif"])
    with col2:
        st.metric("Filles", stats["filles"])
    with col3:
        st.metric("Garçons", stats["garcons"])
    with col4:
        moy = stats.get("moy1_classe")
        st.metric("Moy. 1er Trimestre", f"{moy:.2f}" if moy else "—")

    st.markdown("---")

    # Aperçu des notes
    eleves_enrichis = calculer_moyennes_et_rangs(eleves.copy())
    df = pd.DataFrame(eleves_enrichis)

    display_cols = ["nom", "sexe", "eval1", "eval2", "moy1", "rang1",
                    "eval3", "eval4", "moy2", "rang2",
                    "eval5", "eval6", "moy3", "rang3"]
    df_display = df[[c for c in display_cols if c in df.columns]].copy()
    df_display.columns = ["Nom", "Sexe", "Eval1", "Eval2", "Moy1", "Rang1",
                          "Eval3", "Eval4", "Moy2", "Rang2",
                          "Eval5", "Eval6", "Moy3", "Rang3"]

    st.markdown("### Aperçu des notes")
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=400
    )


def page_saisie(classe: str):
    header()
    st.subheader(f"Saisie des notes — {CLASS_LABELS.get(classe, classe)}")

    eleves = get_eleves(classe)
    if not eleves:
        st.warning("Aucun élève dans cette classe. Ajoutez-en d'abord dans **Gestion des élèves**.")
        return

    eleves_enrichis = calculer_moyennes_et_rangs(eleves.copy())

    # Sélecteur d'élève
    options = {f"{e['nom']} ({e['sexe']})": e for e in eleves_enrichis}
    choix = st.selectbox("Sélectionner un élève", list(options.keys()))
    eleve = options[choix]

    st.markdown(f"**Élève :** {eleve['nom']} — Sexe : {eleve['sexe']}")

    # Formulaire par trimestre
    tab1, tab2, tab3 = st.tabs(["1er Trimestre (Eval 1 & 2)", "2e Trimestre (Eval 3 & 4)", "3e Trimestre (Eval 5 & 6)"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            e1 = st.number_input("Eval 1", min_value=0.0, max_value=20.0, step=0.5,
                                 value=float(eleve["eval1"]) if eleve["eval1"] is not None else 0.0,
                                 key="e1")
        with c2:
            e2 = st.number_input("Eval 2", min_value=0.0, max_value=20.0, step=0.5,
                                 value=float(eleve["eval2"]) if eleve["eval2"] is not None else 0.0,
                                 key="e2")
        with c3:
            moy = round((e1 + e2) / 2, 2) if (e1 or e2) else None
            st.metric("Moyenne T1", f"{moy:.2f}" if moy else "—")

        if st.button("💾 Enregistrer Trimestre 1", key="save_t1"):
            update_notes(eleve["id"], {"eval1": e1 if e1 > 0 else None, "eval2": e2 if e2 > 0 else None})
            st.success("Notes du 1er trimestre enregistrées !")
            st.rerun()

    with tab2:
        c1, c2, c3 = st.columns(3)
        with c1:
            e3 = st.number_input("Eval 3", min_value=0.0, max_value=20.0, step=0.5,
                                 value=float(eleve["eval3"]) if eleve["eval3"] is not None else 0.0,
                                 key="e3")
        with c2:
            e4 = st.number_input("Eval 4", min_value=0.0, max_value=20.0, step=0.5,
                                 value=float(eleve["eval4"]) if eleve["eval4"] is not None else 0.0,
                                 key="e4")
        with c3:
            moy = round((e3 + e4) / 2, 2) if (e3 or e4) else None
            st.metric("Moyenne T2", f"{moy:.2f}" if moy else "—")

        if st.button("💾 Enregistrer Trimestre 2", key="save_t2"):
            update_notes(eleve["id"], {"eval3": e3 if e3 > 0 else None, "eval4": e4 if e4 > 0 else None})
            st.success("Notes du 2e trimestre enregistrées !")
            st.rerun()

    with tab3:
        c1, c2, c3 = st.columns(3)
        with c1:
            e5 = st.number_input("Eval 5", min_value=0.0, max_value=20.0, step=0.5,
                                 value=float(eleve["eval5"]) if eleve["eval5"] is not None else 0.0,
                                 key="e5")
        with c2:
            e6 = st.number_input("Eval 6", min_value=0.0, max_value=20.0, step=0.5,
                                 value=float(eleve["eval6"]) if eleve["eval6"] is not None else 0.0,
                                 key="e6")
        with c3:
            moy = round((e5 + e6) / 2, 2) if (e5 or e6) else None
            st.metric("Moyenne T3", f"{moy:.2f}" if moy else "—")

        if st.button("💾 Enregistrer Trimestre 3", key="save_t3"):
            update_notes(eleve["id"], {"eval5": e5 if e5 > 0 else None, "eval6": e6 if e6 > 0 else None})
            st.success("Notes du 3e trimestre enregistrées !")
            st.rerun()

    # Tableau récapitulatif rapide
    st.markdown("---")
    st.markdown("### Récapitulatif de la classe (édition rapide)")

    df = pd.DataFrame(eleves_enrichis)
    edit_df = df[["id", "nom", "sexe", "eval1", "eval2", "eval3", "eval4", "eval5", "eval6"]].copy()
    edit_df.columns = ["ID", "Nom", "Sexe", "Eval1", "Eval2", "Eval3", "Eval4", "Eval5", "Eval6"]

    edited = st.data_editor(
        edit_df,
        use_container_width=True,
        hide_index=True,
        disabled=["ID", "Nom", "Sexe"],
        num_rows="fixed",
        key="bulk_editor"
    )

    if st.button("💾 Enregistrer toutes les modifications du tableau"):
        for _, row in edited.iterrows():
            notes = {
                "eval1": float(row["Eval1"]) if pd.notna(row["Eval1"]) else None,
                "eval2": float(row["Eval2"]) if pd.notna(row["Eval2"]) else None,
                "eval3": float(row["Eval3"]) if pd.notna(row["Eval3"]) else None,
                "eval4": float(row["Eval4"]) if pd.notna(row["Eval4"]) else None,
                "eval5": float(row["Eval5"]) if pd.notna(row["Eval5"]) else None,
                "eval6": float(row["Eval6"]) if pd.notna(row["Eval6"]) else None,
            }
            update_notes(int(row["ID"]), notes)
        st.success("Toutes les notes ont été mises à jour !")
        st.rerun()


def page_statistiques(classe: str):
    header()
    st.subheader(f"Statistiques — {CLASS_LABELS.get(classe, classe)}")

    stats = get_statistiques(classe)
    if stats["effectif"] == 0:
        st.info("Aucune donnée disponible pour cette classe.")
        return

    # KPIs principaux
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Effectif", stats["effectif"])
    with col2:
        st.metric("Filles", stats["filles"])
    with col3:
        st.metric("Garçons", stats["garcons"])
    with col4:
        st.metric("Moy. T1", f"{stats['moy1_classe']:.2f}" if stats["moy1_classe"] else "—")
    with col5:
        st.metric("Moy. T2", f"{stats['moy2_classe']:.2f}" if stats["moy2_classe"] else "—")

    st.markdown("---")

    # Taux de réussite
    st.markdown("### Taux de réussite (≥ 10/20)")

    taux_data = []
    labels_map = {
        "eval1": "Eval 1", "eval2": "Eval 2", "moy1": "Moy T1",
        "eval3": "Eval 3", "eval4": "Eval 4", "moy2": "Moy T2",
        "eval5": "Eval 5", "eval6": "Eval 6", "moy3": "Moy T3",
    }
    for key, label in labels_map.items():
        if key in stats["taux_reussite"]:
            t = stats["taux_reussite"][key]
            taux_data.append({
                "Séquence": label,
                "Filles (%)": t["filles"],
                "Garçons (%)": t["garcons"],
                "Total (%)": t["total"]
            })

    df_taux = pd.DataFrame(taux_data)
    st.dataframe(df_taux, use_container_width=True, hide_index=True)

    # Graphique taux de réussite
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Filles", x=df_taux["Séquence"], y=df_taux["Filles (%)"], marker_color="#9B59B6"))
    fig.add_trace(go.Bar(name="Garçons", x=df_taux["Séquence"], y=df_taux["Garçons (%)"], marker_color="#3498DB"))
    fig.add_trace(go.Bar(name="Total", x=df_taux["Séquence"], y=df_taux["Total (%)"], marker_color="#27AE60"))
    fig.update_layout(
        barmode="group",
        title="Taux de réussite par séquence",
        yaxis_title="Pourcentage (%)",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Moyennes de classe
    st.markdown("### Moyennes de la classe")
    moy_data = {
        "Séquence": ["Eval 1", "Eval 2", "Moy T1", "Eval 3", "Eval 4", "Moy T2", "Eval 5", "Eval 6", "Moy T3"],
        "Moyenne": [
            stats["moy_classe"].get("eval1"),
            stats["moy_classe"].get("eval2"),
            stats["moy1_classe"],
            stats["moy_classe"].get("eval3"),
            stats["moy_classe"].get("eval4"),
            stats["moy2_classe"],
            stats["moy_classe"].get("eval5"),
            stats["moy_classe"].get("eval6"),
            stats["moy3_classe"],
        ]
    }
    df_moy = pd.DataFrame(moy_data)
    fig2 = px.line(df_moy, x="Séquence", y="Moyenne", markers=True, title="Évolution des moyennes de classe")
    fig2.update_traces(line_color="#1F4E79", line_width=3)
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)

    # Max / Min
    st.markdown("### Notes extrêmes")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Plus grandes notes**")
        for k, v in stats["max"].items():
            st.write(f"- {k.upper()} : **{v}**" if v is not None else f"- {k.upper()} : —")
    with col_b:
        st.write("**Plus petites notes**")
        for k, v in stats["min"].items():
            st.write(f"- {k.upper()} : **{v}**" if v is not None else f"- {k.upper()} : —")


def page_gestion_eleves(classe: str):
    header()
    st.subheader(f"Gestion des élèves — {CLASS_LABELS.get(classe, classe)}")

    eleves = get_eleves(classe)

    # Ajout d'un élève
    with st.expander("➕ Ajouter un nouvel élève", expanded=True):
        with st.form("ajout_eleve"):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                nom = st.text_input("Nom et prénoms")
            with c2:
                sexe = st.selectbox("Sexe", ["F", "M"])
            with c3:
                st.write("")
                st.write("")
                submitted = st.form_submit_button("Ajouter")
            if submitted:
                if not nom.strip():
                    st.error("Le nom est obligatoire.")
                else:
                    try:
                        ajouter_eleve(classe, nom, sexe)
                        st.success(f"Élève **{nom.upper()}** ajouté avec succès !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : cet élève existe déjà ou {e}")

    st.markdown("---")
    st.markdown(f"### Liste des élèves ({len(eleves)})")

    if not eleves:
        st.info("Aucun élève enregistré.")
        return

    for e in eleves:
        col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
        with col1:
            st.write(f"**{e['nom']}**")
        with col2:
            st.write(e["sexe"])
        with col3:
            if st.button("✏️", key=f"edit_{e['id']}", help="Modifier"):
                st.session_state[f"edit_mode_{e['id']}"] = True
        with col4:
            if st.button("🗑️", key=f"del_{e['id']}", help="Supprimer"):
                supprimer_eleve(e["id"])
                st.success("Élève supprimé.")
                st.rerun()

        if st.session_state.get(f"edit_mode_{e['id']}"):
            with st.form(f"form_edit_{e['id']}"):
                new_nom = st.text_input("Nouveau nom", value=e["nom"])
                new_sexe = st.selectbox("Sexe", ["F", "M"], index=0 if e["sexe"] == "F" else 1)
                if st.form_submit_button("Enregistrer"):
                    modifier_eleve(e["id"], new_nom, new_sexe)
                    st.session_state[f"edit_mode_{e['id']}"] = False
                    st.success("Modifié !")
                    st.rerun()


def page_aide():
    header()
    st.subheader("Aide & Guide d'utilisation")

    st.markdown("""
    ### Objectif de l'application
    Cette application permet d'enregistrer les notes d'**Informatique** des élèves du Collège Saint Thomas de Manjo 
    et de produire automatiquement les statistiques par classe après chaque séquence.

    ### Structure des trimestres
    | Trimestre | Évaluations | Moyenne | Rang |
    |-----------|-------------|---------|------|
    | 1er       | Eval 1 + Eval 2 | Moy 1 | Rang 1 |
    | 2e        | Eval 3 + Eval 4 | Moy 2 | Rang 2 |
    | 3e        | Eval 5 + Eval 6 | Moy 3 | Rang 3 |

    ### Comment utiliser
    1. **Choisir la classe** dans le menu de gauche
    2. **Ajouter les élèves** dans l'onglet « Gestion des élèves »
    3. **Saisir les notes** dans l'onglet « Saisie des notes »
       - Soit élève par élève
       - Soit en masse via le tableau éditable
    4. **Consulter les statistiques** (taux de réussite, moyennes, graphiques)

    ### Seuil de réussite
    Une note **≥ 10 / 20** est considérée comme une réussite.

    ### Données
    Les données sont stockées localement dans un fichier SQLite (`notes_informatique.db`).
    Vous pouvez sauvegarder ce fichier pour conserver vos données.
    """)


# ============== MAIN ==============
def export_to_excel():
    """Exporte toutes les classes vers un fichier Excel."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    wb = Workbook()
    wb.remove(wb.active)
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E79")
    thin = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    
    for classe in CLASSES:
        eleves = get_eleves(classe)
        if not eleves:
            continue
        eleves = calculer_moyennes_et_rangs(eleves)
        ws = wb.create_sheet(classe)
        headers = ["N°", "Nom", "Sexe", "Eval1", "Eval2", "Moy1", "Rang1",
                   "Eval3", "Eval4", "Moy2", "Rang2", "Eval5", "Eval6", "Moy3", "Rang3"]
        for col, h in enumerate(headers, 1):
            cell = ws.cell(1, col, h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        for i, e in enumerate(eleves, 1):
            row = [i, e["nom"], e["sexe"],
                   e.get("eval1"), e.get("eval2"), e.get("moy1"), e.get("rang1"),
                   e.get("eval3"), e.get("eval4"), e.get("moy2"), e.get("rang2"),
                   e.get("eval5"), e.get("eval6"), e.get("moy3"), e.get("rang3")]
            for col, val in enumerate(row, 1):
                ws.cell(i+1, col, val)
        ws.column_dimensions["B"].width = 30
    
    if not wb.sheetnames:
        ws = wb.create_sheet("Vide")
        ws["A1"] = "Aucune donnée"
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def main():
    init_db()
    page, classe = sidebar()
    
    # Gestion de l'export
    if st.session_state.get("do_export"):
        st.session_state["do_export"] = False
        buffer = export_to_excel()
        st.sidebar.download_button(
            label="⬇️ Cliquez ici pour télécharger",
            data=buffer,
            file_name="Notes_Informatique_Manjo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    if page == "🏠 Accueil":
        page_accueil(classe)
    elif page == "📝 Saisie des notes":
        page_saisie(classe)
    elif page == "📊 Statistiques":
        page_statistiques(classe)
    elif page == "👥 Gestion des élèves":
        page_gestion_eleves(classe)
    elif page == "ℹ️ Aide":
        page_aide()


if __name__ == "__main__":
    main()
