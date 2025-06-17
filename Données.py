import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from datetime import datetime

class ExcelVisualizationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualisation de Données Excel")
        self.root.geometry("1200x800")
        
        # Variables
        self.df = None
        self.filtered_df = None
        
        # Création des widgets
        self.create_widgets()
        
    def create_widgets(self):
        # Frame pour les contrôles
        control_frame = ttk.LabelFrame(self.root, text="Contrôles", padding=(10, 5))
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Bouton pour charger le fichier
        ttk.Button(control_frame, text="Charger Fichier Excel", command=self.load_file).pack(side=tk.LEFT, padx=5)
        
        # Filtres
        ttk.Label(control_frame, text="Filtres:").pack(side=tk.LEFT, padx=5)
        
        # Filtre par modèle
        self.model_var = tk.StringVar()
        ttk.Label(control_frame, text="Modèle:").pack(side=tk.LEFT, padx=5)
        self.model_cb = ttk.Combobox(control_frame, textvariable=self.model_var, state='readonly')
        self.model_cb.pack(side=tk.LEFT, padx=5)
        self.model_cb.bind('<<ComboboxSelected>>', self.apply_filters)
        
        # Filtre par filiale
        self.filiale_var = tk.StringVar()
        ttk.Label(control_frame, text="Filiale:").pack(side=tk.LEFT, padx=5)
        self.filiale_cb = ttk.Combobox(control_frame, textvariable=self.filiale_var, state='readonly')
        self.filiale_cb.pack(side=tk.LEFT, padx=5)
        self.filiale_cb.bind('<<ComboboxSelected>>', self.apply_filters)
        
        # Filtre par année
        self.year_var = tk.StringVar()
        ttk.Label(control_frame, text="Année:").pack(side=tk.LEFT, padx=5)
        self.year_cb = ttk.Combobox(control_frame, textvariable=self.year_var, state='readonly')
        self.year_cb.pack(side=tk.LEFT, padx=5)
        self.year_cb.bind('<<ComboboxSelected>>', self.apply_filters)
        
        # Bouton pour réinitialiser les filtres
        ttk.Button(control_frame, text="Réinitialiser", command=self.reset_filters).pack(side=tk.LEFT, padx=5)
        
        # Bouton pour exporter
        ttk.Button(control_frame, text="Exporter Données", command=self.export_data).pack(side=tk.RIGHT, padx=5)
        
        # Frame pour les visualisations
        viz_frame = ttk.Frame(self.root)
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Notebook pour les différents onglets
        self.notebook = ttk.Notebook(viz_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet Tableau de données
        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text="Données")
        
        # Treeview pour afficher les données
        self.tree = ttk.Treeview(self.table_frame)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Onglet Statistiques
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistiques")
        
        # Canvas pour les graphiques
        self.stats_canvas = tk.Canvas(self.stats_frame)
        self.stats_canvas.pack(fill=tk.BOTH, expand=True)
        
    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Fichiers Excel", "*.xlsx *.xls")])
        if not file_path:
            return
            
        try:
            # Charger le fichier Excel
            self.df = pd.read_excel(file_path)
            
            # Vérifier les colonnes
            required_columns = ['modèle', 'no de série', 'référence de pays', 'filiale', 
                              'date d\'installation', 'dernière connexion', 'incident', 'date d\'incident']
            
            if not all(col in self.df.columns for col in required_columns):
                messagebox.showerror("Erreur", "Les colonnes dans le fichier Excel ne correspondent pas aux attentes.")
                return
            
            # Nettoyer et préparer les données
            self.prepare_data()
            
            # Mettre à jour les filtres
            self.update_filters()
            
            # Afficher les données
            self.display_data()
            
            # Afficher les statistiques
            self.display_stats()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le fichier: {str(e)}")
    
    def prepare_data(self):
        # Convertir les dates
        self.df['date d\'installation'] = pd.to_datetime(self.df['date d\'installation'])
        self.df['date d\'incident'] = pd.to_datetime(self.df['date d\'incident'])
        self.df['dernière connexion'] = pd.to_datetime(self.df['dernière connexion'])
        
        # Calculer la différence entre date d'incident et date d'installation
        self.df['différence jours'] = (self.df['date d\'incident'] - self.df['date d\'installation']).dt.days
        
        # Extraire l'année du numéro de série
        self.df['année'] = self.df['no de série'].str[2:4].astype(int) + 2000
        
        # Appliquer les filtres initiaux
        self.filtered_df = self.df.copy()
    
    def update_filters(self):
        # Mettre à jour les options des filtres
        models = ['Tous'] + sorted(self.df['modèle'].unique().tolist())
        self.model_cb['values'] = models
        self.model_var.set('Tous')
        
        filiales = ['Tous'] + sorted(self.df['filiale'].unique().tolist())
        self.filiale_cb['values'] = filiales
        self.filiale_var.set('Tous')
        
        years = ['Tous'] + sorted(self.df['année'].unique().astype(str).tolist())
        self.year_cb['values'] = years
        self.year_var.set('Tous')
    
    def apply_filters(self, event=None):
        if self.df is None:
            return
            
        self.filtered_df = self.df.copy()
        
        # Appliquer le filtre par modèle
        if self.model_var.get() != 'Tous':
            self.filtered_df = self.filtered_df[self.filtered_df['modèle'] == self.model_var.get()]
        
        # Appliquer le filtre par filiale
        if self.filiale_var.get() != 'Tous':
            self.filtered_df = self.filtered_df[self.filtered_df['filiale'] == self.filiale_var.get()]
        
        # Appliquer le filtre par année
        if self.year_var.get() != 'Tous':
            self.filtered_df = self.filtered_df[self.filtered_df['année'] == int(self.year_var.get())]
        
        # Mettre à jour l'affichage
        self.display_data()
        self.display_stats()
    
    def reset_filters(self):
        if self.df is None:
            return
            
        self.model_var.set('Tous')
        self.filiale_var.set('Tous')
        self.year_var.set('Tous')
        self.filtered_df = self.df.copy()
        self.display_data()
        self.display_stats()
    
    def display_data(self):
        # Effacer l'affichage précédent
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Configurer les colonnes
        self.tree["columns"] = list(self.filtered_df.columns)
        for col in self.filtered_df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.W)
        
        # Ajouter les données
        for _, row in self.filtered_df.iterrows():
            self.tree.insert("", tk.END, values=list(row))
    
    def display_stats(self):
        # Effacer le canvas précédent
        for widget in self.stats_canvas.winfo_children():
            widget.destroy()
        
        if self.filtered_df.empty:
            return
            
        # Créer une figure matplotlib
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        plt.subplots_adjust(hspace=0.5)
        
        # Graphique 1: Pourcentage par modèle
        model_counts = self.filtered_df['modèle'].value_counts()
        model_percent = model_counts / model_counts.sum() * 100
        model_percent.plot.pie(autopct='%1.1f%%', ax=axes[0, 0])
        axes[0, 0].set_title('Répartition par Modèle')
        
        # Graphique 2: Pourcentage par filiale
        filiale_counts = self.filtered_df['filiale'].value_counts()
        filiale_percent = filiale_counts / filiale_counts.sum() * 100
        filiale_percent.plot.pie(autopct='%1.1f%%', ax=axes[0, 1])
        axes[0, 1].set_title('Répartition par Filiale')
        
        # Graphique 3: Distribution des différences de jours
        sns.histplot(self.filtered_df['différence jours'], bins=20, kde=True, ax=axes[1, 0])
        axes[1, 0].set_title('Distribution des Jours entre Incident et Installation')
        axes[1, 0].set_xlabel('Jours')
        
        # Graphique 4: Nombre d'incidents par année
        sns.countplot(data=self.filtered_df, x='année', ax=axes[1, 1])
        axes[1, 1].set_title('Nombre d\'Incidents par Année')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Intégrer la figure dans Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.stats_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def export_data(self):
        if self.filtered_df is None or self.filtered_df.empty:
            messagebox.showwarning("Avertissement", "Aucune donnée à exporter")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Fichier Excel", "*.xlsx"), ("Tous les fichiers", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Calculer les statistiques supplémentaires
            stats_df = pd.DataFrame({
                'Statistique': ['Nombre total', 'Modèle le plus courant', 'Filiale la plus courante', 
                               'Différence moyenne (jours)', 'Différence médiane (jours)'],
                'Valeur': [
                    len(self.filtered_df),
                    self.filtered_df['modèle'].mode()[0],
                    self.filtered_df['filiale'].mode()[0],
                    self.filtered_df['différence jours'].mean(),
                    self.filtered_df['différence jours'].median()
                ]
            })
            
            # Exporter vers Excel avec plusieurs onglets
            with pd.ExcelWriter(file_path) as writer:
                self.filtered_df.to_excel(writer, sheet_name='Données', index=False)
                stats_df.to_excel(writer, sheet_name='Statistiques', index=False)
                
                # Ajouter les pourcentages par modèle et filiale
                model_percent = self.filtered_df['modèle'].value_counts(normalize=True) * 100
                model_percent.to_excel(writer, sheet_name='Pourcentages Modèle')
                
                filiale_percent = self.filtered_df['filiale'].value_counts(normalize=True) * 100
                filiale_percent.to_excel(writer, sheet_name='Pourcentages Filiale')
            
            messagebox.showinfo("Succès", f"Données exportées avec succès vers:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'export: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelVisualizationApp(root)
    root.mainloop()
