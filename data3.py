import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pycountry
from datetime import datetime
import plotly.express as px

# Configuration de la page
st.set_page_config(
    page_title="Analyse des Appareils",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonctions utilitaires
def validate_sn(sn):
    try:
        if pd.isna(sn) or len(str(sn)) < 4:
            return False
        mm = int(str(sn)[:2])
        aa = int(str(sn)[2:4])
        return (17 <= aa <= 30) and (1 <= mm <= 12)
    except:
        return False

def get_country_name(code):
    try:
        return pycountry.countries.get(numeric=str(int(code))).name
    except:
        return f"Inconnu ({code})"

# Prétraitement des données
def preprocess_data(df):
    # Vérification des colonnes nécessaires
    required_columns = ['modèle', 'SN', 'référence de pays', 
                       'installationDate', 'date de désinstallation', 
                       'dernière connexion']
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"Colonnes manquantes dans le fichier: {', '.join(missing_cols)}")
        return None
    
    try:
        # Conversion des dates
        date_cols = ['installationDate', 'date de désinstallation', 'dernière connexion']
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Extraction info SN
        df['SN_mois'] = df['SN'].astype(str).str[:2].astype(int)
        df['SN_année'] = 2000 + df['SN'].astype(str).str[2:4].astype(int)
        df['SN_valide'] = df['SN'].apply(validate_sn)
        
        # Calcul durée de vie
        df['durée_vie'] = (df['date de désinstallation'] - df['installationDate']).dt.days
        df['jours_sans_connexion'] = (pd.to_datetime('today') - df['dernière connexion']).dt.days
        
        # Nettoyage modèle
        df['modèle_clean'] = df['modèle'].astype(str).str.lower().str.strip()
        
        # Nom du pays
        df['pays_nom'] = df['référence de pays'].apply(get_country_name)
        
        return df
    
    except Exception as e:
        st.error(f"Erreur lors du prétraitement: {str(e)}")
        return None

# Interface principale
def main():
    st.title("📊 Analyse des Données d'Appareils")
    
    # Sidebar - Upload et filtres
    with st.sidebar:
        st.header("Importation des Données")
        uploaded_file = st.file_uploader("Choisir un fichier Excel", type=['xlsx', 'csv'])
    
    if uploaded_file:
        try:
            # Lecture des données
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Afficher un aperçu des données brutes
            with st.expander("Aperçu des données brutes"):
                st.dataframe(df.head())
                st.write(f"Colonnes disponibles: {list(df.columns)}")
            
            # Prétraitement
            df_processed = preprocess_data(df)
            
            if df_processed is None:
                return
            
            # Sidebar filters
            with st.sidebar:
                st.header("Filtres")
                
                # Date range filter
                min_date = pd.to_datetime(df_processed['installationDate'].min()).date()
                max_date = pd.to_datetime(df_processed['installationDate'].max()).date()
                
                date_range = st.date_input(
                    "Période d'installation",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                # Model filter
                available_models = df_processed['modèle_clean'].unique()
                selected_models = st.multiselect(
                    "Modèles à inclure",
                    options=available_models,
                    default=available_models
                )
                
                # SN validity filter
                sn_validity = st.radio(
                    "Validité SN",
                    options=["Tous", "Valides seulement", "Invalides seulement"]
                )
            
            # Apply filters
            if len(date_range) == 2:
                start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
                df_filtered = df_processed[
                    (df_processed['installationDate'] >= start_date) & 
                    (df_processed['installationDate'] <= end_date)
                ]
            else:
                df_filtered = df_processed.copy()
            
            if selected_models:
                df_filtered = df_filtered[df_filtered['modèle_clean'].isin(selected_models)]
            
            if sn_validity == "Valides seulement":
                df_filtered = df_filtered[df_filtered['SN_valide']]
            elif sn_validity == "Invalides seulement":
                df_filtered = df_filtered[~df_filtered['SN_valide']]
            
            # Section Statistiques
            st.header("📈 Statistiques Globales")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Appareils totaux", len(df_filtered))
            col2.metric("Modèles uniques", df_filtered['modèle_clean'].nunique())
            col3.metric("Pays couverts", df_filtered['pays_nom'].nunique())
            validity_rate = df_filtered['SN_valide'].mean() * 100
            col4.metric("SN valides", f"{validity_rate:.1f}%")
            
            # Section Visualisations
            st.header("📊 Visualisations")
            
            tab1, tab2, tab3 = st.tabs(["Distribution", "Temporel", "Géographique"])
            
            with tab1:
                st.plotly_chart(
                    px.pie(df_filtered, names='modèle_clean', title='Répartition des modèles'),
                    use_container_width=True
                )
                
                st.plotly_chart(
                    px.bar(df_filtered['SN_valide'].value_counts().reset_index(), 
                          x='index', y='SN_valide', 
                          labels={'index': 'SN Valide', 'SN_valide': 'Count'},
                          title='Validité des Numéros de Série'),
                    use_container_width=True
                )
            
            with tab2:
                df_filtered['année_mois_installation'] = df_filtered['installationDate'].dt.to_period('M').astype(str)
                monthly = df_filtered.groupby('année_mois_installation').size().reset_index(name='count')
                
                st.plotly_chart(
                    px.line(monthly, x='année_mois_installation', y='count', 
                          title='Installations par Mois'),
                    use_container_width=True
                )
                
                st.plotly_chart(
                    px.box(df_filtered, x='modèle_clean', y='durée_vie', 
                         title='Durée de Vie par Modèle'),
                    use_container_width=True
                )
            
            with tab3:
                country_counts = df_filtered['pays_nom'].value_counts().reset_index()
                country_counts.columns = ['Pays', 'Nombre d\'appareils']
                
                st.plotly_chart(
                    px.choropleth(country_counts,
                                locations='Pays',
                                locationmode='country names',
                                color='Nombre d\'appareils',
                                title='Répartition Géographique des Appareils'),
                    use_container_width=True
                )
            
            # Section Données
            st.header("🔍 Données Traitées")
            st.dataframe(df_filtered)
            
            # Téléchargement
            st.download_button(
                label="Télécharger les données traitées",
                data=df_filtered.to_csv(index=False).encode('utf-8'),
                file_name='donnees_traitees.csv',
                mime='text/csv'
            )
            
        except Exception as e:
            st.error(f"Une erreur est survenue: {str(e)}")
            st.error("Veuillez vérifier que votre fichier contient les colonnes attendues.")
    else:
        st.info("Veuillez uploader un fichier Excel ou CSV pour commencer l'analyse")

if __name__ == "__main__":
    main()
