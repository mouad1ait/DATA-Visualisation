import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

def main():
    st.title("📊 Visualisation Avancée de Données Excel")
    
    # Chargement du fichier
    uploaded_file = st.file_uploader("Charger un fichier Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            
            # Vérification des colonnes
            required_columns = ['modèle', 'SN', 'refPays', 'filiale', 
                              'installationDate', 'Lastconnexion', 'incident', 'incidentDate']
            
            if not all(col in df.columns for col in required_columns):
                st.error("Les colonnes dans le fichier Excel ne correspondent pas aux attentes.")
                return
            
            # Préparation des données
            df = prepare_data(df)
            
            # Sidebar avec filtres
            st.sidebar.header("Filtres")
            model_filter = st.sidebar.selectbox("Modèle", ['Tous'] + sorted(df['modèle'].unique().tolist()))
            filiale_filter = st.sidebar.selectbox("Filiale", ['Tous'] + sorted(df['filiale'].unique().tolist()))
            year_filter = st.sidebar.selectbox("Année", ['Tous'] + sorted(df['année'].unique().astype(str).tolist()))
            
            # Application des filtres
            filtered_df = apply_filters(df, model_filter, filiale_filter, year_filter)
            
            # Affichage des données
            st.header("Données Filtrees")
            st.dataframe(filtered_df)
            
            # Visualisations
            st.header("Visualisations")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Répartition par Modèle")
                fig1 = plot_pie(filtered_df, 'modèle')
                st.pyplot(fig1)
                
            with col2:
                st.subheader("Répartition par Filiale")
                fig2 = plot_pie(filtered_df, 'filiale')
                st.pyplot(fig2)
            
            st.subheader("Distribution des Jours entre Incident et Installation")
            fig3 = plot_histogram(filtered_df, 'différence jours')
            st.pyplot(fig3)
            
            st.subheader("Nombre d'Incidents par Année")
            fig4 = plot_countplot(filtered_df, 'année')
            st.pyplot(fig4)
            
            # Export des données
            if st.button("Exporter les Données"):
                export_data(filtered_df)
                
        except Exception as e:
            st.error(f"Erreur lors du traitement du fichier: {str(e)}")

def prepare_data(df):
    # Conversion des dates
    df['installationDate'] = pd.to_datetime(df['installationDate'])
    df['incidentDate'] = pd.to_datetime(df['incidentDate'])
    df['Lastconnexion'] = pd.to_datetime(df['Lastconnexion'])
    
    # Calcul des différences
    df['différence jours'] = (df['incidentDate'] - df['installationDate']).dt.days
    
    # Extraction de l'année
    df['année'] = df['no de série'].str[2:4].astype(int) + 2000
    
    # Calcul de l'âge
    current_year = datetime.now().year
    df['âge appareil (ans)'] = current_year - df['année']
    
    return df

def apply_filters(df, model, filiale, year):
    filtered = df.copy()
    if model != 'Tous':
        filtered = filtered[filtered['modèle'] == model]
    if filiale != 'Tous':
        filtered = filtered[filtered['filiale'] == filiale]
    if year != 'Tous':
        filtered = filtered[filtered['année'] == int(year)]
    return filtered

def plot_pie(df, column):
    counts = df[column].value_counts()
    fig, ax = plt.subplots()
    counts.plot.pie(autopct='%1.1f%%', ax=ax)
    return fig

def plot_histogram(df, column):
    fig, ax = plt.subplots()
    sns.histplot(df[column], bins=20, kde=True, ax=ax)
    return fig

def plot_countplot(df, column):
    fig, ax = plt.subplots()
    sns.countplot(data=df, x=column, ax=ax)
    plt.xticks(rotation=45)
    return fig

def export_data(df):
    # Création d'un fichier Excel en mémoire
    output = pd.ExcelWriter('donnees_filtrees.xlsx', engine='openpyxl')
    df.to_excel(output, index=False)
    output.close()
    
    # Téléchargement du fichier
    with open('donnees_filtrees.xlsx', 'rb') as f:
        st.download_button(
            label="Télécharger les données filtrées",
            data=f,
            file_name='donnees_filtrees.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    os.remove('donnees_filtrees.xlsx')

if __name__ == "__main__":
    main()
