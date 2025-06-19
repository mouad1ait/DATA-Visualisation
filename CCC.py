import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Analyse des Incidents Produits", layout="wide")
st.title("📊 Analyse des Incidents Produits")

# Fonction pour charger les données
@st.cache_data
def load_data(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, sheet_name='Feuil8')
        
        # Standardisation des noms de colonnes
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Conversion des dates si nécessaire
        date_cols = ['date_d\'installation', 'dernière_connexion', 'date_incident_v2', 'date_de_fabrication']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {e}")
        return None

# Fonction améliorée pour les statistiques descriptives
def safe_describe(df):
    try:
        # Colonnes numériques standard
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0:
            st.write("### Statistiques numériques")
            st.dataframe(df[num_cols].describe())
        
        # Colonnes datetime
        date_cols = df.select_dtypes(include=['datetime']).columns
        if len(date_cols) > 0:
            st.write("### Statistiques des dates")
            date_stats = df[date_cols].agg(['min', 'max', 'count'])
            st.dataframe(date_stats)
        
        # Colonnes catégorielles
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) > 0:
            st.write("### Statistiques catégorielles")
            st.dataframe(df[cat_cols].describe(include='all'))
    except Exception as e:
        st.warning(f"Impossible d'afficher toutes les statistiques: {str(e)}")

# Upload du fichier
uploaded_file = st.file_uploader("Téléchargez votre fichier Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    if df is not None:
        # Aperçu des données
        st.subheader("Aperçu des données")
        st.dataframe(df.head())
        
        # Filtres dans la sidebar
        st.sidebar.header("Filtres")
        
        # Filtre par modèle
        if 'modèle' in df.columns:
            modeles = df['modèle'].unique()
            selected_modeles = st.sidebar.multiselect(
                "Filtrer par modèle",
                options=modeles,
                default=modeles
            )
            df = df[df['modèle'].isin(selected_modeles)]
        
        # Filtre par filiale
        if 'filiale' in df.columns:
            filiales = df['filiale'].unique()
            selected_filiales = st.sidebar.multiselect(
                "Filtrer par filiale",
                options=filiales,
                default=filiales
            )
            df = df[df['filiale'].isin(selected_filiales)]
        
        # Statistiques descriptives
        st.subheader("Statistiques descriptives")
        safe_describe(df)
        
        # Onglets pour différentes analyses
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Distribution", 
            "🔄 Time to Failure", 
            "🌍 Par Pays", 
            "📅 Analyse Temporelle", 
            "🔍 Détails"
        ])
        
        with tab1:
            st.subheader("Distribution des données")
            
            col1, col2 = st.columns(2)
            with col1:
                if 'modèle' in df.columns:
                    st.write("### Répartition par modèle")
                    model_counts = df['modèle'].value_counts()
                    fig, ax = plt.subplots()
                    ax.pie(model_counts, labels=model_counts.index, autopct='%1.1f%%')
                    st.pyplot(fig)
            
            with col2:
                if 'filiale' in df.columns:
                    st.write("### Répartition par filiale")
                    filiale_counts = df['filiale'].value_counts().head(10)
                    fig, ax = plt.subplots()
                    sns.barplot(x=filiale_counts.values, y=filiale_counts.index, ax=ax)
                    st.pyplot(fig)
            
            if 'référence_pays' in df.columns:
                st.write("### Distribution des références pays")
                fig, ax = plt.subplots()
                sns.histplot(df['référence_pays'], bins=20, kde=True, ax=ax)
                st.pyplot(fig)
        
        with tab2:
            st.subheader("Analyse du Time to Failure")
            
            if 'ttf_v2' in df.columns:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### Distribution du TTF")
                    fig, ax = plt.subplots()
                    sns.histplot(df['ttf_v2'], bins=20, kde=True, ax=ax)
                    st.pyplot(fig)
                
                with col2:
                    if 'modèle' in df.columns:
                        st.write("### TTF par modèle")
                        fig, ax = plt.subplots()
                        sns.boxplot(x='modèle', y='ttf_v2', data=df, ax=ax)
                        plt.xticks(rotation=45)
                        st.pyplot(fig)
            
            if 'age_dès_installation' in df.columns:
                st.write("### Âge depuis l'installation lors de l'incident")
                fig, ax = plt.subplots()
                sns.histplot(df['age_dès_installation'], bins=20, kde=True, ax=ax)
                st.pyplot(fig)
        
        with tab3:
            st.subheader("Analyse par filiale")
            
            if 'filiale' in df.columns:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### Incidents par filiale")
                    incident_by_filiale = df['filiale'].value_counts().head(15)
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(x=incident_by_filiale.values, y=incident_by_filiale.index, ax=ax)
                    st.pyplot(fig)
                
                with col2:
                    if 'modèle' in df.columns:
                        st.write("### Modèles les plus défaillants par filiale")
                        top_models_by_filiale = df.groupby(['filiale', 'modèle']).size().reset_index(name='counts')
                        top_models_by_filiale = top_models_by_filiale.sort_values('counts', ascending=False).head(15)
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.barplot(x='counts', y='filiale', hue='modèle', data=top_models_by_filiale, ax=ax)
                        st.pyplot(fig)
        
        with tab4:
            st.subheader("Analyse temporelle")
            
            if 'date_incident_v2' in df.columns:
                df['année_incident'] = df['date_incident_v2'].dt.year
                df['mois_incident'] = df['date_incident_v2'].dt.to_period('M').astype(str)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### Incidents par année")
                    incidents_by_year = df['année_incident'].value_counts().sort_index()
                    fig, ax = plt.subplots()
                    sns.lineplot(x=incidents_by_year.index, y=incidents_by_year.values, ax=ax)
                    st.pyplot(fig)
                
                with col2:
                    st.write("### Incidents par mois")
                    incidents_by_month = df['mois_incident'].value_counts().sort_index().head(24)
                    fig, ax = plt.subplots(figsize=(12, 6))
                    sns.lineplot(x=incidents_by_month.index, y=incidents_by_month.values, ax=ax)
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
            
            if 'entre_fabrication_et_installation' in df.columns:
                st.write("### Durée entre fabrication et installation")
                fig, ax = plt.subplots()
                sns.histplot(df['entre_fabrication_et_installation'], bins=20, kde=True, ax=ax)
                st.pyplot(fig)
        
        with tab5:
            st.subheader("Détails des incidents")
            
            if 'incident' in df.columns:
                st.write("### Top 20 des incidents les plus fréquents")
                top_incidents = df['incident'].value_counts().head(20)
                st.dataframe(top_incidents)
                
                if 'modèle' in df.columns:
                    selected_incident = st.selectbox(
                        "Sélectionnez un incident pour voir les modèles concernés",
                        options=top_incidents.index
                    )
                    
                    if selected_incident:
                        st.write(f"### Modèles pour l'incident {selected_incident}")
                        models_for_incident = df[df['incident'] == selected_incident]['modèle'].value_counts()
                        fig, ax = plt.subplots()
                        sns.barplot(x=models_for_incident.values, y=models_for_incident.index, ax=ax)
                        st.pyplot(fig)
    else:
        st.warning("Le fichier n'a pas pu être chargé correctement. Veuillez vérifier le format.")
else:
    st.info("Veuillez télécharger un fichier Excel pour commencer l'analyse.")
