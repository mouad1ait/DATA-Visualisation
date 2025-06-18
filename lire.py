import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np

st.title("Analyse de fichiers Excel")

# Fonction pour charger le fichier Excel
@st.cache_data
def load_excel(file):
    xls = pd.ExcelFile(file)
    sheets = xls.sheet_names
    dfs = {sheet: xls.parse(sheet) for sheet in sheets}
    return dfs, sheets

# Upload du fichier
uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    # Charger les données
    dfs, sheets = load_excel(uploaded_file)
    
    # Sélection de la feuille
    selected_sheet = st.selectbox("Sélectionnez une feuille", sheets)
    df = dfs[selected_sheet].copy()
    
    st.success(f"Feuille '{selected_sheet}' chargée avec succès!")
    
    # Afficher les premières lignes
    st.subheader("Aperçu des données")
    st.write(df.head())
    
    # Sélection des colonnes à afficher
    st.subheader("Sélection des colonnes")
    all_columns = df.columns.tolist()
    selected_columns = st.multiselect(
        "Choisissez les colonnes à afficher", 
        all_columns, 
        default=all_columns
    )
    
    if selected_columns:
        st.write(df[selected_columns])
    
    # Calcul des valeurs nulles
    st.subheader("Valeurs nulles par colonne")
    null_counts = df.isnull().sum()
    st.write(null_counts)
    
    # Conversion de format de date
    st.subheader("Conversion de format de date")
    date_columns = [col for col in df.columns if df[col].dtype == 'object' and 
                   df[col].str.contains(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}').any()]
    
    if date_columns:
        selected_date_col = st.selectbox(
            "Sélectionnez la colonne à convertir (format AAAA-MM-JJ HH:MM:SS)",
            date_columns
        )
        
        if st.button("Convertir en JJ/MM/AAAA"):
            try:
                df[selected_date_col] = pd.to_datetime(df[selected_date_col]).dt.strftime('%d/%m/%Y')
                st.success(f"Colonne '{selected_date_col}' convertie avec succès!")
                st.write(df[[selected_date_col]].head())
            except Exception as e:
                st.error(f"Erreur lors de la conversion: {e}")
    else:
        st.info("Aucune colonne au format date détectée.")
    
    # Ajout de colonnes de calcul
    st.subheader("Ajouter des colonnes de calcul")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_col_name = st.text_input("Nom de la nouvelle colonne")
    
    with col2:
        operation = st.selectbox(
            "Opération", 
            ["Sélectionner", "Somme", "Moyenne", "Différence", "Produit", "Ratio"]
        )
    
    if operation != "Sélectionner":
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(num_cols) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                first_col = st.selectbox("Première colonne", num_cols)
            
            with col2:
                second_col = st.selectbox("Deuxième colonne", num_cols, index=1 if len(num_cols) > 1 else 0)
            
            if st.button("Ajouter la colonne"):
                if new_col_name:
                    try:
                        if operation == "Somme":
                            df[new_col_name] = df[first_col] + df[second_col]
                        elif operation == "Moyenne":
                            df[new_col_name] = (df[first_col] + df[second_col]) / 2
                        elif operation == "Différence":
                            df[new_col_name] = df[first_col] - df[second_col]
                        elif operation == "Produit":
                            df[new_col_name] = df[first_col] * df[second_col]
                        elif operation == "Ratio":
                            df[new_col_name] = df[first_col] / df[second_col]
                        
                        st.success(f"Colonne '{new_col_name}' ajoutée avec succès!")
                        st.write(df[[first_col, second_col, new_col_name]].head())
                    except Exception as e:
                        st.error(f"Erreur lors du calcul: {e}")
                else:
                    st.warning("Veuillez entrer un nom pour la nouvelle colonne.")
        else:
            st.warning("Pas assez de colonnes numériques pour effectuer des calculs.")
    
    # Télécharger le fichier modifié
    st.subheader("Télécharger les modifications")
    if st.button("Préparer le fichier pour téléchargement"):
        output = pd.ExcelWriter('fichier_modifie.xlsx', engine='xlsxwriter')
        for sheet in sheets:
            if sheet == selected_sheet:
                df.to_excel(output, sheet_name=sheet, index=False)
            else:
                dfs[sheet].to_excel(output, sheet_name=sheet, index=False)
        output.close()
        
        with open('fichier_modifie.xlsx', 'rb') as f:
            st.download_button(
                label="Télécharger le fichier Excel modifié",
                data=f,
                file_name='fichier_modifie.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
else:
    st.info("Veuillez charger un fichier Excel pour commencer.")
