import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Prétraitement des données", layout="wide")

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

# Fonction de validation des numéros de série améliorée
def valider_numero_serie(num_serie):
    """Valide un numéro de série selon les règles spécifiées"""
    num_str = str(num_serie).strip()
    
    # Dictionnaire de caractères spéciaux
    special_chars = {
        '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5',
        '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁰': '0',
        '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5',
        '₆': '6', '₇': '7', '₈': '8', '₉': '9', '₀': '0'
    }
    
    # Nettoyage de la chaîne
    cleaned_str = ''.join([special_chars.get(c, c) for c in num_str])
    
    # Règle 1: Longueur exacte de 7 chiffres
    if len(cleaned_str) != 7 or not cleaned_str.isdigit():
        return "Invalide (longueur)"
    
    chiffres = [int(c) for c in cleaned_str]
    
    # Règle 2: 2 premiers chiffres <= 12
    if (chiffres[0]*10 + chiffres[1]) > 12:
        return "Invalide (2 premiers > 12)"
    
    # Règle 3: Chiffres 3-4 entre 17 et 26
    trois_quatre = chiffres[2]*10 + chiffres[3]
    if trois_quatre < 17 or trois_quatre > 26:
        return "Invalide (chiffres 3-4 hors 17-26)"
    
    return "Valide"

# Interface Streamlit
st.title("📊 Outil de prétraitement des données")

# Section 1: Upload du fichier
with st.expander("1. Chargement des données", expanded=True):
    uploaded_file = st.file_uploader("Téléversez votre fichier (CSV ou Excel)", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file is not None:
        # Chargement des données
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"Fichier {uploaded_file.name} chargé avec succès!")
        
        # Aperçu des données
        st.subheader("Aperçu des données brutes")
        st.dataframe(df.head())

# Traitement des données si fichier chargé
if 'df' in locals():
    # Section 2: Conversion des dates
    with st.expander("2. Conversion des formats de date"):
        # Détection automatique des colonnes de date
        date_columns = []
        for col in df.columns:
            if df[col].astype(str).str.contains(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}').any():
                date_columns.append(col)
        
        if date_columns:
            selected_date_cols = st.multiselect(
                "Colonnes à convertir (format AAAA-MM-JJ HH:MM:SS)",
                date_columns,
                default=date_columns
            )
            
            if st.button("Convertir les dates sélectionnées"):
                for col in selected_date_cols:
                    df[col] = df[col].apply(convert_date_format)
                st.success("Conversion terminée!")
                st.dataframe(df[selected_date_cols].head())
        else:
            st.info("Aucune colonne de date détectée")

    # Section 3: Validation des numéros de série
    with st.expander("3. Validation des numéros de série"):
        if 'no de série' in df.columns:
            # Ajout de la colonne de validation
            df['statut_numero_serie'] = df['no de série'].apply(valider_numero_serie)
            
            # Affichage des résultats
            st.subheader("Répartition des statuts")
            st.bar_chart(df['statut_numero_serie'].value_counts())
            
            # Afficher les invalides
            invalid_mask = df['statut_numero_serie'] != "Valide"
            if invalid_mask.any():
                st.subheader(f"Exemples de numéros invalides ({invalid_mask.sum()} au total)")
                st.dataframe(df[invalid_mask][['no de série', 'statut_numero_serie']].head())
        else:
            st.warning("La colonne 'no de série' n'existe pas dans les données")

    # Section 4: Nettoyage des doublons
    with st.expander("4. Gestion des doublons"):
        if all(col in df.columns for col in ['modèle', 'no de série']):
            # Statistiques avant nettoyage
            duplicates = df.duplicated(subset=['modèle', 'no de série'], keep=False)
            st.write(f"Nombre de lignes avant nettoyage: {len(df)}")
            st.write(f"Nombre de doublons détectés: {duplicates.sum()}")
            
            if st.button("Supprimer les doublons (conserver la première occurrence)"):
                df = df.sort_values(by='no de série', ascending=True)
                df_clean = df.drop_duplicates(subset=['modèle', 'no de série'], keep='first')
                st.success(f"Doublons supprimés! {len(df)-len(df_clean)} lignes enlevées")
                df = df_clean.copy()
                st.dataframe(df.head())
        else:
            st.warning("Les colonnes 'modèle' et 'no de série' sont requises pour cette opération")

    # Section 5: Sauvegarde des résultats
    with st.expander("5. Export des données traitées"):
        # Options d'export
        export_format = st.radio("Format d'export", ['Excel', 'CSV'])
        filename = st.text_input("Nom du fichier", "donnees_pretraitees")
        
        # Bouton d'export
        if st.button("Générer le fichier exporté"):
            output = BytesIO()
            
            if export_format == 'Excel':
                filename += '.xlsx'
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                filename += '.csv'
                output.write(df.to_csv(index=False).encode('utf-8'))
                mime_type = 'text/csv'
            
            st.download_button(
                label="Télécharger le fichier",
                data=output.getvalue(),
                file_name=filename,
                mime=mime_type
            )

# Instructions
with st.expander("Instructions d'utilisation"):
    st.markdown("""
    1. **Téléversez** votre fichier CSV ou Excel
    2. **Convertissez** les formats de date si nécessaire
    3. **Validez** automatiquement les numéros de série
    4. **Supprimez** les doublons (même modèle + même numéro de série)
    5. **Exportez** vos données traitées
    
    **Règles de validation des numéros de série**:
    - 7 chiffres exactement
    - 2 premiers chiffres ≤ 12
    - Chiffres 3 et 4 entre 17 et 26
    """)
