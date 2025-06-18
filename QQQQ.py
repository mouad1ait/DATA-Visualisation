import streamlit as st
import pandas as pd
from datetime import datetime
import io
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Analyse Produits", layout="wide")
st.title("📊 Analyse des Produits Installés, Incidents et Retours")

# Fonctions de traitement
def process_data(uploaded_file):
    """Fusionne les données des 3 feuilles Excel"""
    try:
        # Charger les feuilles
        df_install = pd.read_excel(uploaded_file, sheet_name='Feuil1')
        df_incidents = pd.read_excel(uploaded_file, sheet_name='Feuil2')
        df_retours = pd.read_excel(uploaded_file, sheet_name='Feuil3')

        # Nettoyage des dates
        date_cols = ['date d\'installation', 'dernière connexion', 'date d\'incidents', 'date de retour']
        for df in [df_install, df_incidents, df_retours]:
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

        # Fusionner les données
        incidents_agg = df_incidents.groupby('no de série').agg(
            nombre_incidents=('incident', 'count'),
            dernier_incident=('date d\'incidents', 'max')
        ).reset_index()

        retours_agg = df_retours.groupby('no de série').agg(
            nombre_retours=('RMA', 'count'),
            dernier_retour=('date de retour', 'max'),
            RMA=('RMA', 'last')
        ).reset_index()

        df_final = df_install.merge(
            incidents_agg, 
            on='no de série', 
            how='left'
        ).merge(
            retours_agg, 
            on='no de série', 
            how='left'
        )

        # Calculs supplémentaires
        df_final['nombre_incidents'] = df_final['nombre_incidents'].fillna(0)
        df_final['nombre_retours'] = df_final['nombre_retours'].fillna(0)
        df_final['duree_depuis_installation'] = (datetime.now() - df_final['date d\'installation']).dt.days
        df_final['jours_inactivite'] = (datetime.now() - df_final['dernière connexion']).dt.days
        df_final['a_incident_sans_retour'] = (df_final['nombre_incidents'] > 0) & (df_final['nombre_retours'] == 0)

        return df_final
    
    except Exception as e:
        st.error(f"Erreur lors du traitement des données: {str(e)}")
        return None

def generate_stats(df):
    """Génère les statistiques principales"""
    stats = {}
    
    # Stats globales
    stats['global'] = {
        'total_produits': len(df),
        'produits_avec_incidents': len(df[df['nombre_incidents'] > 0]),
        'produits_retournes': len(df[df['nombre_retours'] > 0]),
        'taux_incidents': len(df[df['nombre_incidents'] > 0]) / len(df),
        'taux_retours': len(df[df['nombre_retours'] > 0]) / len(df)
    }
    
    # Par modèle
    stats['par_modele'] = df.groupby('modèle').agg({
        'no de série': 'count',
        'nombre_incidents': 'sum',
        'nombre_retours': 'sum',
        'duree_depuis_installation': 'mean',
        'jours_inactivite': 'mean'
    }).rename(columns={
        'no de série': 'nombre_produits',
        'duree_depuis_installation': 'duree_moyenne_installation',
        'jours_inactivite': 'inactivite_moyenne'
    })
    
    # Par pays
    stats['par_pays'] = df.groupby('filiale').agg({
        'no de série': 'count',
        'nombre_incidents': 'sum',
        'nombre_retours': 'sum'
    }).rename(columns={'no de série': 'nombre_produits'})
    
    return stats

# Interface utilisateur
uploaded_file = st.file_uploader("Télécharger votre fichier Excel", type=['xlsx'])

if uploaded_file:
    with st.spinner('Traitement des données en cours...'):
        df_final = process_data(uploaded_file)
        
    if df_final is not None:
        # Afficher les données fusionnées
        st.success("Données fusionnées avec succès!")
        
        # Téléchargement des données fusionnées
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Fusion')
        st.download_button(
            label="📥 Télécharger les données fusionnées",
            data=output.getvalue(),
            file_name="donnees_fusionnees.xlsx",
            mime="application/vnd.ms-excel"
        )
        
        # Statistiques
        st.subheader("🔍 Statistiques Globales")
        stats = generate_stats(df_final)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Produits", stats['global']['total_produits'])
        col2.metric("Produits avec Incidents", stats['global']['produits_avec_incidents'], 
                   f"{stats['global']['taux_incidents']:.1%}")
        col3.metric("Produits Retournés", stats['global']['produits_retournes'], 
                   f"{stats['global']['taux_retours']:.1%}")
        
        # Statistiques par modèle
        st.subheader("📈 Statistiques par Modèle")
        st.dataframe(stats['par_modele'].style.format({
            'duree_moyenne_installation': '{:.1f} jours',
            'inactivite_moyenne': '{:.1f} jours',
            'nombre_incidents': '{:.0f}',
            'nombre_retours': '{:.0f}'
        }))
        
        # Statistiques par pays
        st.subheader("🌍 Statistiques par Pays")
        st.dataframe(stats['par_pays'])
        
        # Visualisations
        st.subheader("📊 Visualisations")
        
        tab1, tab2, tab3 = st.tabs(["Incidents par Modèle", "Retours par Pays", "Durée d'Installation"])
        
        with tab1:
            st.bar_chart(stats['par_modele']['nombre_incidents'])
        
        with tab2:
            st.bar_chart(stats['par_pays']['nombre_retours'])
        
        with tab3:
            st.bar_chart(stats['par_modele']['duree_moyenne_installation'])
        
        # Produits problématiques
        st.subheader("⚠️ Produits avec Incidents mais sans Retour")
        problematic = df_final[df_final['a_incident_sans_retour']]
        st.dataframe(problematic[['modèle', 'no de série', 'filiale', 'nombre_incidents', 'dernière connexion']])
        
else:
    st.info("Veuillez télécharger un fichier Excel contenant les 3 feuilles : feuille1 (installations), feuille2 (incidents), feuille3 (retours)")
