import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.api.types import is_datetime64_any_dtype as is_datetime

# Configuration de la page
st.set_page_config(page_title="Analyse des Réclamations", page_uploader="📊", layout="wide")

# Titre de l'application
st.title("📊 Analyse des Données de Réclamation")

# Fonction pour détecter et convertir les dates
def detect_and_convert_dates(df):
    date_cols = []
    date_patterns = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', 
                    '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d',
                    '%d.%m.%Y', '%m.%d.%Y', '%Y.%m.%d']
    
    for col in df.columns:
        # Vérifier si la colonne est déjà au format datetime
        if is_datetime(df[col]):
            date_cols.append(col)
            continue
            
        # Essayer de convertir avec différentes formats de date
        for pattern in date_patterns:
            try:
                converted = pd.to_datetime(df[col], format=pattern, errors='raise')
                df[col] = converted
                date_cols.append(col)
                break
            except:
                continue
                
        # Essayer la conversion automatique si les formats spécifiques échouent
        if col not in date_cols:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                if df[col].notna().any():
                    date_cols.append(col)
            except:
                pass
    
    return df, date_cols

# Téléchargement du fichier Excel
uploaded_file = st.file_uploader("Téléchargez votre fichier Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Lecture du fichier Excel
        df = pd.read_excel(uploaded_file)
        
        # Détection et conversion des dates
        df, date_cols = detect_and_convert_dates(df)
        
        if not date_cols:
            st.warning("Aucune colonne de date n'a été détectée. Vérifiez vos données.")
        else:
            st.success(f"Colonnes de date détectées: {', '.join(date_cols)}")
            
            # Afficher les types de données pour vérification
            st.subheader("Types de données des colonnes")
            st.write(df.dtypes)
            
            # Interface pour mapper les colonnes aux dates spécifiques
            st.subheader("Mapping des colonnes de date")
            
            date_mapping = {
                'Date de fabrication': None,
                'Date d\'installation': None,
                'Date de réclamation': None,
                'Date d\'analyse': None
            }
            
            for date_type in date_mapping.keys():
                date_mapping[date_type] = st.selectbox(
                    f"Sélectionnez la colonne pour {date_type}",
                    options=[''] + date_cols,
                    index=0
                )
            
            # Calcul du TTF selon les colonnes sélectionnées
            if st.button("Calculer le TTF"):
                if date_mapping['Date de réclamation']:
                    claim_date = date_mapping['Date de réclamation']
                    
                    if date_mapping['Date d\'installation']:
                        install_date = date_mapping['Date d\'installation']
                        df['TTF'] = (df[claim_date] - df[install_date]).dt.days
                    elif date_mapping['Date de fabrication']:
                        manuf_date = date_mapping['Date de fabrication']
                        df['TTF'] = (df[claim_date] - df[manuf_date]).dt.days
                    else:
                        st.error("Veuillez sélectionner au moins une date de référence (installation ou fabrication)")
                
                # Afficher les résultats
                st.subheader("Résultats avec TTF calculé")
                st.write(df)
                
                # Téléchargement des résultats
                output = pd.ExcelWriter('resultats_avec_ttf.xlsx', engine='xlsxwriter')
                df.to_excel(output, index=False)
                output.close()
                
                with open('resultats_avec_ttf.xlsx', 'rb') as f:
                    st.download_button(
                        label="Télécharger les résultats",
                        data=f,
                        file_name='resultats_avec_ttf.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
    
    except Exception as e:
        st.error(f"Erreur lors du traitement: {str(e)}")
