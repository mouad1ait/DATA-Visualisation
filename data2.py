import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def main():
    st.title("Analyse des appareils")
    
    # Upload du fichier
    uploaded_file = st.file_uploader("Choisir un fichier Excel", type=['xlsx'])
    
    if uploaded_file:
        # Lecture et prétraitement
        df = pd.read_excel(uploaded_file)
        
        # Section prétraitement
        st.header("Prétraitement des données")
        
        # Conversion des dates
        date_cols = ['installationDate', 'date de désinstallation', 'dernière connexion']
        for col in date_cols:
            df[col] = pd.to_datetime(df[col])
            df[f'{col}_formaté'] = df[col].dt.strftime('%d/%m/%Y')
        
        # Validation SN
        df['SN_année'] = df['SN'].str[2:4].astype(int) + 2000
        df['SN_valide'] = (df['SN_année'] >= 2017) & (df['SN_année'] <= 2030)
        
        st.write("Données après prétraitement:", df)
        
        # Section analyse
        st.header("Analyse des données")
        
        # Graphique 1: Répartition des modèles
        st.subheader("Répartition des modèles")
        fig1, ax1 = plt.subplots()
        df['modèle'].value_counts().plot(kind='bar', ax=ax1)
        st.pyplot(fig1)
        
        # Graphique 2: Appareils valides/invalides
        st.subheader("Validité des numéros de série")
        fig2, ax2 = plt.subplots()
        df['SN_valide'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax2)
        st.pyplot(fig2)
        
        # Graphique 3: Evolution des installations
        st.subheader("Installations par année")
        df['année_installation'] = df['installationDate'].dt.year
        fig3, ax3 = plt.subplots()
        df['année_installation'].value_counts().sort_index().plot(kind='line', ax=ax3)
        st.pyplot(fig3)

if __name__ == "__main__":
    main()
