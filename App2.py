import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration de la page
st.set_page_config(
    page_title="Analyse de Fichiers Excel",
    page_icon="📊",
    layout="wide"
)

# Style personnalisé avec bleu et blanc
st.markdown(
    """
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #1e88e5;
        color: white;
        border-radius: 5px;
        border: none;
    }
    .stSelectbox, .stDateInput, .stFileUploader {
        background-color: white;
        border-radius: 5px;
    }
    .sidebar .sidebar-content {
        background-color: #1e88e5;
        color: white;
    }
    h1, h2, h3 {
        color: #1e88e5;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Titre de l'application
st.title("📊 Analyse de Fichiers Excel")
st.markdown("""
Cette application vous permet d'importer des fichiers Excel et d'obtenir des statistiques descriptives 
pour les données numériques et catégorielles.
""")

# Sidebar pour le téléchargement du fichier
with st.sidebar:
    st.header("Paramètres")
    uploaded_file = st.file_uploader("Téléchargez votre fichier Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            # Lire toutes les feuilles du fichier Excel
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            selected_sheet = st.selectbox("Sélectionnez une feuille", sheet_names)
            
            # Charger les données
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            
            # Afficher les informations de base
            st.success("Fichier chargé avec succès!")
            st.write(f"Lignes: {df.shape[0]}, Colonnes: {df.shape[1]}")
            
            # Options de filtrage
            st.subheader("Options de Filtrage")
            
            # Filtre par date si des colonnes de date existent
            date_columns = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
            if date_columns:
                selected_date_col = st.selectbox("Colonne de date pour le filtrage", date_columns)
                
                min_date = df[selected_date_col].min()
                max_date = df[selected_date_col].max()
                
                date_range = st.date_input(
                    "Sélectionnez une plage de dates",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    df = df[(df[selected_date_col] >= pd.to_datetime(start_date)) & 
                           (df[selected_date_col] <= pd.to_datetime(end_date))]
            
            # Filtre pour d'autres colonnes
            other_columns = [col for col in df.columns if col not in date_columns]
            for col in other_columns:
                unique_vals = df[col].unique()
                if len(unique_vals) <= 20:  # Seulement pour les colonnes avec peu de valeurs uniques
                    selected_vals = st.multiselect(
                        f"Filtrer {col}",
                        options=unique_vals,
                        default=unique_vals
                    )
                    df = df[df[col].isin(selected_vals)]
                    
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier: {e}")

# Corps principal de l'application
if uploaded_file is not None:
    # Aperçu des données
    st.subheader("Aperçu des Données")
    st.dataframe(df.head())
    
    # Statistiques descriptives
    st.subheader("Statistiques Descriptives")
    
    # Sélection des colonnes à analyser
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if numeric_cols:
        st.markdown("### Statistiques Numériques")
        stats_df = df[numeric_cols].describe().T
        stats_df = stats_df[['count', 'mean', 'min', '25%', '50%', '75%', 'max']]
        stats_df.columns = ['Count', 'Moyenne', 'Min', '25%', 'Médiane', '75%', 'Max']
        st.dataframe(stats_df.style.background_gradient(cmap='Blues'))
        
        # Visualisation des distributions
        st.markdown("### Distributions des Variables Numériques")
        selected_num_col = st.selectbox("Sélectionnez une colonne numérique", numeric_cols)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.histplot(df[selected_num_col], kde=True, color='#1e88e5', ax=ax)
        ax.set_title(f"Distribution de {selected_num_col}")
        st.pyplot(fig)
    
    if categorical_cols:
        st.markdown("### Statistiques Catégorielles")
        selected_cat_col = st.selectbox("Sélectionnez une colonne catégorielle", categorical_cols)
        
        value_counts = df[selected_cat_col].value_counts().reset_index()
        value_counts.columns = ['Valeur', 'Occurrence']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(value_counts.style.background_gradient(cmap='Blues'))
        
        with col2:
            st.markdown(f"**Valeur la plus fréquente:** {value_counts.iloc[0, 0]}")
            st.markdown(f"**Occurrence:** {value_counts.iloc[0, 1]}")
            
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.barplot(
                data=value_counts.head(10), 
                x='Occurrence', 
                y='Valeur', 
                palette='Blues_r',
                ax=ax
            )
            ax.set_title(f"Top 10 des valeurs pour {selected_cat_col}")
            st.pyplot(fig)
    
    # Téléchargement des résultats
    st.subheader("Exporter les Résultats")
    
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')
    
    csv = convert_df_to_csv(df)
    st.download_button(
        label="Télécharger les données filtrées (CSV)",
        data=csv,
        file_name='donnees_filtrees.csv',
        mime='text/csv'
    )
    
else:
    st.info("Veuillez télécharger un fichier Excel pour commencer l'analyse.")
