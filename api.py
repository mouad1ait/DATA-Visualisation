import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages

# Configuration de la page
st.set_page_config(
    page_title="Analyse Produits - Sélection Personnalisée",
    page_icon="🛠️",
    layout="wide"
)

# Fonctions de traitement
def validate_serial(serial, format_rules):
    """Validation du numéro de série selon les règles définies"""
    if pd.isna(serial):
        return False
    # Implémentez ici votre logique de validation
    return True

def extract_manufacture_date(serial, date_rules):
    """Extraction de la date de fabrication selon les règles"""
    try:
        # Exemple: les 4 premiers chiffres représentent l'année et la semaine
        year_part = int(str(serial)[:2]) + 2000
        week_part = int(str(serial)[2:4])
        return datetime.strptime(f"{week_part} {year_part}", "%U %Y").strftime('%d/%m/%Y')
    except:
        return None

def process_data(df_inst, df_inc, df_rma, col_mapping):
    """Traitement principal des données"""
    # Fusion
    merged = pd.merge(
        df_inst, 
        df_inc, 
        left_on=[col_mapping['inst']['serie']], 
        right_on=[col_mapping['inc']['serie']],
        how='left'
    )
    merged = pd.merge(
        merged,
        df_rma,
        left_on=[col_mapping['inst']['serie']],
        right_on=[col_mapping['rma']['serie']],
        how='left'
    )
    
    # Conversion dates
    for df_type in ['inst', 'inc', 'rma']:
        if 'date' in col_mapping[df_type]:
            merged[col_mapping[df_type]['date']] = pd.to_datetime(
                merged[col_mapping[df_type]['date']], 
                errors='coerce'
            )
    
    # Calculs
    if 'inst' in col_mapping and 'date' in col_mapping['inst'] and 'inc' in col_mapping and 'date' in col_mapping['inc']:
        merged['ttf'] = (
            merged[col_mapping['inc']['date']] - 
            merged[col_mapping['inst']['date']]
        ).dt.days
    
    return merged

