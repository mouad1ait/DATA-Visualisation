import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Traitement des données produits", layout="wide")

def main():
    st.title("Traitement des données produits")
    st.markdown("""
    **Workflow en 2 étapes :**  
    1. Fusion des données  
    2. Conversion des dates
    """)

    # Initialisation des variables de session
    if 'merged_data' not in st.session_state:
        st.session_state.merged_data = None
    if 'converted_data' not in st.session_state:
        st.session_state.converted_data = None

    # Chargement des fichiers
    uploaded_file = st.file_uploader("Téléverser le fichier Excel", type=["xlsx", "xls"])
    
    if uploaded_file:
        try:
            # Lecture des noms de feuilles disponibles
            xl = pd.ExcelFile(uploaded_file)
            sheet_names = xl.sheet_names
            
            # Sélection des feuilles
            col1, col2, col3 = st.columns(3)
            with col1:
                inst_sheet = st.selectbox("Feuille des Installations", sheet_names)
            with col2:
                inc_sheet = st.selectbox("Feuille des Incidents", sheet_names)
            with col3:
                rma_sheet = st.selectbox("Feuille des RMA", sheet_names)

            # Chargement des données
            df_inst = pd.read_excel(uploaded_file, sheet_name=inst_sheet)
            df_inc = pd.read_excel(uploaded_file, sheet_name=inc_sheet) 
            df_rma = pd.read_excel(uploaded_file, sheet_name=rma_sheet)

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
                    try:
                        # Fusion progressive
                        merged = pd.merge(df_inst, df_inc, on='no_serie', how='left', suffixes=('', '_incident'))
                        merged = pd.merge(merged, df_rma, on='no_serie', how='left', suffixes=('', '_rma'))
                        
                        # Suppression des colonnes en double
                        merged = merged.loc[:, ~merged.columns.duplicated()]
                        
                        st.session_state.merged_data = merged
                        st.success("Fusion terminée avec succès!")
                        st.dataframe(merged.head(3))
                    except Exception as e:
                        st.error(f"Erreur lors de la fusion : {str(e)}")

            # Affichage des données fusionnées si disponible
            if st.session_state.merged_data is not None:
                with st.expander("Voir toutes les données fusionnées", expanded=False):
                    st.dataframe(st.session_state.merged_data)

                # Étape 2: Bouton de conversion des dates
                st.subheader("Étape 2: Conversion des dates")
                if st.button("📅 Convertir les dates en jj/mm/aaaa", help="Convertit toutes les colonnes de date"):
                    with st.spinner("Conversion des dates..."):
                        try:
                            converted = st.session_state.merged_data.copy()
                            date_cols = [col for col in converted.columns if 'date' in col.lower()]
                            
                            for col in date_cols:
                                converted[col] = pd.to_datetime(converted[col], errors='coerce')
                                converted[col] = converted[col].dt.strftime('%d/%m/%Y')
                            
                            st.session_state.converted_data = converted
                            st.success("Conversion des dates terminée!")
                            
                            # Afficher uniquement les colonnes de dates
                            st.dataframe(converted[date_cols].head(3))
                        except Exception as e:
                            st.error(f"Erreur lors de la conversion : {str(e)}")

                # Affichage des données converties si disponible
                if st.session_state.converted_data is not None:
                    with st.expander("Voir toutes les données converties", expanded=False):
                        st.dataframe(st.session_state.converted_data)

                    # Bouton d'export
                    st.subheader("Export des résultats")
                    if st.button("💾 Exporter les données traitées"):
                        with st.spinner("Préparation de l'export..."):
                            try:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"donnees_traitees_{timestamp}.xlsx"
                                
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                    st.session_state.converted_data.to_excel(writer, index=False)
                                
                                st.download_button(
                                    label="⬇️ Télécharger le fichier Excel",
                                    data=output.getvalue(),
                                    file_name=filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            except Exception as e:
                                st.error(f"Erreur lors de l'export : {str(e)}")

        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {str(e)}")

if __name__ == "__main__":
    main()
