import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

def main():
    st.title("📊 Visualisation de Données Techniques")
    
    # Chargement du fichier
    uploaded_file = st.file_uploader("Charger un fichier Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            # Lecture du fichier
            df = pd.read_excel(uploaded_file)
            
            # Vérification des colonnes
            required_columns = {
                'modèle': 'Modèle produit',
                'SN': 'Numéro de série',
                'refPays': 'Référence pays',
                'filiale': 'Filiale',
                'installationDate': 'Date installation',
                'Lastconnexion': 'Dernière connexion',
                'incident': 'Incident',
                'incidentDate': 'Date incident'
            }
            
            # Vérifier les colonnes manquantes
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                st.error(f"Colonnes manquantes: {', '.join(missing_cols)}")
                st.write("Colonnes détectées:", list(df.columns))
                return
            
            # Préparation des données
            df = prepare_data(df)
            
            # Sidebar avec filtres
            st.sidebar.header("Filtres")
            
            # Filtre par modèle
            model_list = ['Tous'] + sorted(df['modèle'].unique().tolist())
            model_filter = st.sidebar.selectbox("Modèle", model_list)
            
            # Filtre par filiale
            filiale_list = ['Tous'] + sorted(df['filiale'].unique().tolist())
            filiale_filter = st.sidebar.selectbox("Filiale", filiale_list)
            
            # Filtre par année (extraite du SN)
            if 'année' in df:
                year_list = ['Tous'] + sorted(df['année'].astype(str).unique().tolist())
                year_filter = st.sidebar.selectbox("Année de production", year_list)
            else:
                year_filter = 'Tous'
            
            # Application des filtres
            filtered_df = apply_filters(df, model_filter, filiale_filter, year_filter)
            
            # Métriques clés
            st.header("Indicateurs Clés")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Appareils", len(filtered_df))
                
            with col2:
                if 'différence jours' in filtered_df:
                    avg_days = round(filtered_df['différence jours'].mean(), 1)
                    st.metric("Jours moyen avant incident", avg_days)
            
            with col3:
                if 'âge appareil (ans)' in filtered_df:
                    avg_age = round(filtered_df['âge appareil (ans)'].mean(), 1)
                    st.metric("Âge moyen (ans)", avg_age)
            
            # Affichage des données
            st.header("Données Filtrees")
            st.dataframe(filtered_df, height=300)
            
            # Visualisations
            st.header("Analyses")
            
            # Graphiques en ligne
            col1, col2 = st.columns(2)
            with col1:
                plot_pie_chart(filtered_df, 'modèle', "Répartition par Modèle")
            with col2:
                plot_pie_chart(filtered_df, 'filiale', "Répartition par Filiale")
            
            # Histogramme
            if 'différence jours' in filtered_df:
                plot_histogram(filtered_df, 'différence jours', 
                             "Distribution des jours avant incident", 
                             "Jours", "Nombre d'appareils")
            
            # Export des données
            st.header("Export")
            if st.button("Exporter les données filtrées"):
                export_data(filtered_df)
                
        except Exception as e:
            st.error(f"Erreur lors du traitement: {str(e)}")

def prepare_data(df):
    # Conversion robuste des dates
    date_columns = {
        'installationDate': 'Date installation',
        'incidentDate': 'Date incident',
        'Lastconnexion': 'Dernière connexion'
    }
    
    for col, label in date_columns.items():
        try:
            # Conversion en datetime avec gestion d'erreur
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
            
            # Vérification des conversions
            if df[col].isnull().any():
                nb_errors = df[col].isnull().sum()
                st.warning(f"{nb_errors} {label} non converties (format invalide)")
        except Exception as e:
            st.error(f"Erreur conversion {label}: {str(e)}")
            raise
    
    # Calcul différence entre incident et installation
    if 'installationDate' in df and 'incidentDate' in df:
        df['différence jours'] = (df['incidentDate'] - df['installationDate']).dt.days
    
    # Extraction année du numéro de série (SN)
    if 'SN' in df:
        try:
            # Format: mmaaxxx (mm=mois, aa=année)
            df['année'] = '20' + df['SN'].astype(str).str[2:4]
            df['année'] = pd.to_numeric(df['année'], errors='coerce')
            
            # Calcul âge appareil
            current_year = datetime.now().year
            df['âge appareil (ans)'] = current_year - df['année']
        except:
            st.warning("Impossible d'extraire l'année du numéro de série")
    
    return df

def apply_filters(df, model, filiale, year):
    filtered = df.copy()
    
    if model != 'Tous':
        filtered = filtered[filtered['modèle'] == model]
    
    if filiale != 'Tous':
        filtered = filtered[filtered['filiale'] == filiale]
    
    if year != 'Tous' and 'année' in filtered:
        filtered = filtered[filtered['année'] == int(year)]
    
    return filtered

def plot_pie_chart(df, column, title):
    if column not in df or df[column].isnull().all():
        st.warning(f"Données manquantes pour {title}")
        return
    
    fig, ax = plt.subplots()
    counts = df[column].value_counts()
    if len(counts) > 10:
        # Regrouper les petites catégories
        threshold = counts.sum() * 0.02  # 2%
        small_categories = counts[counts < threshold]
        if len(small_categories) > 0:
            counts = counts[counts >= threshold]
            counts['Autres'] = small_categories.sum()
    
    counts.plot.pie(autopct='%1.1f%%', ax=ax)
    ax.set_title(title)
    ax.set_ylabel('')
    st.pyplot(fig)

def plot_histogram(df, column, title, xlabel, ylabel):
    fig, ax = plt.subplots()
    sns.histplot(data=df, x=column, bins=20, kde=True, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    st.pyplot(fig)

def export_data(df):
    # Création du fichier Excel
    output_path = 'donnees_filtrees.xlsx'
    
    with pd.ExcelWriter(output_path) as writer:
        # Données complètes
        df.to_excel(writer, sheet_name='Données', index=False)
        
        # Statistiques
        stats = pd.DataFrame({
            'Statistique': ['Nombre total', 'Modèle le plus courant', 'Filiale la plus courante',
                           'Jours moyens avant incident', 'Âge moyen des appareils'],
            'Valeur': [
                len(df),
                df['modèle'].mode()[0] if 'modèle' in df else 'N/A',
                df['filiale'].mode()[0] if 'filiale' in df else 'N/A',
                round(df['différence jours'].mean(), 1) if 'différence jours' in df else 'N/A',
                round(df['âge appareil (ans)'].mean(), 1) if 'âge appareil (ans)' in df else 'N/A'
            ]
        })
        stats.to_excel(writer, sheet_name='Statistiques', index=False)
    
    # Téléchargement
    with open(output_path, 'rb') as f:
        st.download_button(
            label="Télécharger le fichier Excel",
            data=f,
            file_name='donnees_techniques_filtrees.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    # Nettoyage
    os.remove(output_path)

if __name__ == "__main__":
    main()