# Interface Streamlit
def main():
    st.title("🛠️ Analyse Produits - Sélection Personnalisée")
    
    # Étape 1: Upload du fichier
    with st.expander("ÉTAPE 1: Chargement du fichier Excel", expanded=True):
        uploaded_file = st.file_uploader("Déposez votre fichier Excel ici", type=["xlsx", "xls"])
        
        if uploaded_file:
            try:
                xls = pd.ExcelFile(uploaded_file)
                sheet_names = xls.sheet_names
                
                # Sélection des feuilles
                col1, col2, col3 = st.columns(3)
                with col1:
                    inst_sheet = st.selectbox("Feuille des Installations", sheet_names)
                with col2:
                    inc_sheet = st.selectbox("Feuille des Incidents", sheet_names)
                with col3:
                    rma_sheet = st.selectbox("Feuille des RMA", sheet_names)
                
                # Chargement des données
                df_inst = pd.read_excel(xls, sheet_name=inst_sheet)
                df_inc = pd.read_excel(xls, sheet_name=inc_sheet)
                df_rma = pd.read_excel(xls, sheet_name=rma_sheet)
                
                # Affichage aperçu
                st.success("Fichier chargé avec succès!")
                tab1, tab2, tab3 = st.tabs(["Installations", "Incidents", "RMA"])
                with tab1:
                    st.dataframe(df_inst.head())
                with tab2:
                    st.dataframe(df_inc.head())
                with tab3:
                    st.dataframe(df_rma.head())
                
                # Stockage en session
                st.session_state['raw_data'] = {
                    'inst': df_inst,
                    'inc': df_inc,
                    'rma': df_rma,
                    'sheet_names': {
                        'inst': inst_sheet,
                        'inc': inc_sheet,
                        'rma': rma_sheet
                    }
                }
                
            except Exception as e:
                st.error(f"Erreur lors du chargement: {str(e)}")

    # Étape 2: Mapping des colonnes
    if 'raw_data' in st.session_state:
        with st.expander("ÉTAPE 2: Configuration des colonnes", expanded=True):
            st.markdown("**Veuillez mapper chaque champ aux colonnes de vos données**")
            
            col_mapping = {}
            df_inst = st.session_state['raw_data']['inst']
            df_inc = st.session_state['raw_data']['inc']
            df_rma = st.session_state['raw_data']['rma']
            
            # Mapping pour les installations
            with st.container():
                st.subheader("Installations")
                cols = st.columns(4)
                with cols[0]:
                    col_mapping['inst'] = {
                        'serie': st.selectbox("Colonne Série", df_inst.columns, key='inst_serie'),
                        'modele': st.selectbox("Colonne Modèle", df_inst.columns, key='inst_modele')
                    }
                with cols[1]:
                    col_mapping['inst']['pays_ref'] = st.selectbox(
                        "Colonne Réf. Pays", 
                        df_inst.columns, 
                        key='inst_pays_ref'
                    )
                with cols[2]:
                    col_mapping['inst']['filiale'] = st.selectbox(
                        "Colonne Filiale", 
                        df_inst.columns, 
                        key='inst_filiale'
                    )
                with cols[3]:
                    col_mapping['inst']['date'] = st.selectbox(
                        "Colonne Date Installation", 
                        df_inst.columns, 
                        key='inst_date'
                    )
            
            # Mapping pour les incidents
            with st.container():
                st.subheader("Incidents")
                cols = st.columns(4)
                with cols[0]:
                    col_mapping['inc'] = {
                        'serie': st.selectbox("Colonne Série", df_inc.columns, key='inc_serie'),
                        'incident': st.selectbox("Colonne Incident", df_inc.columns, key='inc_incident')
                    }
                with cols[1]:
                    col_mapping['inc']['date'] = st.selectbox(
                        "Colonne Date Incident", 
                        df_inc.columns, 
                        key='inc_date'
                    )
            
            # Mapping pour les RMA
            with st.container():
                st.subheader("Retours RMA")
                cols = st.columns(4)
                with cols[0]:
                    col_mapping['rma'] = {
                        'serie': st.selectbox("Colonne Série", df_rma.columns, key='rma_serie'),
                        'rma': st.selectbox("Colonne RMA", df_rma.columns, key='rma_num')
                    }
                with cols[1]:
                    col_mapping['rma']['date'] = st.selectbox(
                        "Colonne Date RMA", 
                        df_rma.columns, 
                        key='rma_date'
                    )
            
            st.session_state['col_mapping'] = col_mapping

    # Étape 3: Traitement et analyse
    if 'col_mapping' in st.session_state:
        with st.expander("ÉTAPE 3: Traitement et Analyse", expanded=True):
            if st.button("Lancer le traitement"):
                with st.spinner('Traitement en cours...'):
                    try:
                        # Récupération des données
                        raw_data = st.session_state['raw_data']
                        col_mapping = st.session_state['col_mapping']
                        
                        # Traitement
                        processed_data = process_data(
                            raw_data['inst'],
                            raw_data['inc'],
                            raw_data['rma'],
                            col_mapping
                        )
                        
                        # Validation S/N et date fabrication
                        processed_data['serie_valide'] = processed_data[
                            col_mapping['inst']['serie']
                        ].apply(validate_serial, format_rules={})
                        
                        processed_data['date_fabrication'] = processed_data[
                            col_mapping['inst']['serie']
                        ].apply(extract_manufacture_date, date_rules={})
                        
                        # Calculs supplémentaires
                        if col_mapping['inst']['date'] in processed_data.columns:
                            processed_data['age_installation'] = (
                                pd.to_datetime('now') - 
                                pd.to_datetime(processed_data[col_mapping['inst']['date']])
                            ).dt.days
                        
                        # Sauvegarde des résultats
                        st.session_state['processed_data'] = processed_data
                        st.success("Traitement terminé avec succès!")
                        
                        # Affichage des résultats
                        st.dataframe(processed_data.head())
                        
                        # Visualisations
                        st.subheader("Analyses")
                        if 'ttf' in processed_data.columns:
                            fig, ax = plt.subplots(figsize=(10, 6))
                            sns.boxplot(
                                data=processed_data,
                                x=col_mapping['inst']['modele'],
                                y='ttf'
                            )
                            plt.title("TTF par modèle")
                            st.pyplot(fig)
                        
                    except Exception as e:
                        st.error(f"Erreur lors du traitement: {str(e)}")

    # Étape 4: Export des résultats
    if 'processed_data' in st.session_state:
        with st.expander("ÉTAPE 4: Export des Résultats"):
            # Export Excel
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                st.session_state['processed_data'].to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Télécharger Excel",
                data=excel_buffer.getvalue(),
                file_name="resultats_analyse.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Export PDF
            if st.button("Générer PDF"):
                pdf_buffer = BytesIO()
                with PdfPages(pdf_buffer) as pdf:
                    plt.figure(figsize=(11, 8))
                    plt.text(0.1, 0.9, "Rapport d'analyse", fontsize=16)
                    plt.axis('off')
                    
                    if 'ttf' in st.session_state['processed_data'].columns:
                        plt.figure(figsize=(10, 6))
                        sns.boxplot(
                            data=st.session_state['processed_data'],
                            x=st.session_state['col_mapping']['inst']['modele'],
                            y='ttf'
                        )
                        plt.title("TTF par modèle")
                        pdf.savefig()
                        plt.close()
                
                st.download_button(
                    label="📥 Télécharger PDF",
                    data=pdf_buffer.getvalue(),
                    file_name="rapport_analyse.pdf",
                    mime="application/pdf"
                )

if __name__ == '__main__':
    main()
