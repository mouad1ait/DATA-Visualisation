import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from fpdf import FPDF
import base64
import numpy as np
from io import BytesIO
import logging

# Configuration de l'application
st.set_page_config(layout="wide", page_title="Analyse Technique des Appareils")
logging.basicConfig(level=logging.INFO)

def main():
    st.title("📊 Analyse Complète des Appareils Techniques")
    
    # Chargement du fichier
    uploaded_file = st.file_uploader("Charger un fichier Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            # Lecture du fichier
            df = pd.read_excel(uploaded_file)
            
            # Vérification des colonnes
            required_columns = [
                'modèle', 'SN', 'FabricationDate', 'refPays', 'filiale',
                'installationDate', 'Lastconnexion', 'incident', 'incidentDate'
            ]
            
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                st.error(f"Colonnes manquantes: {', '.join(missing_cols)}")
                st.write("Colonnes détectées:", list(df.columns))
                return
            
            # Préparation des données
            df = clean_and_prepare_data(df)
            
            # Sidebar avec filtres et commentaires
            with st.sidebar:
                st.header("Filtres")
                model_filter = st.selectbox(
                    "Modèle",
                    ['Tous'] + sorted(df['modèle'].dropna().unique().tolist())
                
                filiale_filter = st.selectbox(
                    "Filiale",
                    ['Tous'] + sorted(df['filiale'].dropna().unique().tolist())
                
                st.header("Commentaires")
                global_comment = st.text_area("Commentaire général")
                ttf_comment = st.text_area("Interprétation Time to Failure")
                age_comment = st.text_area("Interprétation Âge des appareils")
            
            # Application des filtres
            filtered_df = apply_filters(df, model_filter, filiale_filter)
            
            # Section indicateurs
            show_key_metrics(filtered_df)
            
            # Section tableau filiale
            show_filiale_table(filtered_df)
            
            # Section visualisations
            show_visualizations(filtered_df, ttf_comment, age_comment)
            
            # Section export
            show_export_options(filtered_df, global_comment, ttf_comment, age_comment)
            
        except Exception as e:
            st.error(f"Erreur lors du traitement: {str(e)}")
            logging.exception("Erreur dans le traitement principal")

def clean_and_prepare_data(df):
    """Nettoie et prépare les données"""
    # Conversion des dates
    date_cols = ['FabricationDate', 'installationDate', 'incidentDate', 'Lastconnexion']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Calcul des métriques
    today = datetime.now()
    
    # Time to Failure (en mois)
    df['TTF_installation'] = (df['incidentDate'] - df['installationDate']).dt.days / 30.44
    df['TTF_fabrication'] = (df['incidentDate'] - df['FabricationDate']).dt.days / 30.44
    df['Time_to_Failure'] = df[['TTF_installation', 'TTF_fabrication']].max(axis=1)
    
    # Âges (en mois)
    df['Age_installation'] = (today - df['installationDate']).dt.days / 30.44
    df['Age_fabrication'] = (today - df['FabricationDate']).dt.days / 30.44
    
    return df

def apply_filters(df, model, filiale):
    """Applique les filtres aux données"""
    filtered = df.copy()
    if model != 'Tous':
        filtered = filtered[filtered['modèle'] == model]
    if filiale != 'Tous':
        filtered = filtered[filtered['filiale'] == filiale]
    return filtered

def show_key_metrics(df):
    """Affiche les indicateurs clés"""
    st.header("🔍 Indicateurs Clés")
    cols = st.columns(4)
    
    with cols[0]:
        st.metric("Appareils analysés", len(df))
        
    with cols[1]:
        valid_ttf = df['Time_to_Failure'].notna().sum()
        st.metric("Appareils avec incidents", valid_ttf)
    
    with cols[2]:
        if valid_ttf > 0:
            max_ttf = df['Time_to_Failure'].max()
            st.metric("Max Time to Failure (mois)", f"{max_ttf:.1f}")
    
    with cols[3]:
        avg_age = df['Age_fabrication'].mean()
        st.metric("Âge moyen depuis fab. (mois)", f"{avg_age:.1f}")

def show_filiale_table(df):
    """Affiche le tableau de répartition par filiale"""
    st.header("📋 Répartition par Filiale")
    
    table = df.groupby('filiale').agg(
        Nombre=('SN', 'count'),
        'TTF moyen (mois)'=('Time_to_Failure', 'mean'),
        'Âge moyen (mois)'=('Age_fabrication', 'mean')
    ).round(1).sort_values('Nombre', ascending=False)
    
    st.dataframe(table.style.background_gradient(cmap='Blues'), height=400)

def show_visualizations(df, ttf_comment, age_comment):
    """Affiche les graphiques"""
    st.header("📈 Visualisations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Time to Failure (mois)")
        fig1 = plt.figure(figsize=(10, 6))
        sns.histplot(df['Time_to_Failure'].dropna(), bins=20, kde=True)
        plt.xlabel("Mois avant incident")
        plt.ylabel("Nombre d'appareils")
        st.pyplot(fig1)
        if ttf_comment:
            st.info(f"💬 {ttf_comment}")
    
    with col2:
        st.subheader("Âge depuis fabrication (mois)")
        fig2 = plt.figure(figsize=(10, 6))
        sns.histplot(df['Age_fabrication'].dropna(), bins=20, kde=True)
        plt.xlabel("Âge (mois)")
        plt.ylabel("Nombre d'appareils")
        st.pyplot(fig2)
        if age_comment:
            st.info(f"💬 {age_comment}")

def show_export_options(df, global_comment, ttf_comment, age_comment):
    """Gère l'export des données"""
    st.header("💾 Export des Résultats")
    
    # Export Excel
    st.subheader("Export Excel")
    excel_data = export_to_excel(df, global_comment, ttf_comment, age_comment)
    st.download_button(
        label="Télécharger Excel",
        data=excel_data,
        file_name='analyse_appareils.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Export PDF
    st.subheader("Export PDF")
    if st.button("Générer le rapport PDF"):
        pdf_report = create_pdf_report(df, global_comment, ttf_comment, age_comment)
        st.download_button(
            label="Télécharger PDF",
            data=pdf_report,
            file_name='rapport_analyse.pdf',
            mime='application/pdf'
        )

def export_to_excel(df, global_comment, ttf_comment, age_comment):
    """Exporte les données au format Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Données complètes
        df.to_excel(writer, sheet_name='Données', index=False)
        
        # Statistiques
        stats = pd.DataFrame({
            'Métrique': ['Appareils totaux', 'Appareils avec incidents',
                        'Time to Failure max', 'Âge moyen depuis fabrication'],
            'Valeur': [
                len(df),
                df['Time_to_Failure'].notna().sum(),
                f"{df['Time_to_Failure'].max():.1f} mois" if df['Time_to_Failure'].notna().any() else 'N/A',
                f"{df['Age_fabrication'].mean():.1f} mois"
            ]
        })
        stats.to_excel(writer, sheet_name='Statistiques', index=False)
        
        # Commentaires
        comments = pd.DataFrame({
            'Section': ['Global', 'Time to Failure', 'Âge des appareils'],
            'Commentaire': [global_comment, ttf_comment, age_comment]
        })
        comments.to_excel(writer, sheet_name='Commentaires', index=False)
    
    return output.getvalue()

def create_pdf_report(df, global_comment, ttf_comment, age_comment):
    """Crée un rapport PDF professionnel"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # En-tête
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Rapport d'Analyse Technique", ln=1, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align='C')
    pdf.ln(15)
    
    # Commentaire global
    if global_comment:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Commentaire Global:", ln=1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 8, txt=global_comment)
        pdf.ln(10)
    
    # Statistiques
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Statistiques Clés", ln=1)
    pdf.set_font("Arial", size=10)
    
    stats = [
        f"Appareils analysés: {len(df)}",
        f"Appareils avec incidents: {df['Time_to_Failure'].notna().sum()}",
        f"Time to Failure max: {df['Time_to_Failure'].max():.1f} mois" if df['Time_to_Failure'].notna().any() else "Time to Failure max: N/A",
        f"Âge moyen depuis fabrication: {df['Age_fabrication'].mean():.1f} mois"
    ]
    
    for stat in stats:
        pdf.cell(0, 8, txt=stat, ln=1)
    pdf.ln(10)
    
    # Tableau par filiale
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Répartition par Filiale", ln=1)
    
    filiale_table = df.groupby('filiale').agg(
        Nombre=('SN', 'count'),
        'TTF moyen (mois)'=('Time_to_Failure', 'mean'),
        'Âge moyen (mois)'=('Age_fabrication', 'mean')
    ).round(1).reset_index()
    
    # En-têtes du tableau
    pdf.set_font("Arial", 'B', 10)
    col_width = [50, 30, 40, 40]
    headers = filiale_table.columns
    for i, header in enumerate(headers):
        pdf.cell(col_width[i], 10, str(header), border=1)
    pdf.ln()
    
    # Données du tableau
    pdf.set_font("Arial", size=10)
    for _, row in filiale_table.iterrows():
        for i, val in enumerate(row):
            pdf.cell(col_width[i], 10, str(val), border=1)
        pdf.ln()
    
    pdf.ln(15)
    
    # Commentaires
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Commentaires", ln=1)
    
    if ttf_comment:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Time to Failure:", ln=1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 8, txt=ttf_comment)
        pdf.ln(5)
    
    if age_comment:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Âge des appareils:", ln=1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 8, txt=age_comment)
    
    return pdf.output(dest='S').encode('latin1')

if __name__ == "__main__":
    main()
