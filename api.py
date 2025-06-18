import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Analyse Produits", layout="wide", page_icon="📊")

def main():
    st.title("📊 Analyse des Données Produits")
    st.markdown("""
    **Workflow complet :**  
    1. Chargement des données  
    2. Conversion des dates  
    3. Statistiques par feuille  
    4. Fusion des données  
    5. Export des résultats
    """)

    # Initialisation des variables de session
    for key in ['dfs', 'converted_dfs', 'merged_data']:
        if key not in st.session_state:
            st.session_state[key] = None

    # Étape 1: Chargement des fichiers
    st.header("Étape 1: Chargement des données")
    uploaded_file = st.file_uploader("Téléverser le fichier Excel", type=["xlsx", "xls"])

    if uploaded_file:
        try:
            # Lecture des noms de feuilles disponibles
            xl = pd.ExcelFile(uploaded_file)
            sheet_names = xl.sheet_names
            
            # Sélection des feuilles
            cols = st.columns(3)
            with cols[0]:
                inst_sheet = st.selectbox("Feuille Installations", sheet_names, key='inst_sheet')
            with cols[1]:
                inc_sheet = st.selectbox("Feuille Incidents", sheet_names, key='inc_sheet')
            with cols[2]:
                rma_sheet = st.selectbox("Feuille RMA", sheet_names, key='rma_sheet')

            # Chargement des données
            dfs = {
                'installations': pd.read_excel(uploaded_file, sheet_name=inst_sheet),
                'incidents': pd.read_excel(uploaded_file, sheet_name=inc_sheet),
                'rma': pd.read_excel(uploaded_file, sheet_name=rma_sheet)
            }
            st.session_state.dfs = dfs

            # Affichage des aperçus
            with st.expander("Aperçu des données brutes", expanded=False):
                tabs = st.tabs(["Installations", "Incidents", "RMA"])
                for (name, df), tab in zip(dfs.items(), tabs):
                    with tab:
                        st.dataframe(df.head(3))

            # Étape 2: Conversion des dates (avant fusion)
            st.header("Étape 2: Conversion des dates")
            if st.button("🕒 Convertir toutes les dates en jj/mm/aaaa"):
                with st.spinner("Conversion en cours..."):
                    try:
                        converted_dfs = {}
                        date_columns = ['date_installation', 'derniere_connexion', 'date_incident', 'date_rma']
                        
                        for name, df in dfs.items():
                            df_converted = df.copy()
                            for col in df_converted.columns:
                                if any(date_col in col.lower() for date_col in date_columns):
                                    df_converted[col] = pd.to_datetime(df_converted[col], errors='coerce')
                                    df_converted[col] = df_converted[col].dt.strftime('%d/%m/%Y')
                            converted_dfs[name] = df_converted
                        
                        st.session_state.converted_dfs = converted_dfs
                        st.success("Conversion terminée avec succès!")
                        
                        # Afficher un exemple de dates converties
                        with st.expander("Voir un exemple de dates converties", expanded=False):
                            st.dataframe(converted_dfs['installations'].filter(like='date').head(3))
                    except Exception as e:
                        st.error(f"Erreur lors de la conversion : {str(e)}")

            # Étape 3: Statistiques par feuille
            if st.session_state.converted_dfs:
                st.header("Étape 3: Statistiques par feuille")
                
                # Sélection de la feuille à analyser
                selected_sheet = st.selectbox(
                    "Choisir une feuille pour les statistiques",
                    list(st.session_state.converted_dfs.keys())
                )
                
                df_stats = st.session_state.converted_dfs[selected_sheet]
                
                # Statistiques de base
                st.subheader(f"Statistiques pour {selected_sheet}")
                cols = st.columns(4)
                with cols[0]:
                    st.metric("Nombre d'entrées", len(df_stats))
                with cols[1]:
                    st.metric("Modèles uniques", df_stats['modèle'].nunique())
                with cols[2]:
                    st.metric("Pays uniques", df_stats['filiale'].nunique())
                with cols[3]:
                    if 'date_installation' in df_stats.columns:
                        min_date = df_stats['date_installation'].min()
                        st.metric("Date installation min", min_date)
                
                # Graphiques
                tab1, tab2, tab3 = st.tabs(["Répartition", "Tendances", "Détails"])
                
                with tab1:
                    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
                    df_stats['modèle'].value_counts().plot(kind='bar', ax=ax[0])
                    ax[0].set_title('Répartition par modèle')
                    df_stats['filiale'].value_counts().plot(kind='bar', ax=ax[1])
                    ax[1].set_title('Répartition par pays')
                    st.pyplot(fig)
                
                with tab2:
                    if 'date_installation' in df_stats.columns:
                        df_temp = df_stats.copy()
                        df_temp['date_installation'] = pd.to_datetime(df_temp['date_installation'])
                        df_temp['mois'] = df_temp['date_installation'].dt.to_period('M').astype(str)
                        
                        fig, ax = plt.subplots(figsize=(10, 4))
                        df_temp['mois'].value_counts().sort_index().plot(kind='line', marker='o', ax=ax)
                        ax.set_title('Installations par mois')
                        st.pyplot(fig)
                
                with tab3:
                    st.dataframe(df_stats.describe(include='all', datetime_is_numeric=True))

            # Étape 4: Fusion des données
            if st.session_state.converted_dfs:
                st.header("Étape 4: Fusion des données")
                if st.button("🔀 Fusionner les feuilles"):
                    with st.spinner("Fusion en cours..."):
                        try:
                            dfs = st.session_state.converted_dfs
                            
                            # Fusion avec gestion des colonnes communes
                            merged = pd.merge(
                                dfs['installations'],
                                dfs['incidents'],
                                on=['modèle', 'no_serie', 'référence pays', 'filiale'],
                                how='left',
                                suffixes=('', '_incident')
                            )
                            
                            merged = pd.merge(
                                merged,
                                dfs['rma'],
                                on=['modèle', 'no_serie', 'référence pays', 'filiale'],
                                how='left',
                                suffixes=('', '_rma')
                            )
                            
                            # Suppression des doublons de colonnes
                            merged = merged.loc[:, ~merged.columns.duplicated()]
                            
                            st.session_state.merged_data = merged
                            st.success("Fusion terminée avec succès!")
                            
                            # Afficher les colonnes fusionnées
                            with st.expander("Colonnes fusionnées", expanded=False):
                                st.write(list(merged.columns))
                            
                        except Exception as e:
                            st.error(f"Erreur lors de la fusion : {str(e)}")

            # Étape 5: Export des résultats
            if st.session_state.merged_data is not None:
                st.header("Étape 5: Export des résultats")
                
                # Options d'export
                export_format = st.radio("Format d'export", ["Excel", "CSV"])
                filename = f"donnees_produits_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                if export_format == "Excel":
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        st.session_state.merged_data.to_excel(writer, index=False)
                        # Ajouter les stats dans un onglet séparé
                        for name, df in st.session_state.converted_dfs.items():
                            df.to_excel(writer, sheet_name=f"Stats_{name}", index=False)
                    
                    st.download_button(
                        label="📥 Télécharger Excel",
                        data=output.getvalue(),
                        file_name=f"{filename}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    csv = st.session_state.merged_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f"{filename}.csv",
                        mime="text/csv"
                    )

        except Exception as e:
            st.error(f"Erreur lors du chargement : {str(e)}")

if __name__ == "__main__":
    main()
