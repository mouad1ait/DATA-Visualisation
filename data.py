import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from fpdf import FPDF
import base64

# Configuration de la page
st.set_page_config(layout="wide", page_title="Analyse Technique des Appareils")

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
            df, stats_df = prepare_data(df)
            
            # Sidebar avec filtres et commentaires
            with st.sidebar:
                st.header("Filtres et Commentaires")
                
                # Filtre par modèle
                model_list = ['Tous'] + sorted(df['modèle'].dropna().unique().tolist())
                model_filter = st.selectbox("Modèle", model_list)
                
                # Filtre par filiale
                filiale_list = ['Tous'] + sorted(df['filiale'].dropna().unique().tolist())
                filiale_filter = st.selectbox("Filiale", filiale_list)
                
                # Commentaires
                st.header("Commentaires")
                global_comment = st.text_area("Commentaire général sur l'analyse")
                
                graph_comments = {
                    'filiale_table': st.text_area("Commentaire sur la répartition par filiale"),
                    'ttf_hist': st.text_area("Commentaire sur le Time to Failure"),
                    'age_hist': st.text_area("Commentaire sur l'âge des appareils")
                }
            
            # Application des filtres
            filtered_df = apply_filters(df, model_filter, filiale_filter)
            
            # Section des indicateurs
            st.header("🔍 Indicateurs Clés")
            cols = st.columns(4)
            
            with cols[0]:
                st.metric("Appareils analysés", len(filtered_df))
                
            with cols[1]:
                valid_ttf = filtered_df['Time_to_Failure_months'].notna().sum()
                st.metric("Appareils avec incidents", valid_ttf)
            
            with cols[2]:
                if valid_ttf > 0:
                    max_ttf = filtered_df['Time_to_Failure_months'].max()
                    st.metric("Max Time to Failure (mois)", f"{max_ttf:.1f}")
            
            with cols[3]:
                avg_age = filtered_df['Age_depuis_fabrication_months'].mean()
                st.metric("Âge moyen depuis fab. (mois)", f"{avg_age:.1f}")
            
            # Section tableau de répartition par filiale
            st.header("📋 Répartition par Filiale")
            filiale_table = create_filiale_table(filtered_df)
            st.dataframe(filiale_table, height=400)
            
            if graph_comments['filiale_table']:
                st.info(f"💬 {graph_comments['filiale_table']}")
            
            # Section visualisations
            st.header("📈 Visualisations")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Time to Failure (mois)")
                fig_ttf = plot_histogram(filtered_df, 'Time_to_Failure_months', 
                                       "Distribution du Time to Failure", 
                                       "Mois avant incident", "Nombre d'appareils")
                if graph_comments['ttf_hist']:
                    st.info(f"💬 {graph_comments['ttf_hist']}")
            
            with col2:
                st.subheader("Âge depuis fabrication (mois)")
                fig_age = plot_histogram(filtered_df, 'Age_depuis_fabrication_months', 
                                       "Distribution de l'âge des appareils", 
                                       "Âge (mois)", "Nombre d'appareils")
                if graph_comments['age_hist']:
                    st.info(f"💬 {graph_comments['age_hist']}")
            
            # Section export
            st.header("💾 Export des Résultats")
            
            export_col1, export_col2 = st.columns(2)
            with export_col1:
                st.subheader("Export Excel")
                st.download_button(
                    label="Télécharger les données analysées (Excel)",
                    data=export_to_excel(filtered_df, stats_df),
                    file_name='analyse_appareils.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            
            with export_col2:
                st.subheader("Rapport PDF")
                pdf_report = create_pdf_report(filtered_df, filiale_table, fig_ttf, fig_age, 
                                             global_comment, graph_comments)
                st.download_button(
                    label="Télécharger le rapport complet (PDF)",
                    data=pdf_report,
                    file_name='rapport_analyse.pdf',
                    mime='application/pdf'
                )
            
            # Affichage des données brutes (optionnel)
            if st.checkbox("Afficher les données brutes"):
                st.dataframe(filtered_df)
                
        except Exception as e:
            st.error(f"Erreur lors du traitement: {str(e)}")

def prepare_data(df):
    # Nettoyage initial
    df = df.dropna(how='all')
    stats_data = {'Statistique': [], 'Valeur': []}
    
    # Conversion des dates
    date_cols = ['FabricationDate', 'installationDate', 'incidentDate', 'Lastconnexion']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
        invalid_dates = df[col].isna().sum()
        if invalid_dates > 0:
            st.warning(f"{invalid_dates} dates invalides dans {col}")

    # Calcul des métriques
    today = datetime.now()
    
    # Time to Failure (en mois)
    df['TTF_installation'] = (df['incidentDate'] - df['installationDate']).dt.days / 30.44
    df['TTF_fabrication'] = (df['incidentDate'] - df['FabricationDate']).dt.days / 30.44
    df['Time_to_Failure_months'] = df[['TTF_installation', 'TTF_fabrication']].max(axis=1)
    
    # Âges (en mois)
    df['Age_depuis_installation_months'] = (today - df['installationDate']).dt.days / 30.44
    df['Age_depuis_fabrication_months'] = (today - df['FabricationDate']).dt.days / 30.44
    
    # Statistiques descriptives
    stats_data['Statistique'].extend([
        'Appareils totaux',
        'Appareils avec incidents',
        'Time to Failure max (mois)',
        'Âge moyen depuis fab. (mois)'
    ])
    
    stats_data['Valeur'].extend([
        len(df),
        df['Time_to_Failure_months'].notna().sum(),
        df['Time_to_Failure_months'].max() if df['Time_to_Failure_months'].notna().any() else 'N/A',
        df['Age_depuis_fabrication_months'].mean()
    ])
    
    stats_df = pd.DataFrame(stats_data)
    return df, stats_df

def apply_filters(df, model, filiale):
    filtered = df.copy()
    
    if model != 'Tous':
        filtered = filtered[filtered['modèle'] == model]
    
    if filiale != 'Tous':
        filtered = filtered[filtered['filiale'] == filiale]
    
    return filtered

def create_filiale_table(df):
    if df.empty:
        return pd.DataFrame()
    
    table = df.groupby('filiale').agg(
        Nombre=pd.NamedAgg(column='SN', aggfunc='count'),
        Time_to_Failure_moyen_mois=pd.NamedAgg(column='Time_to_Failure_months', aggfunc='mean'),
        Age_moyen_depuis_fab_mois=pd.NamedAgg(column='Age_depuis_fabrication_months', aggfunc='mean')
    ).reset_index()
    
    table['Time_to_Failure_moyen_mois'] = table['Time_to_Failure_moyen_mois'].round(1)
    table['Age_moyen_depuis_fab_mois'] = table['Age_moyen_depuis_fab_mois'].round(1)
    
    return table.sort_values('Nombre', ascending=False)

def plot_histogram(df, column, title, xlabel, ylabel):
    if column not in df or df[column].isnull().all():
        st.warning(f"Données manquantes pour {title}")
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(data=df, x=column, bins=20, kde=True, ax=ax)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    plt.tight_layout()
    return fig

def export_to_excel(data_df, stats_df):
    output = pd.ExcelWriter('temp_export.xlsx', engine='openpyxl')
    data_df.to_excel(output, sheet_name='Données analysées', index=False)
    stats_df.to_excel(output, sheet_name='Statistiques', index=False)
    
    # Ajout des métriques par filiale
    filiale_table = create_filiale_table(data_df)
    filiale_table.to_excel(output, sheet_name='Par filiale', index=False)
    
    output.close()
    
    with open('temp_export.xlsx', 'rb') as f:
        data = f.read()
    os.remove('temp_export.xlsx')
    return data

def create_pdf_report(data_df, filiale_table, fig_ttf, fig_age, global_comment, graph_comments):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # En-tête
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Rapport d'Analyse des Appareils Techniques", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align='C')
    pdf.ln(10)
    
    # Commentaire global
    if global_comment:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Commentaire global:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=global_comment)
        pdf.ln(5)
    
    # Statistiques
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Statistiques Clés", ln=1)
    pdf.set_font("Arial", size=12)
    
    stats = [
        f"Appareils analysés: {len(data_df)}",
        f"Appareils avec incidents: {data_df['Time_to_Failure_months'].notna().sum()}",
        f"Time to Failure max: {data_df['Time_to_Failure_months'].max():.1f} mois",
        f"Âge moyen depuis fabrication: {data_df['Age_depuis_fabrication_months'].mean():.1f} mois"
    ]
    
    for stat in stats:
        pdf.cell(0, 10, txt=stat, ln=1)
    pdf.ln(10)
    
    # Tableau par filiale
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Répartition par Filiale", ln=1)
    
    if not filiale_table.empty:
        col_widths = [60, 30, 50, 50]
        pdf.set_font("Arial", 'B', 12)
        cols = filiale_table.columns
        for i, col in enumerate(cols):
            pdf.cell(col_widths[i], 10, txt=str(col), border=1)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        for _, row in filiale_table.iterrows():
            for i, col in enumerate(cols):
                pdf.cell(col_widths[i], 10, txt=str(row[col]), border=1)
            pdf.ln()
    
    if graph_comments['filiale_table']:
        pdf.ln(5)
        pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(0, 10, txt=f"Commentaire: {graph_comments['filiale_table']}")
    
    pdf.ln(10)
    
    # Graphiques
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Visualisations", ln=1)
    
    # Sauvegarde des graphiques temporaires
    temp_files = []
    try:
        if fig_ttf:
            ttf_path = "temp_ttf.png"
            fig_ttf.savefig(ttf_path, bbox_inches='tight', dpi=150)
            temp_files.append(ttf_path)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Distribution du Time to Failure", ln=1)
            pdf.image(ttf_path, w=180)
            
            if graph_comments['ttf_hist']:
                pdf.set_font("Arial", 'I', 10)
                pdf.multi_cell(0, 10, txt=f"Commentaire: {graph_comments['ttf_hist']}")
                pdf.ln(5)
        
        if fig_age:
            age_path = "temp_age.png"
            fig_age.savefig(age_path, bbox_inches='tight', dpi=150)
            temp_files.append(age_path)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Distribution de l'âge des appareils", ln=1)
            pdf.image(age_path, w=180)
            
            if graph_comments['age_hist']:
                pdf.set_font("Arial", 'I', 10)
                pdf.multi_cell(0, 10, txt=f"Commentaire: {graph_comments['age_hist']}")
                pdf.ln(5)
    
    finally:
        # Nettoyage des fichiers temporaires
        for file in temp_files:
            if os.path.exists(file):
                os.remove(file)
    
    # Retourne directement les bytes du PDF
    return pdf.output(dest='S').encode('latin1')
if __name__ == "__main__":
    main()
