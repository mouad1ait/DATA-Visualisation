import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from io import BytesIO
from PIL import Image
import base64

# Configuration de la page
st.set_page_config(
    page_title="Analyse Produits",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonctions de traitement (conservées depuis la version originale)
def analyze_data(df_inst, df_inc, df_rma):
    analysis = {
        "Produits installés": len(df_inst),
        "Produits avec incidents": len(df_inc),
        "Produits retournés": len(df_rma),
        "Dates min/max installation": (df_inst['date_installation'].min(), df_inst['date_installation'].max()),
        "Modèles uniques": df_inst['modèle'].unique().tolist(),
        "Pays uniques": df_inst['filiale'].unique().tolist()
    }
    return analysis

def merge_data(df_inst, df_inc, df_rma):
    merged = pd.merge(df_inst, df_inc, on=['no_serie', 'modèle'], how='left', suffixes=('', '_incident'))
    merged = pd.merge(merged, df_rma, on=['no_serie', 'modèle'], how='left', suffixes=('', '_rma'))
    merged = merged.loc[:,~merged.columns.duplicated()]
    return merged

def convert_dates(df):
    date_cols = [col for col in df.columns if 'date' in col.lower()]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        df[col] = df[col].dt.strftime('%d/%m/%Y')
    return df

def validate_serial(serial):
    if pd.isna(serial):
        return False
    return len(str(serial)) >= 6

def extract_manufacture_date(serial):
    if not validate_serial(serial):
        return None
    try:
        year = int(str(serial)[:2]) + 2000
        week = int(str(serial)[2:4])
        return datetime.strptime(f"{week} {year}", "%U %Y").strftime('%d/%m/%Y')
    except:
        return None

def calculate_ages(df):
    df['age_fabrication'] = (pd.to_datetime('now') - pd.to_datetime(df['date_fabrication'], errors='coerce')).dt.days
    df['age_installation'] = (pd.to_datetime('now') - pd.to_datetime(df['date_installation'], errors='coerce')).dt.days
    return df

def calculate_ttf(df):
    df['ttf'] = (pd.to_datetime(df['date_incident']) - pd.to_datetime(df['date_installation'])).dt.days
    ttf_stats = df.groupby('modèle')['ttf'].agg(['min', 'mean', 'max']).reset_index()
    return df, ttf_stats

def calculate_stock_time(df):
    df['duree_stock'] = (pd.to_datetime(df['date_installation']) - pd.to_datetime(df['date_fabrication'])).dt.days
    return df

# Interface Streamlit
def main():
    st.title("📊 Analyse des Produits")
    st.markdown("""
    **Outil complet d'analyse des données produits**  
    *Fusion des données installations/incidents/RMA avec calculs avancés*
    """)

    # Upload fichier
    with st.expander("ÉTAPE 1 : Chargement des données", expanded=True):
        uploaded_file = st.file_uploader("Déposer votre fichier Excel ici", type=["xlsx", "xls"])
        
        if uploaded_file:
            try:
                df_inst = pd.read_excel(uploaded_file, sheet_name='installations')
                df_inc = pd.read_excel(uploaded_file, sheet_name='incidents')
                df_rma = pd.read_excel(uploaded_file, sheet_name='RMA')
                
                with st.container():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Produits installés", len(df_inst))
                    with col2:
                        st.metric("Incidents enregistrés", len(df_inc))
                    with col3:
                        st.metric("Retours RMA", len(df_rma))
                
                # Analyse rapide
                st.success("Fichier chargé avec succès !")
                if st.checkbox("Afficher un aperçu des données brutes"):
                    tab1, tab2, tab3 = st.tabs(["Installations", "Incidents", "RMA"])
                    with tab1:
                        st.dataframe(df_inst.head())
                    with tab2:
                        st.dataframe(df_inc.head())
                    with tab3:
                        st.dataframe(df_rma.head())
            
            except Exception as e:
                st.error(f"Erreur lors du chargement : {str(e)}")

    # Traitement des données
    if 'df_inst' in locals():
        with st.expander("ÉTAPE 2 : Traitement des données"):
            if st.button("Lancer le traitement complet"):
                with st.spinner('Traitement en cours...'):
                    try:
                        # Exécution des fonctions
                        analysis = analyze_data(df_inst, df_inc, df_rma)
                        merged = merge_data(df_inst, df_inc, df_rma)
                        merged = convert_dates(merged)
                        
                        merged['serie_valide'] = merged['no_serie'].apply(validate_serial)
                        merged['date_fabrication'] = merged['no_serie'].apply(extract_manufacture_date)
                        
                        merged = calculate_ages(merged)
                        merged, ttf_stats = calculate_ttf(merged)
                        merged = calculate_stock_time(merged)
                        
                        # Sauvegarde en session
                        st.session_state['processed_data'] = merged
                        st.session_state['ttf_stats'] = ttf_stats
                        
                        st.success("Traitement terminé avec succès !")
                        
                        # Affichage des résultats
                        st.subheader("Statistiques clés")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.dataframe(ttf_stats.style.background_gradient(cmap='YlOrRd'))
                        with col2:
                            st.write("**Distribution des âges**")
                            fig, ax = plt.subplots()
                            sns.histplot(merged['age_installation'], kde=True, ax=ax)
                            st.pyplot(fig)
                        
                    except Exception as e:
                        st.error(f"Erreur lors du traitement : {str(e)}")

    # Visualisations
    if 'processed_data' in st.session_state:
        with st.expander("ÉTAPE 3 : Visualisations", expanded=True):
            st.subheader("Analyses statistiques")
            
            tab1, tab2, tab3 = st.tabs(["Par modèle", "Par pays", "Évolutions temporelles"])
            
            with tab1:
                fig = plt.figure(figsize=(10, 6))
                sns.boxplot(data=st.session_state['processed_data'], x='modèle', y='ttf')
                plt.title('TTF par modèle')
                st.pyplot(fig)
                
            with tab2:
                fig = plt.figure(figsize=(12, 6))
                sns.countplot(data=st.session_state['processed_data'], y='filiale', hue='modèle')
                plt.title('Répartition par pays')
                st.pyplot(fig)
                
            with tab3:
                fig = plt.figure(figsize=(12, 6))
                temp_df = st.session_state['processed_data'].copy()
                temp_df['date_installation'] = pd.to_datetime(temp_df['date_installation'])
                temp_df['mois_installation'] = temp_df['date_installation'].dt.to_period('M')
                monthly = temp_df.groupby('mois_installation').size()
                monthly.plot(kind='line', marker='o')
                plt.title('Installations par mois')
                st.pyplot(fig)

    # Export des résultats
    if 'processed_data' in st.session_state:
        with st.expander("ÉTAPE 4 : Export des résultats"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Export Excel")
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    st.session_state['processed_data'].to_excel(writer, sheet_name='Données traitées', index=False)
                    st.session_state['ttf_stats'].to_excel(writer, sheet_name='Statistiques TTF', index=False)
                
                st.download_button(
                    label="📥 Télécharger Excel",
                    data=excel_buffer.getvalue(),
                    file_name="analyse_produits.xlsx",
                    mime="application/vnd.ms-excel"
                )
            
            with col2:
                st.subheader("Export PDF")
                if st.button("Générer PDF"):
                    pdf_buffer = BytesIO()
                    with PdfPages(pdf_buffer) as pdf:
                        # Page 1 - Résumé
                        plt.figure(figsize=(11, 8))
                        plt.text(0.1, 0.9, "Rapport d'analyse produits", fontsize=16)
                        plt.text(0.1, 0.8, f"Date du rapport : {datetime.now().strftime('%d/%m/%Y')}", fontsize=10)
                        plt.axis('off')
                        
                        # Tableau stats
                        plt.table(cellText=st.session_state['ttf_stats'].values,
                                 colLabels=st.session_state['ttf_stats'].columns,
                                 cellLoc='center', loc='center')
                        pdf.savefig()
                        plt.close()
                        
                        # Page 2 - Graphiques
                        fig = plt.figure(figsize=(11, 8))
                        sns.boxplot(data=st.session_state['processed_data'], x='modèle', y='ttf')
                        plt.title('TTF par modèle')
                        pdf.savefig(fig)
                        plt.close()
                    
                    st.download_button(
                        label="📥 Télécharger PDF",
                        data=pdf_buffer.getvalue(),
                        file_name="rapport_produits.pdf",
                        mime="application/pdf"
                    )

# Exécution
if __name__ == '__main__':
    main()
