import streamlit as st
import pandas as pd
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Traitement des données produits", layout="wide")

# Fonction pour fusionner les données
def merge_data(df_inst, df_inc, df_rma):
    """Étape 1: Fusion des données"""
    try:
        # Fusion progressive avec gestion des colonnes dupliquées
        merged = pd.merge(df_inst, df_inc, on='no_serie', how='left', suffixes=('', '_incident'))
        merged = pd.merge(merged, df_rma, on='no_serie', how='left', suffixes=('', '_rma'))
        
        # Suppression des colonnes en double
        merged = merged.loc[:, ~merged.columns.duplicated()]
        
        st.session_state['merged_data'] = merged
        st.success("Fusion terminée avec succès!")
        return merged
    except Exception as e:
        st.error(f"Erreur lors de la fusion : {str(e)}")
        return None

# Fonction pour convertir les dates
def convert_dates(df):
    """Étape 2: Conversion des dates au format jj/mm/aaaa"""
    try:
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        
        for col in date_cols:
            # Conversion en datetime puis formatage
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df[col] = df[col].dt.strftime('%d/%m/%Y')
        
        st.session_state['converted_data'] = df
        st.success("Conversion des dates terminée!")
        return df
    except Exception as e:
        st.error(f"Erreur lors de la conversion : {str(e)}")
        return None

# Interface utilisateur
def main():
    st.title("Traitement des données produits")
    st.markdown("""
    **Workflow en 2 étapes :**  
    1. Fusion des données  
    2. Conversion des dates
    """)

    # Chargement des fichiers
    uploaded_file = st.file_uploader("Téléverser le fichier Excel", type=["xlsx", "xls"])
    
    if uploaded_file:
        # Chargement des feuilles
        df_inst = pd.read_excel(uploaded_file, sheet_name='installations')
        df_inc = pd.read_excel(uploaded_file, sheet_name='incidents') 
        df_rma = pd.read_excel(uploaded_file, sheet_name='RMA')

        # Affichage des aperçus
        with st.expander("Aperçu des données brutes", expanded=False):
            tab1, tab2, tab3 = st.tabs(["Installations", "Incidents", "RMA"])
            with tab1:
                st.dataframe(df_inst.head(3))
            with tab2:
                st.dataframe(df_inc.head(3))
            with tab3:
                st.dataframe(df_rma.head(3))

        # Étape 1: Bouton de fusion
        st.subheader("Étape 1: Fusion des données")
        if st.button("🔀 Fusionner les feuilles", help="Combine installations, incidents et RMA"):
            with st.spinner("Fusion en cours..."):
                merged = merge_data(df_inst, df_inc, df_rma)
                if merged is not None:
                    st.dataframe(merged.head(3))

        # Affichage des données fusionnées si disponible
        if 'merged_data' in st.session_state:
            with st.expander("Voir toutes les données fusionnées", expanded=False):
                st.dataframe(st.session_state['merged_data'])

        # Étape 2: Bouton de conversion des dates
        st.subheader("Étape 2: Conversion des dates")
        if st.button("📅 Convertir les dates en jj/mm/aaaa", 
                    disabled='merged_data' not in st.session_state,
                    help="Nécessite d'avoir fusionné les données d'abord"):
            
            with st.spinner("Conversion des dates..."):
                converted = convert_dates(st.session_state['merged_data'])
                if converted is not None:
                    # Afficher uniquement les colonnes de dates
                    date_cols = [col for col in converted.columns if 'date' in col.lower()]
                    st.dataframe(converted[date_cols].head(3))

        # Affichage des données converties si disponible
        if 'converted_data' in st.session_state:
            with st.expander("Voir toutes les données converties", expanded=False):
                st.dataframe(st.session_state['converted_data'])

            # Bouton d'export
            st.subheader("Export des résultats")
            if st.button("💾 Exporter les données traitées"):
                with st.spinner("Préparation de l'export..."):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"donnees_traitees_{timestamp}.xlsx"
                    
                    # Création du fichier Excel
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        st.session_state['converted_data'].to_excel(writer, index=False)
                    
                    # Téléchargement
                    st.download_button(
                        label="⬇️ Télécharger le fichier Excel",
                        data=output.getvalue(),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

if __name__ == "__main__":
    main()
