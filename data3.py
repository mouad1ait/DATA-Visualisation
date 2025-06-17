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
        mm = int(sn[:2])
        aa = int(sn[2:4])
        return (17 <= aa <= 30) and (1 <= mm <= 12)
    except:
        return False

def get_country_name(code):
    try:
        return pycountry.countries.get(numeric=str(code).name
    except:
        return f"Inconnu ({code})"

# Prétraitement des données
def preprocess_data(df):
    # Conversion des dates
    date_cols = ['installationDate', 'date de désinstallation', 'dernière connexion']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Extraction info SN
    df['SN_mois'] = df['SN'].str[:2].astype(int)
    df['SN_année'] = 2000 + df['SN'].str[2:4].astype(int)
    df['SN_valide'] = df['SN'].apply(validate_sn)
    
    # Calcul durée de vie
    df['durée_vie'] = (df['date de désinstallation'] - df['installationDate']).dt.days
    df['jours_sans_connexion'] = (pd.to_datetime('today') - df['dernière connexion']).dt.days
    
    # Nettoyage modèle
    df['modèle_clean'] = df['modèle'].str.lower().str.strip()
    
    # Nom du pays
    df['pays_nom'] = df['référence de pays'].apply(get_country_name)
    
    return df

# Visualisations
def plot_model_distribution(df):
    fig = px.pie(df, names='modèle_clean', title='Répartition des modèles')
    st.plotly_chart(fig, use_container_width=True)

def plot_sn_validity(df):
    fig = px.bar(df['SN_valide'].value_counts().reset_index(), 
                 x='index', y='SN_valide', 
                 labels={'index': 'SN Valide', 'SN_valide': 'Count'},
                 title='Validité des Numéros de Série')
    st.plotly_chart(fig, use_container_width=True)

def plot_installations_over_time(df):
    df['année_mois_installation'] = df['installationDate'].dt.to_period('M').astype(str)
    monthly = df.groupby('année_mois_installation').size().reset_index(name='count')
    
    fig = px.line(monthly, x='année_mois_installation', y='count', 
                  title='Installations par Mois')
    fig.update_xaxes(title='Mois')
    fig.update_yaxes(title='Nombre d\'installations')
    st.plotly_chart(fig, use_container_width=True)

def plot_lifespan_by_model(df):
    fig = px.box(df, x='modèle_clean', y='durée_vie', 
                 title='Durée de Vie par Modèle')
    fig.update_xaxes(title='Modèle')
    fig.update_yaxes(title='Durée de vie (jours)')
    st.plotly_chart(fig, use_container_width=True)

def plot_geographic_distribution(df):
    country_counts = df['pays_nom'].value_counts().reset_index()
    country_counts.columns = ['Pays', 'Nombre d\'appareils']
    
    fig = px.choropleth(country_counts,
                        locations='Pays',
                        locationmode='country names',
                        color='Nombre d\'appareils',
                        title='Répartition Géographique des Appareils')
    st.plotly_chart(fig, use_container_width=True)

def plot_inactivity_analysis(df):
    bins = [0, 30, 90, 180, 365, float('inf')]
    labels = ['<1 mois', '1-3 mois', '3-6 mois', '6-12 mois', '>1 an']
    df['inactivité_catégorie'] = pd.cut(df['jours_sans_connexion'], bins=bins, labels=labels)
    
    fig = px.bar(df['inactivité_catégorie'].value_counts().reset_index(),
                 x='index', y='inactivité_catégorie',
                 labels={'index': 'Période d\'inactivité', 'inactivité_catégorie': 'Nombre d\'appareils'},
                 title='Analyse de l\'Inactivité des Appareils')
    st.plotly_chart(fig, use_container_width=True)

# Interface principale
def main():
    st.title("📊 Analyse des Données d'Appareils")
    
    # Sidebar - Upload et filtres
    with st.sidebar:
        st.header("Importation des Données")
        uploaded_file = st.file_uploader("Choisir un fichier Excel", type=['xlsx', 'csv'])
        
        if uploaded_file:
            st.success("Fichier chargé avec succès!")
            
            st.header("Filtres")
            min_date = st.date_input("Date d'installation min", 
                                     value=datetime(2017, 1, 1))
            max_date = st.date_input("Date d'installation max", 
                                    value=datetime.today())
            
            selected_models = st.multiselect(
                "Modèles à inclure",
                options=[],
                default=[]
            )
            
            sn_validity = st.radio("Validité SN", 
                                  options=["Tous", "Valides seulement", "Invalides seulement"])
    
    # Contenu principal
    if uploaded_file:
        try:
            # Lecture des données
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Prétraitement
            df = preprocess_data(df)
            
            # Mise à jour des filtres dynamiques
            if 'selected_models' in locals():
                selected_models = st.sidebar.multiselect(
                    "Modèles à inclure",
                    options=df['modèle_clean'].unique(),
                    default=df['modèle_clean'].unique()
                )
            
            # Application des filtres
            df_filtered = df[
                (df['installationDate'].dt.date >= min_date) & 
                (df['installationDate'].dt.date <= max_date)
            ]
            
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
            
            tab1, tab2, tab3, tab4 = st.tabs(["Distribution", "Temporel", "Géographique", "Analyse"])
            
            with tab1:
                plot_model_distribution(df_filtered)
                plot_sn_validity(df_filtered)
            
            with tab2:
                plot_installations_over_time(df_filtered)
                plot_lifespan_by_model(df_filtered)
            
            with tab3:
                plot_geographic_distribution(df_filtered)
            
            with tab4:
                plot_inactivity_analysis(df_filtered)
            
            # Section Données
            st.header("🔍 Données Brutes")
            
            with st.expander("Afficher les données filtrées"):
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
    else:
        st.info("Veuillez uploader un fichier Excel ou CSV pour commencer l'analyse")

if __name__ == "__main__":
    main()
