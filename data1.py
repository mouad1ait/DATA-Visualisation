import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from fpdf import FPDF
from io import BytesIO

# Configuration de l'application
st.set_page_config(layout="wide", page_title="Analyse Technique des Appareils")

def main():
    st.title("📊 Analyse Complète des Appareils Techniques")
    
    # Chargement du fichier
    uploaded_file = st.file_uploader("Charger un fichier Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            df = load_and_validate_data(uploaded_file)
            df = clean_and_prepare_data(df)
            
            # Affichage des données brutes
            st.header("📋 Données Brutes")
            st.dataframe(df, height=400)
            
            # Sidebar
            with st.sidebar:
                model_filter, filiale_filter = create_filters(df)
                global_comment = st.text_area("Commentaire général")
                ttf_comment = st.text_area("Interprétation Time to Failure")
                age_comment = st.text_area("Interprétation Âge des appareils")
            
            filtered_df = apply_filters(df, model_filter, filiale_filter)
            
            # Tableau de répartition
            st.header("📊 Répartition par Filiale")
            show_filiale_table(filtered_df)
            
            # Indicateurs
            st.header("🔍 Indicateurs Clés")
            show_key_metrics(filtered_df)
            
            # Visualisations
            st.header("📈 Visualisations")
            show_visualizations(filtered_df, ttf_comment, age_comment)
            
            # Export
            st.header("💾 Export des Résultats")
            show_export_options(filtered_df, global_comment, ttf_comment, age_comment)
            
        except Exception as e:
            st.error(f"Erreur: {str(e)}")

def load_and_validate_data(uploaded_file):
    """Charge et valide les données"""
    df = pd.read_excel(uploaded_file)
    required_columns = [
        'modèle', 'SN', 'FabricationDate', 'refPays', 'filiale',
        'installationDate', 'Lastconnexion', 'incident', 'incidentDate'
    ]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes: {', '.join(missing_cols)}")
    return df

def clean_and_prepare_data(df):
    """Nettoie et prépare les données"""
    # Conversion des dates
    date_cols = ['FabricationDate', 'installationDate', 'incidentDate', 'Lastconnexion']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Calcul des métriques
    today = datetime.now()
    
    # Time to Failure selon la nouvelle règle
    ttf_inst = (df['incidentDate'] - df['installationDate']).dt.days / 30.44
    ttf_fab = (df['incidentDate'] - df['FabricationDate']).dt.days / 30.44
    df['Time_to_Failure'] = np.where(ttf_inst > 0, ttf_inst, ttf_fab)
    
    # Âges (en mois)
    df['Age_installation'] = (today - df['installationDate']).dt.days / 30.44
    df['Age_fabrication'] = (today - df['FabricationDate']).dt.days / 30.44
    
    return df

def create_filters(df):
    """Crée les widgets de filtre"""
    return (
        st.selectbox("Modèle", ['Tous'] + sorted(df['modèle'].dropna().unique().tolist())),
        st.selectbox("Filiale", ['Tous'] + sorted(df['filiale'].dropna().unique().tolist()))
    )

def apply_filters(df, model, filiale):
    """Applique les filtres"""
    filtered = df.copy()
    if model != 'Tous':
        filtered = filtered[filtered['modèle'] == model]
    if filiale != 'Tous':
        filtered = filtered[filtered['filiale'] == filiale]
    return filtered

def show_filiale_table(df):
    """Affiche le tableau de répartition par filiale"""
    table = df.groupby('filiale').agg(
        Nombre=('SN', 'count'),
        **{'TTF moyen (mois)': ('Time_to_Failure', 'mean')},
        **{'Âge moyen (mois)': ('Age_fabrication', 'mean')}
    ).round(1).sort_values('Nombre', ascending=False)
    
    st.dataframe(table.style.background_gradient(cmap='Blues'), height=400)

def show_key_metrics(df):
    """Affiche les indicateurs clés"""
    cols = st.columns(4)
    metrics = [
        ("Appareils analysés", len(df)),
        ("Appareils avec incidents", df['Time_to_Failure'].notna().sum()),
        ("Max TTF (mois)", df['Time_to_Failure'].max() if df['Time_to_Failure'].notna().any() else 0),
        ("Âge moyen (mois)", df['Age_fabrication'].mean())
    ]
    
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, f"{value:.1f}" if isinstance(value, float) else value)

def show_visualizations(df, ttf_comment, age_comment):
    """Affiche les graphiques"""
    col1, col2 = st.columns(2)
    
    with col1:
        fig = plt.figure(figsize=(10, 6))
        sns.histplot(df['Time_to_Failure'].dropna(), bins=20, kde=True)
        plt.title("Distribution du Time to Failure")
        plt.xlabel("Mois avant incident")
        st.pyplot(fig)
        if ttf_comment:
            st.info(f"💬 {ttf_comment}")
    
    with col2:
        fig = plt.figure(figsize=(10, 6))
        sns.histplot(df['Age_fabrication'].dropna(), bins=20, kde=True)
        plt.title("Distribution de l'âge des appareils")
        plt.xlabel("Âge (mois)")
        st.pyplot(fig)
        if age_comment:
            st.info(f"💬 {age_comment}")

def show_export_options(df, global_comment, ttf_comment, age_comment):
    """Gère l'export des données"""
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
    
    # Export PDF
    if st.button("Générer PDF"):
        pdf_report = create_pdf_report(df, global_comment, ttf_comment, age_comment)
        st.download_button(
            "Télécharger PDF",
            pdf_report,
            "rapport_analyse.pdf",
            "application/pdf"
        )

def export_to_excel(df, global_comment, ttf_comment, age_comment):
    """Exporte en Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Données', index=False)
        stats = pd.DataFrame({
            'Statistique': ['Appareils totaux', 'Appareils avec incidents',
                          'Time to Failure max', 'Âge moyen'],
            'Valeur': [
                len(df),
                df['Time_to_Failure'].notna().sum(),
                f"{df['Time_to_Failure'].max():.1f}" if df['Time_to_Failure'].notna().any() else 'N/A',
                f"{df['Age_fabrication'].mean():.1f}"
            ]
        })
        stats.to_excel(writer, sheet_name='Statistiques', index=False)
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
        **{'TTF moyen (mois)': ('Time_to_Failure', 'mean')},
        **{'Âge moyen (mois)': ('Age_fabrication', 'mean')}
    ).round(1).reset_index()
    
    # En-têtes du tableau
    pdf.set_font("Arial", 'B', 10)
    col_width = [50, 30, 40, 40]
    headers = filiale_table.columns
    for i, header in enumerate(headers):
        pdf.cell(col_width[i], 10, str(header), border=1, align='C')
    pdf.ln()
    
    # Données du tableau
    pdf.set_font("Arial", size=10)
    for _, row in filiale_table.iterrows():
        for i, val in enumerate(row):
            pdf.cell(col_width[i], 10, str(val), border=1)
        pdf.ln()
    
    # Commentaires
    if global_comment or ttf_comment or age_comment:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Commentaires", ln=1)
        
        if global_comment:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Commentaire général:", ln=1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 8, txt=global_comment)
        
        if ttf_comment:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Time to Failure:", ln=1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 8, txt=ttf_comment)
        
        if age_comment:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Âge des appareils:", ln=1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 8, txt=age_comment)
    
    # Retourne directement les bytes sans ré-encoder
    return pdf.output(dest='S')

if __name__ == "__main__":
    main()
