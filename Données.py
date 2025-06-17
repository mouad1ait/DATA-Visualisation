import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

def main():
    st.title("📊 Analyse des Appareils Techniques")
    
    # Chargement du fichier
    uploaded_file = st.file_uploader("Charger un fichier Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            # Lecture du fichier
            df = pd.read_excel(uploaded_file)
            
            # Vérification des colonnes
            required_columns = [
                'modèle', 'SN', 'refPays', 'filiale',
                'installationDate', 'Lastconnexion', 'incident', 'incidentDate'
            ]
            
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
            
            # Application des filtres
            filtered_df = apply_filters(df, model_filter, filiale_filter)
            
            # Métriques clés
            st.header("Indicateurs Clés")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Nombre d'appareils", len(filtered_df))
                
            with col2:
                if 'Time_to_Failure' in filtered_df:
                    avg_ttf = round(filtered_df['Time_to_Failure'].mean(), 1)
                    st.metric("Time to Failure moyen (jours)", avg_ttf)
            
            with col3:
                if 'Age_appareil' in filtered_df:
                    avg_age = round(filtered_df['Age_appareil'].mean(), 1)
                    st.metric("Âge moyen (jours)", avg_age)
            
            # Affichage des données
            st.header("Données Complètes")
            st.dataframe(filtered_df, height=300)
            
            # Visualisations
            st.header("Analyses")
            
            # Graphiques en ligne
            col1, col2 = st.columns(2)
            with col1:
                plot_pie_chart(filtered_df, 'modèle', "Répartition par Modèle")
            with col2:
                plot_pie_chart(filtered_df, 'filiale', "Répartition par Filiale")
            
            # Histogrammes
            if 'Time_to_Failure' in filtered_df:
                plot_histogram(filtered_df, 'Time_to_Failure', 
                             "Distribution du Time to Failure", 
                             "Jours avant incident", "Nombre d'appareils")
            
            if 'Age_appareil' in filtered_df:
                plot_histogram(filtered_df, 'Age_appareil', 
                             "Distribution de l'âge des appareils", 
                             "Âge (jours)", "Nombre d'appareils")
            
            # Export des données
            st.header("Export")
            if st.button("Exporter les données analysées"):
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
    
    # Calcul du Time to Failure (date incident - date installation)
    if 'installationDate' in df and 'incidentDate' in df:
        df['Time_to_Failure'] = (df['incidentDate'] - df['installationDate']).dt.days
        st.success(f"Time to Failure calculé pour {len(df)} appareils")
    
    # Calcul de l'âge (aujourd'hui - date installation)
    if 'installationDate' in df:
        df['Age_appareil'] = (datetime.now() - df['installationDate']).dt.days
        st.success(f"Âge des appareils calculé pour {len(df)} appareils")
    
    return df

def apply_filters(df, model, filiale):
    filtered = df.copy()
    
    if model != 'Tous':
        filtered = filtered[filtered['modèle'] == model]
    
    if filiale != 'Tous':
        filtered = filtered[filtered['filiale'] == filiale]
    
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
    output_path = 'analyse_appareils.xlsx'
    
    with pd.ExcelWriter(output_path) as writer:
        # Données complètes
        df.to_excel(writer, sheet_name='Données', index=False)
        
        # Statistiques
        stats_data = {
            'Statistique': ['Nombre total', 'Modèle le plus courant', 'Filiale la plus courante',
                           'Time to Failure moyen (jours)', 'Âge moyen (jours)'],
            'Valeur': [
                len(df),
                df['modèle'].mode()[0] if 'modèle' in df else 'N/A',
                df['filiale'].mode()[0] if 'filiale' in df else 'N/A',
                round(df['Time_to_Failure'].mean(), 1) if 'Time_to_Failure' in df else 'N/A',
                round(df['Age_appareil'].mean(), 1) if 'Age_appareil' in df else 'N/A'
            ]
        }
        pd.DataFrame(stats_data).to_excel(writer, sheet_name='Statistiques', index=False)
    
    # Téléchargement
    with open(output_path, 'rb') as f:
        st.download_button(
            label="Télécharger l'analyse complète",
            data=f,
            file_name='analyse_appareils_techniques.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    # Nettoyage
    os.remove(output_path)

if __name__ == "__main__":
    main()
