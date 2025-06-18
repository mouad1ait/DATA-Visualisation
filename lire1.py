import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Outil de prétraitement", layout="wide")
st.title("📊 Outil de prétraitement des données")

# Fonction pour convertir les dates
def convert_date_format(date_str):
    """Convertit une date de format 'aaaa-mm-jj hh:mm:ss.ms' vers 'jj/mm/aaaa'"""
    try:
        dt = datetime.strptime(str(date_str), '%Y-%m-%d %H:%M:%S.%f')
        return dt.strftime('%d/%m/%Y')
    except ValueError:
        try:
            dt = datetime.strptime(str(date_str), '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d/%m/%Y')
        except ValueError:
            return np.nan

# Fonction de validation des numéros de série
def valider_numero_serie(num_serie):
    """Valide un numéro de série selon les règles spécifiées"""
    num_str = str(num_serie).strip()
    
    # Nettoyage des caractères spéciaux
    special_chars = {
        '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5',
        '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁰': '0'
    }
    cleaned_str = ''.join([special_chars.get(c, c) for c in num_str])
    
    # Validation
    if len(cleaned_str) != 7 or not cleaned_str.isdigit():
        return "Invalide (longueur)"
    
    chiffres = [int(c) for c in cleaned_str]
    deux_premiers = chiffres[0]*10 + chiffres[1]
    trois_quatre = chiffres[2]*10 + chiffres[3]
    
    if deux_premiers > 12:
        return "Invalide (2 premiers > 12)"
    if trois_quatre < 17 or trois_quatre > 26:
        return "Invalide (chiffres 3-4 hors 17-26)"
    
    return "Valide"

# Section 1: Upload du fichier
with st.expander("1. Chargement des données", expanded=True):
    uploaded_file = st.file_uploader("Téléversez votre fichier (CSV ou Excel)", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"Fichier {uploaded_file.name} chargé avec succès!")
        st.dataframe(df.head())

# Traitement si fichier chargé
if 'df' in locals():
    # Section 2: Conversion des dates
    with st.expander("2. Conversion des dates"):
        # Détection automatique des colonnes de date
        date_columns = [col for col in df.columns 
                       if df[col].astype(str).str.contains(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}').any()]
        
        if date_columns:
            selected_dates = st.multiselect("Sélectionnez les colonnes à convertir", 
                                          date_columns, default=date_columns)
            
            if st.button("Convertir les dates"):
                for col in selected_dates:
                    df[col] = df[col].apply(convert_date_format)
                st.success("Conversion terminée!")
                st.dataframe(df[selected_dates].head())
        else:
            st.info("Aucune colonne de date détectée")

    # Section 3: Validation des numéros de série
    with st.expander("3. Validation des numéros de série"):
        if 'numéro de série' in df.columns:
            df['Validation S/N'] = df['no de série'].apply(valider_numero_serie)
            st.write("Répartition des statuts:")
            st.bar_chart(df['Validation S/N'].value_counts())
            
            invalid = df[df['Validation S/N'] != "Valide"]
            if not invalid.empty:
                st.write(f"{len(invalid)} numéros invalides trouvés")
                st.dataframe(invalid[['no de série', 'Validation S/N']].head())
        else:
            st.warning("Colonne 'no de série' introuvable")

    # Section 4: Gestion des doublons
    with st.expander("4. Suppression des doublons"):
        if all(col in df.columns for col in ['modèle', 'no de série']):
            dup_count = df.duplicated(subset=['modèle', 'no de série']).sum()
            st.write(f"Nombre de doublons trouvés : {dup_count}")
            
            if st.button("Supprimer les doublons"):
                df = df.sort_values('no de série').drop_duplicates(
                    subset=['modèle', 'no de série'], keep='first')
                st.success(f"{dup_count} doublons supprimés")
                st.dataframe(df.head())
        else:
            st.warning("Colonnes 'modèle' et/ou 'no de série' manquantes")

    # Section 5: Export des données
    with st.expander("5. Exporter les données traitées"):
        # Conversion finale avant export
        def prepare_export(df):
            """Convertit toutes les dates avant export"""
            date_cols = [col for col in df.columns 
                        if df[col].astype(str).str.contains(r'\d{4}-\d{2}-\d{2}').any()]
            for col in date_cols:
                df[col] = df[col].apply(convert_date_format)
            return df
        
        export_format = st.radio("Format d'export", ['Excel', 'CSV'])
        filename = st.text_input("Nom du fichier", "donnees_pretraitees")
        
        if st.button("Générer le fichier d'export"):
            df_export = prepare_export(df.copy())
            output = BytesIO()
            
            if export_format == 'Excel':
                filename += '.xlsx'
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_export.to_excel(writer, index=False)
                mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                filename += '.csv'
                output.write(df_export.to_csv(index=False).encode('utf-8'))
                mime = 'text/csv'
            
            st.download_button(
                "Télécharger le fichier",
                output.getvalue(),
                filename,
                mime=mime
            )
            st.success("Fichier prêt au téléchargement!")

# Instructions
with st.expander("ℹ️ Instructions"):
    st.markdown("""
    1. Téléversez votre fichier Excel ou CSV
    2. Convertissez les colonnes de date si nécessaire
    3. Validez les numéros de série
    4. Supprimez les doublons
    5. Exportez les données traitées
    """)
