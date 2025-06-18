import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Traitement des données produits", layout="wide")

def main():
    st.title("Traitement des données produits")
    st.markdown("""
    **Workflow complet avec sélection des colonnes**  
    1. Chargement des données  
    2. Mapping des colonnes  
    3. Fusion des données  
    4. Conversion des dates  
    5. Export des résultats
    """)

    # Initialisation des variables de session
    if 'merged_data' not in st.session_state:
        st.session_state.merged_data = None
    if 'converted_data' not in st.session_state:
        st.session_state.converted_data = None
    if 'column_mapping' not in st.session_state:
        st.session_state.column_mapping = {}

    # Étape 1: Chargement des fichiers
    st.header("Étape 1: Chargement des données")
    uploaded_file = st.file_uploader("Téléverser le fichier Excel", type=["xlsx", "xls"])
    
    if uploaded_file:
        try:
            # Lecture des noms de feuilles disponibles
            xl = pd.ExcelFile(uploaded_file)
            sheet_names = xl.sheet_names
            
            # Sélection des feuilles
            col1, col2, col3 = st.columns(3)
            with col1:
                inst_sheet = st.selectbox("Feuille des Installations", sheet_names, key='inst_sheet')
            with col2:
                inc_sheet = st.selectbox("Feuille des Incidents", sheet_names, key='inc_sheet')
            with col3:
                rma_sheet = st.selectbox("Feuille des RMA", sheet_names, key='rma_sheet')

            # Chargement des données
            df_inst = pd.read_excel(uploaded_file, sheet_name=inst_sheet)
            df_inc = pd.read_excel(uploaded_file, sheet_name=inc_sheet)
            df_rma = pd.read_excel(uploaded_file, sheet_name=rma_sheet)

            # Stockage des dataframes bruts
            st.session_state.df_inst = df_inst
            st.session_state.df_inc = df_inc
            st.session_state.df_rma = df_rma

            # Affichage des aperçus
            with st.expander("Aperçu des données brutes", expanded=False):
                tab1, tab2, tab3 = st.tabs(["Installations", "Incidents", "RMA"])
                with tab1:
                    st.dataframe(df_inst.head(3))
                with tab2:
                    st.dataframe(df_inc.head(3))
                with tab3:
                    st.dataframe(df_rma.head(3))

            # Étape 2: Mapping des colonnes
            st.header("Étape 2: Mapping des colonnes")
            
            # Fonction pour créer les sélecteurs de colonnes
            def create_column_selectors(df, prefix):
                cols = st.columns(4)
                mapping = {}
                with cols[0]:
                    mapping['serie'] = st.selectbox("Colonne Série", df.columns, key=f'{prefix}_serie')
                with cols[1]:
                    mapping['modele'] = st.selectbox("Colonne Modèle", df.columns, key=f'{prefix}_modele')
                with cols[2]:
                    mapping['date'] = st.selectbox("Colonne Date", df.columns, key=f'{prefix}_date')
                with cols[3]:
                    mapping['pays'] = st.selectbox("Colonne Pays", df.columns, key=f'{prefix}_pays')
                return mapping

            # Mapping pour chaque type de données
            st.subheader("Installations")
            inst_mapping = create_column_selectors(df_inst, 'inst')
            
            st.subheader("Incidents")
            inc_mapping = create_column_selectors(df_inc, 'inc')
            with st.expander("Colonnes supplémentaires incidents"):
                incident_col = st.selectbox("Colonne Incident", df_inc.columns, key='inc_incident')
                inc_mapping['incident'] = incident_col
            
            st.subheader("Retours RMA")
            rma_mapping = create_column_selectors(df_rma, 'rma')
            with st.expander("Colonnes supplémentaires RMA"):
                rma_col = st.selectbox("Colonne RMA", df_rma.columns, key='rma_num')
                rma_mapping['rma'] = rma_col

            # Sauvegarde du mapping
            st.session_state.column_mapping = {
                'inst': inst_mapping,
                'inc': inc_mapping,
                'rma': rma_mapping
            }

            # Étape 3: Fusion des données
            st.header("Étape 3: Fusion des données")
            if st.button("🔀 Fusionner les données", key='merge_btn'):
                with st.spinner("Fusion en cours..."):
                    try:
                        # Renommage des colonnes selon le mapping
                        df_inst_renamed = st.session_state.df_inst.rename(columns={
                            st.session_state.column_mapping['inst']['serie']: 'no_serie',
                            st.session_state.column_mapping['inst']['modele']: 'modele',
                            st.session_state.column_mapping['inst']['date']: 'date_installation',
                            st.session_state.column_mapping['inst']['pays']: 'pays'
                        })
                        
                        df_inc_renamed = st.session_state.df_inc.rename(columns={
                            st.session_state.column_mapping['inc']['serie']: 'no_serie',
                            st.session_state.column_mapping['inc']['modele']: 'modele',
                            st.session_state.column_mapping['inc']['date']: 'date_incident',
                            st.session_state.column_mapping['inc']['pays']: 'pays',
                            st.session_state.column_mapping['inc']['incident']: 'incident'
                        })
                        
                        df_rma_renamed = st.session_state.df_rma.rename(columns={
                            st.session_state.column_mapping['rma']['serie']: 'no_serie',
                            st.session_state.column_mapping['rma']['modele']: 'modele',
                            st.session_state.column_mapping['rma']['date']: 'date_rma',
                            st.session_state.column_mapping['rma']['pays']: 'pays',
                            st.session_state.column_mapping['rma']['rma']: 'rma'
                        })

                        # Fusion des données
                        merged = pd.merge(df_inst_renamed, df_inc_renamed, on='no_serie', how='left', suffixes=('', '_incident'))
                        merged = pd.merge(merged, df_rma_renamed, on='no_serie', how='left', suffixes=('', '_rma'))
                        
                        # Suppression des colonnes en double
                        merged = merged.loc[:, ~merged.columns.duplicated()]
                        
                        st.session_state.merged_data = merged
                        st.success("Fusion terminée avec succès!")
                        st.dataframe(merged.head(3))
                    except Exception as e:
                        st.error(f"Erreur lors de la fusion : {str(e)}")

            # Affichage des données fusionnées
            if st.session_state.merged_data is not None:
                with st.expander("Voir toutes les données fusionnées", expanded=False):
                    st.dataframe(st.session_state.merged_data)

                # Étape 4: Conversion des dates
                st.header("Étape 4: Conversion des dates")
                if st.button("📅 Convertir les dates en jj/mm/aaaa", key='convert_btn'):
                    with st.spinner("Conversion en cours..."):
                        try:
                            converted = st.session_state.merged_data.copy()
                            date_cols = [col for col in converted.columns if 'date' in col.lower()]
                            
                            for col in date_cols:
                                converted[col] = pd.to_datetime(converted[col], errors='coerce')
                                converted[col] = converted[col].dt.strftime('%d/%m/%Y')
                            
                            st.session_state.converted_data = converted
                            st.success("Conversion des dates terminée!")
                            st.dataframe(converted[date_cols].head(3))
                        except Exception as e:
                            st.error(f"Erreur lors de la conversion : {str(e)}")

                # Affichage des données converties
                if st.session_state.converted_data is not None:
                    with st.expander("Voir toutes les données converties", expanded=False):
                        st.dataframe(st.session_state.converted_data)

                    # Étape 5: Export des résultats
                    st.header("Étape 5: Export des résultats")
                    if st.button("💾 Exporter les données traitées", key='export_btn'):
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
