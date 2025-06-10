import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Éditeur de Données", layout="wide")

# Titre
st.title("📊 Éditeur de Données Interactif")

# Fonction pour charger les données
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        try:
            return pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Erreur de chargement: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# Upload de fichier
uploaded_file = st.file_uploader("Importer un fichier Excel", type=["xlsx", "xls"])
data = load_data(uploaded_file)

# Si pas de données, créer un dataframe vide avec exemple
if data.empty:
    data = pd.DataFrame({
        'ID': [1, 2, 3],
        'Nom': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'Département': ['Ventes', 'IT', 'Marketing'],
        'Salaire': [50000, 75000, 60000]
    })

# Sidebar pour les filtres
with st.sidebar:
    st.header("🔍 Filtres")
    
    # Filtres dynamiques pour chaque colonne
    filters = {}
    for col in data.columns:
        if data[col].dtype == 'object':
            options = st.multiselect(
                f"Filtrer {col}",
                options=data[col].unique(),
                default=data[col].unique(),
                key=f"filter_{col}"
            )
            filters[col] = options
        else:
            min_val = float(data[col].min())
            max_val = float(data[col].max())
            values = st.slider(
                f"Plage pour {col}",
                min_val, max_val, (min_val, max_val),
                key=f"range_{col}"
            )
            filters[col] = values

# Application des filtres
filtered_data = data.copy()
for col, condition in filters.items():
    if isinstance(condition, list):  # Filtre catégoriel
        filtered_data = filtered_data[filtered_data[col].isin(condition)]
    else:  # Filtre numérique
        filtered_data = filtered_data[
            (filtered_data[col] >= condition[0]) & 
            (filtered_data[col] <= condition[1])
        ]

# Section d'édition des données
st.header("✏️ Édition des Données")

# Édition avec st.data_editor
edited_data = st.data_editor(
    filtered_data,
    num_rows="dynamic",  # Permet d'ajouter/supprimer des lignes
    column_config={
        "Age": st.column_config.NumberColumn("Age", min_value=0, max_value=120),
        "Salaire": st.column_config.NumberColumn("Salaire", format="$%.2f")
    },
    hide_index=True,
    key="data_editor",
    use_container_width=True
)

# Boutons d'action
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔁 Appliquer les modifications", use_container_width=True):
        data = edited_data
        st.success("Données mises à jour!")
with col2:
    if st.button("➕ Ajouter une ligne vide", use_container_width=True):
        new_row = {col: "" for col in data.columns}
        data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
        st.rerun()
with col3:
    if st.button("🗑️ Supprimer les lignes sélectionnées", use_container_width=True):
        selected_rows = st.session_state.get("data_editor", {}).get("selected_rows", [])
        if selected_rows:
            data = data.drop(selected_rows).reset_index(drop=True)
            st.success(f"{len(selected_rows)} lignes supprimées!")
            st.rerun()
        else:
            st.warning("Aucune ligne sélectionnée")

# Section des statistiques
st.header("📈 Statistiques Descriptives")

if not filtered_data.empty:
    # Statistiques de base
    st.subheader("Résumé Statistique")
    st.dataframe(filtered_data.describe(), use_container_width=True)
    
    # Statistiques par colonne
    selected_col = st.selectbox(
        "Analyser une colonne spécifique",
        options=filtered_data.select_dtypes(include=np.number).columns
    )
    
    if selected_col:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Moyenne", f"{filtered_data[selected_col].mean():.2f}")
        with col2:
            st.metric("Médiane", f"{filtered_data[selected_col].median():.2f}")
        with col3:
            st.metric("Écart-type", f"{filtered_data[selected_col].std():.2f}")
        with col4:
            st.metric("Plage", f"{filtered_data[selected_col].min():.2f} - {filtered_data[selected_col].max():.2f}")

# Export Excel
st.header("💾 Export des Données")

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Données')
    processed_data = output.getvalue()
    return processed_data

if not data.empty:
    excel_data = to_excel(data)
    st.download_button(
        label="📤 Télécharger en Excel",
        data=excel_data,
        file_name="donnees_modifiees.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
