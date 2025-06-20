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
        
        # Conversion des dates si nécessaire
        date_cols = ['date d\'installation', 'dernière connexion', 'date incident', 'date de fabrication']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Calcul des ages si les colonnes existent
        if all(col in df.columns for col in ['date incident', 'date de fabrication', 'date d\'installation']):
            df['age dès fabrication'] = (df['date incident'] - df['date de fabrication']).dt.days
            df['age dès installation'] = (df['date incident'] - df['date d\'installation']).dt.days
            df['durée entre fabrication et installation'] = (df['date d\'installation'] - df['date de fabrication']).dt.days
        
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
        
        # Statistiques descriptives améliorées
        st.subheader("Statistiques descriptives")
        safe_describe(df)
        
        # Sélection des colonnes à analyser
        st.sidebar.header("Options d'analyse")
        
        # Filtres conditionnels
        if 'modèle' in df.columns:
            model_filter = st.sidebar.multiselect(
                "Filtrer par modèle",
                options=df['modèle'].unique(),
                default=df['modèle'].unique()
            )
            df = df[df['modèle'].isin(model_filter)]
        
        if 'filiale' in df.columns:
            country_filter = st.sidebar.multiselect(
                "Filtrer par pays",
                options=df['filiale'].unique(),
                default=df['filiale'].unique()
            )
            df = df[df['filiale'].isin(country_filter)]
        
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
                    st.write("### Répartition par pays")
                    country_counts = df['filiale'].value_counts().head(10)
                    fig, ax = plt.subplots()
                    sns.barplot(x=country_counts.values, y=country_counts.index, ax=ax)
                    st.pyplot(fig)
            
            if 'référence pays' in df.columns:
                st.write("### Distribution des références pays")
                fig, ax = plt.subplots()
                sns.histplot(df['référence pays'], bins=20, kde=True, ax=ax)
                st.pyplot(fig)
        
        with tab2:
            st.subheader("Analyse du Time to Failure")
            
            if 'TTF_V2' in df.columns:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### Distribution du TTF")
                    fig, ax = plt.subplots()
                    sns.histplot(df['TTF_V2'], bins=20, kde=True, ax=ax)
                    st.pyplot(fig)
                
                with col2:
                    if 'modèle' in df.columns:
                        st.write("### TTF par modèle")
                        fig, ax = plt.subplots()
                        sns.boxplot(x='modèle', y='TTF_V2', data=df, ax=ax)
                        plt.xticks(rotation=45)
                        st.pyplot(fig)
            
            if 'Age dès installation' in df.columns:
                st.write("### Âge depuis l'installation lors de l'incident")
                fig, ax = plt.subplots()
                sns.histplot(df['Age dès installation'], bins=20, kde=True, ax=ax)
                st.pyplot(fig)
        
        with tab3:
            st.subheader("Analyse par pays")
            
            if 'filiale' in df.columns:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### Incidents par pays")
                    incident_by_country = df['filiale'].value_counts().head(15)
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(x=incident_by_country.values, y=incident_by_country.index, ax=ax)
                    st.pyplot(fig)
                
                with col2:
                    if 'modèle' in df.columns:
                        st.write("### Modèles les plus défaillants par pays")
                        top_models_by_country = df.groupby(['filiale', 'modèle']).size().reset_index(name='counts')
                        top_models_by_country = top_models_by_country.sort_values('counts', ascending=False).head(15)
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.barplot(x='counts', y='filiale', hue='modèle', data=top_models_by_country, ax=ax)
                        st.pyplot(fig)
        
        with tab4:
            st.subheader("Analyse temporelle")
            
            if 'date incident' in df.columns:
                df['année incident'] = df['Date incident v2'].dt.year
                df['mois incident'] = df['Date incident v2'].dt.to_period('M').astype(str)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### Incidents par année")
                    incidents_by_year = df['année incident'].value_counts().sort_index()
                    fig, ax = plt.subplots()
                    sns.lineplot(x=incidents_by_year.index, y=incidents_by_year.values, ax=ax)
                    st.pyplot(fig)
                
                with col2:
                    st.write("### Incidents par mois")
                    incidents_by_month = df['mois incident'].value_counts().sort_index().head(24)
                    fig, ax = plt.subplots(figsize=(12, 6))
                    sns.lineplot(x=incidents_by_month.index, y=incidents_by_month.values, ax=ax)
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
            
            if 'entre fabrication et installation ' in df.columns:
                st.write("### Durée entre fabrication et installation")
                fig, ax = plt.subplots()
                sns.histplot(df['entre fabrication et installation '], bins=20, kde=True, ax=ax)
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
