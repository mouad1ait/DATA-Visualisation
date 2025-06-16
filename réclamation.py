import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Analyse des Réclamations", page_icon="📊", layout="wide")

# Titre de l'application
st.title("📊 Analyse des Données de Réclamation")

# Téléchargement du fichier Excel
uploaded_file = st.file_uploader("Téléchargez votre fichier Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Lecture du fichier Excel
        df = pd.read_excel(uploaded_file)
        
        # Afficher les premières lignes
        st.subheader("Aperçu des Données")
        st.write(df.head())
        
        # Vérification des colonnes de date
        date_cols = ['Date de fabrication', 'Date d\'installation', 'Date de réclamation', 'Date d\'analyse']
        date_cols_present = [col for col in date_cols if col in df.columns]
        
        if not date_cols_present:
            st.error("Aucune colonne de date trouvée dans le fichier.")
        else:
            # Conversion des colonnes de date en format datetime
            for col in date_cols_present:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Calcul du TTF
            if 'Date de réclamation' in df.columns:
                if 'Date d\'installation' in df.columns:
                    df['TTF'] = (df['Date de réclamation'] - df['Date d\'installation']).dt.days
                elif 'Date de fabrication' in df.columns:
                    df['TTF'] = (df['Date de réclamation'] - df['Date de fabrication']).dt.days
                else:
                    st.warning("Impossible de calculer le TTF - colonnes de date manquantes")
            
            # Traitement du numéro de série
            if 'Numéro de série' in df.columns:
                # Extraction des informations du numéro de série
                try:
                    df['Mois'] = df['Numéro de série'].str[:2]
                    df['Année'] = df['Numéro de série'].str[2:4]
                    df['Numéro'] = df['Numéro de série'].str[4:]
                except:
                    st.warning("Format du numéro de série non conforme à mmaaxxx")
                
                # Calcul du MTTF en excluant les numéros de série en double
                if 'TTF' in df.columns:
                    # Identifier les numéros de série uniques
                    unique_serials = df['Numéro de série'].value_counts()
                    unique_serials = unique_serials[unique_serials == 1].index
                    
                    # Calculer MTTF seulement pour les numéros de série uniques
                    mttf = df[df['Numéro de série'].isin(unique_serials)]['TTF'].mean()
                    st.metric("MTTF (jours)", round(mttf, 2))
            
            # Affichage des données transformées
            st.subheader("Données Transformées")
            st.write(df)
            
            # Téléchargement des données transformées
            output = pd.ExcelWriter('donnees_transformees.xlsx', engine='xlsxwriter')
            df.to_excel(output, index=False)
            output.close()
            
            with open('donnees_transformees.xlsx', 'rb') as f:
                st.download_button(
                    label="Télécharger les données transformées",
                    data=f,
                    file_name='donnees_transformees.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            
            # Visualisations
            st.subheader("Visualisations des Données")
            
            # Sélection des colonnes pour les visualisations
            col1, col2 = st.columns(2)
            
            with col1:
                # Histogramme du TTF
                if 'TTF' in df.columns:
                    fig, ax = plt.subplots()
                    sns.histplot(df['TTF'].dropna(), bins=20, kde=True, ax=ax)
                    ax.set_title("Distribution du TTF (jours)")
                    st.pyplot(fig)
                
                # Courbe des réclamations dans le temps
                if 'Date de réclamation' in df.columns:
                    fig, ax = plt.subplots()
                    df['Date de réclamation'].value_counts().sort_index().plot(ax=ax)
                    ax.set_title("Nombre de réclamations par date")
                    ax.set_ylabel("Nombre de réclamations")
                    st.pyplot(fig)
            
            with col2:
                # Répartition par produit
                if 'Produit' in df.columns:
                    fig, ax = plt.subplots()
                    df['Produit'].value_counts().plot(kind='bar', ax=ax)
                    ax.set_title("Répartition par Produit")
                    ax.set_ylabel("Nombre de réclamations")
                    st.pyplot(fig)
                
                # Répartition des pannes
                if 'Panne' in df.columns:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    df['Panne'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax)
                    ax.set_title("Répartition des Types de Panne")
                    ax.set_ylabel("")
                    st.pyplot(fig)
            
            # Analyse par catégorie si disponible
            if 'Catégorie' in df.columns:
                st.subheader("Analyse par Catégorie")
                
                # Sélection de la catégorie
                selected_category = st.selectbox("Sélectionnez une catégorie", df['Catégorie'].unique())
                
                category_df = df[df['Catégorie'] == selected_category]
                
                # Afficher les statistiques pour la catégorie sélectionnée
                if 'TTF' in category_df.columns:
                    st.write(f"MTTF pour la catégorie {selected_category}: {category_df['TTF'].mean():.2f} jours")
                
                # Visualisation des pannes dans cette catégorie
                fig, ax = plt.subplots()
                category_df['Panne'].value_counts().plot(kind='bar', ax=ax)
                ax.set_title(f"Répartition des Pannes pour {selected_category}")
                st.pyplot(fig)
    
    except Exception as e:
        st.error(f"Une erreur s'est produite lors du traitement du fichier: {str(e)}")
else:
    st.info("Veuillez télécharger un fichier Excel pour commencer l'analyse.")
