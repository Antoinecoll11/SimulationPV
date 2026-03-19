import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
from scipy.interpolate import PchipInterpolator
import plotly.graph_objects as go
import streamlit.components.v1 as components



# 1. TOUJOURS LA CONFIGURATION DE LA PAGE EN PREMIER !
st.set_page_config(page_title="Simulateur PV", layout="wide")








# ==========================================
# --- EN-TÊTE DE L'APPLICATION AVEC IMAGE ---
# ==========================================
col1, col2 = st.columns([3, 1]) # Crée 2 colonnes (la 1ère plus grande pour le texte)

with col1:
    st.title("Simulateur Photovoltaïque & Stockage")
    st.markdown("""
    Analysez votre production, votre consommation et l'impact d'une batterie.
    Optimisez votre taux d'autoconsommation en un clic !
    """)

with col2:
    # Affiche la photo de panneau
    try:
        st.image("panneau.jpg", use_container_width=True)
    except Exception as e:
        pass # Si l'image n'est pas trouvée, l'appli continue sans planter

st.divider() # Ajoute une belle ligne grise de séparation







# ==========================================
# --- CRÉATION DES ONGLETS ---
# ==========================================
tab_import, tab_saisons, tab_mensuel, tab_annuel = st.tabs([
    "Import & Paramètres", 
    "Profils Journaliers", 
    "Bilan Mensuel", 
    "Résumé Annuel"
])

donnees_conso = None
profil_choisi = None






# ==========================================
# ONGLET 1 : IMPORT ET PARAMÈTRES
# ==========================================
with tab_import:
    st.sidebar.image("logo.jpg", use_container_width=True)
    st.header("Paramètres du projet")
    puissance_crete = st.number_input("Puissance Crête à installer (kWc)", min_value=0.0, value=10.0, step=0.1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Production Solaire")
        fichier_prod = st.file_uploader("Importez le CSV SolarEdge", type=['csv'], key="prod")
        
    with col2:
        st.subheader("Source de Consommation")
        mode_conso = st.radio("Choix de la méthode :", 
                             ["Profils types (Fichier CSV)", "Calculateur personnalisé (Tableau)"])

    # --- INITIALISATION DES VARIABLES ---
    profil_24h_custom = np.zeros(24)

    # --- CHARGEMENT ET CALCUL DE LA CONSO ---
    try:
        if mode_conso == "Profils types (Fichier CSV)":
            donnees_conso = pd.read_csv('consommation.csv', sep=";", decimal=",")
            choix_profils = [col for col in donnees_conso.columns if col.lower() != "date" and "unnamed" not in col.lower()]
            
            st.success("Fichier de profils détecté !")
            profil_choisi = st.selectbox("Choisissez le profil à simuler :", choix_profils)
            
            conso_col = pd.to_numeric(donnees_conso[profil_choisi], errors='coerce').fillna(0)
            dates_apercu = pd.date_range(start='2024-01-01', periods=len(donnees_conso), freq='h')
            
            y_jour = conso_col.groupby(dates_apercu.hour).mean()
            y_mois = conso_col.groupby(dates_apercu.month).sum() / 1000
            total_kwh = conso_col.sum() / 1000

        else:
            # --- MODE PERSONNALISÉ ---
            st.info("💡 Ajoutez vos appareils. Horaires : '8-10' ou '12-13;19-21'")
            default_devices = [
                {"Appareil": "Talon (Veilles, Box, Frigo)", "Puissance (W)": 150, "Horaires": "0-24", "Actif": True},
                {"Appareil": "Éclairage & Prises", "Puissance (W)": 300, "Horaires": "7-9;18-23", "Actif": True},
                {"Appareil": "Lave-Linge", "Puissance (W)": 2000, "Horaires": "14-16", "Actif": True},
                {"Appareil": "Plaques Cuisson", "Puissance (W)": 1500, "Horaires": "12-13;19-20", "Actif": True},
            ]
            df_custom = st.data_editor(pd.DataFrame(default_devices), num_rows="dynamic", use_container_width=True)
            
            def parse_h(h_str):
                p = np.zeros(24)
                try:
                    for b in str(h_str).split(';'):
                        d, f = map(int, b.split('-'))
                        p[d:f] = 1
                except: pass
                return p

            for _, row in df_custom.iterrows():
                if row["Actif"]:
                    profil_24h_custom += parse_h(row["Horaires"]) * row["Puissance (W)"]
            
            y_jour = pd.Series(profil_24h_custom)
            jours_mois = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            y_mois = pd.Series([(y_jour.sum() * j / 1000) for j in jours_mois], index=range(1, 13))
            total_kwh = y_mois.sum()
            profil_choisi = "Sur Mesure"

        # --- AFFICHAGE COMMUN DES GRAPHES ---
        st.markdown("---")
        st.subheader(f"Aperçu : {profil_choisi} (Total : {total_kwh:,.0f} kWh)".replace(',', ' '))
        
        # On ajoute les metrics pour le mode personnalisé
        if mode_conso == "Calculateur personnalisé (Tableau)":
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Annuel", f"{total_kwh:,.0f} kWh".replace(",", " "))
            c2.metric("Puissance Max", f"{profil_24h_custom.max():,.0f} W")
            c3.metric("Conso / Jour", f"{(profil_24h_custom.sum()/1000):.1f} kWh")

        fig_apercu, (ax_jour, ax_mois) = plt.subplots(1, 2, figsize=(14, 4))
        ax_jour.plot(y_jour.index, y_jour.values, color='#1565C0', linewidth=2.5)
        ax_jour.fill_between(y_jour.index, y_jour.values, color='#1565C0', alpha=0.2)
        ax_jour.set_title("Modèle sur un jour type")
        ax_jour.set_xticks(range(0, 24, 2))
        ax_jour.grid(True, linestyle='--', alpha=0.6)
        
        mois_noms = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        ax_mois.bar(mois_noms, y_mois.values, color='#FF9800', edgecolor='black', alpha=0.8)
        ax_mois.set_title("Consommation Mensuelle Totale")
        ax_mois.grid(axis='y', linestyle='--', alpha=0.6)
        
        plt.tight_layout()
        st.pyplot(fig_apercu)

    except Exception as e:
        st.error(f"Erreur : {e}")

# --- BARRIÈRE DE SÉCURITÉ ---
if fichier_prod is None:
    st.info("Veuillez importer le fichier de production SolarEdge pour voir le reste de la simulation.")
    st.stop()

# ==========================================
# 1. CHARGEMENT ET NETTOYAGE PRINCIPAL
# ==========================================
fichier_prod.seek(0) 
donnees_prod = pd.read_csv(fichier_prod, sep=",", skiprows=[1], index_col=False)

# ... (Ton code de nettoyage Date&Time identique) ...
donnees_prod = donnees_prod[donnees_prod['Date&Time'].astype(str).str.contains('-', na=False)]
donnees_prod['Date&Time'] = donnees_prod['Date&Time'].astype(str) + " 2024"
donnees_prod['Date&Time'] = pd.to_datetime(donnees_prod['Date&Time'], format='%d-%b %H:%M:%S %Y', errors='coerce')




mon_tableau = donnees_prod[['Date&Time', 'Inverter Output']].copy()
mon_tableau['Inverter Output'] = pd.to_numeric(mon_tableau['Inverter Output'], errors='coerce').fillna(0)



augmentation_prod_pct = st.sidebar.number_input(
    "Augmentation de la production (%)",
    min_value=0.0,
    value=0.0,
    step=1.0
)




facteur_augmentation_prod = 1 + augmentation_prod_pct / 100
mon_tableau['Inverter Output'] = mon_tableau['Inverter Output'] * facteur_augmentation_prod




# --- L'ARBITRAGE CRUCIAL ---
if mode_conso == "Calculateur personnalisé (Tableau)":
    conso_base = np.tile(profil_24h_custom, len(mon_tableau) // 24 + 1)[:len(mon_tableau)]
    mon_tableau['Consumption'] = conso_base
else:
    if donnees_conso is not None and profil_choisi is not None:
        valeurs_conso = pd.to_numeric(donnees_conso[profil_choisi], errors='coerce').fillna(0).values
        mon_tableau['Consumption'] = valeurs_conso[:len(mon_tableau)]
    else:
        mon_tableau['Consumption'] = 0.0




# ==========================================
# 2. CALCULS 
# ==========================================
mon_tableau['Autoconsommation'] = np.minimum(mon_tableau['Inverter Output'], mon_tableau['Consumption'])
mon_tableau['Import_Reseau'] = np.maximum(0, mon_tableau['Consumption'] - mon_tableau['Inverter Output'])
mon_tableau['Export_Reseau'] = np.maximum(0, mon_tableau['Inverter Output'] - mon_tableau['Consumption'])











# ==========================================
# 2. CALCULS (AVEC BATTERIE)
# ==========================================

st.sidebar.markdown("---")
st.sidebar.subheader("Stockage (Batterie)")


# ==========================================
# AJUSTEMENT DE LA PRODUCTION PV
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("Évolution de la production PV")










# 1. On charge la base de données Excel
try:
    df_batteries = pd.read_excel('batteries.xlsx')
    # On enlève les lignes vides (comme ton module Fronius sans puissance)
    df_batteries = df_batteries.dropna(subset=['Energie util', 'P charge / décharge'])
except Exception as e:
    st.sidebar.error("Fichier batteries.xlsx introuvable. Placez-le dans le dossier.")
    df_batteries = pd.DataFrame() # DataFrame vide pour éviter les plantages

activer_batterie = st.sidebar.checkbox("Activer la simulation de batterie", value=False)

# On prépare nos variables par défaut (à zéro)
capa_wh = 0.0
puiss_w = 0.0

if activer_batterie and not df_batteries.empty:
    # 2. Le menu déroulant avec la colonne 'Référence' de ton Excel
    liste_batteries = df_batteries['Référence'].tolist()
    choix_batterie = st.sidebar.selectbox("Choisissez un modèle :", liste_batteries)

    # 3. On récupère la ligne Excel qui correspond au choix
    infos_batterie = df_batteries[df_batteries['Référence'] == choix_batterie].iloc[0]

    # 4. On extrait la capacité et la puissance (et on gère les virgules françaises si besoin)
    capa_kwh = float(str(infos_batterie['Energie util']).replace(',', '.'))
    puiss_kw = float(str(infos_batterie['P charge / décharge']).replace(',', '.'))

    # Affichage des infos dans la barre latérale
    st.sidebar.info(f"Capacité : {capa_kwh:.2f} kWh\n Puissance Max : {puiss_kw:.2f} kW")

    # On convertit en Wh et W pour notre algorithme
    capa_wh = capa_kwh * 1000
    puiss_w = puiss_kw * 1000

# L'algorithme de la batterie (la fonction)
def simuler_batterie(production_wh, consommation_wh, capacite_max_wh, puissance_max_w):
    niveau_actuel = 0.0
    niveaux, charges, decharges, exports, achats = [], [], [], [], []

    for prod, conso in zip(production_wh, consommation_wh):
        autoconso_directe = min(prod, conso)
        surplus = prod - autoconso_directe
        manque = conso - autoconso_directe
        
        charge, decharge, export, achat = 0.0, 0.0, 0.0, 0.0

        if surplus > 0:
            charge = min(surplus, puissance_max_w, capacite_max_wh - niveau_actuel)
            niveau_actuel += charge
            export = surplus - charge
        elif manque > 0:
            decharge = min(manque, puissance_max_w, niveau_actuel)
            niveau_actuel -= decharge
            achat = manque - decharge

        niveaux.append(niveau_actuel)
        charges.append(charge)
        decharges.append(decharge)
        exports.append(export)
        achats.append(achat)

    return niveaux, charges, decharges, exports, achats

# --- APPLICATION DES CALCULS SUR LE TABLEAU ---
mon_tableau['Autoconso_Directe'] = np.minimum(mon_tableau['Inverter Output'], mon_tableau['Consumption'])

if activer_batterie and capa_wh > 0:
    # On fait tourner l'algorithme avec les données dynamiques sélectionnées
    niveaux, charges, decharges, exports, achats = simuler_batterie(
        mon_tableau['Inverter Output'].values, 
        mon_tableau['Consumption'].values, 
        capacite_max_wh=capa_wh, 
        puissance_max_w=puiss_w
    )
    mon_tableau['Niveau_Batterie'] = niveaux
    mon_tableau['Charge_Batterie'] = charges
    mon_tableau['Decharge_Batterie'] = decharges 
    mon_tableau['Export_Reseau'] = exports
    mon_tableau['Import_Reseau'] = achats
    mon_tableau['Autoconsommation'] = mon_tableau['Autoconso_Directe'] + mon_tableau['Decharge_Batterie']
else:
    # Comportement classique sans batterie
    mon_tableau['Decharge_Batterie'] = 0.0
    mon_tableau['Autoconsommation'] = mon_tableau['Autoconso_Directe']
    mon_tableau['Import_Reseau'] = np.maximum(0, mon_tableau['Consumption'] - mon_tableau['Inverter Output'])
    mon_tableau['Export_Reseau'] = np.maximum(0, mon_tableau['Inverter Output'] - mon_tableau['Consumption'])








# ==========================================
# 3. AFFICHAGES GRAPHIQUES
# ==========================================

# ==========================================
# ONGLET 2 : LES 4 SAISONS (PROFILS JOURNALIERS)
# ==========================================
with tab_saisons:
    st.header("Analyse des 4 Saisons")
    
    st.markdown("**Sélectionnez les courbes à afficher :**")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    afficher_prod = col1.checkbox("Production", value=True)
    afficher_conso = col2.checkbox("Consommation", value=True)
    afficher_auto = col3.checkbox("Autoconsommation", value=False)
    afficher_import = col4.checkbox("Importé (Réseau)", value=False)
    afficher_export = col5.checkbox("Exporté (Réseau)", value=False)

    fig1, axes = plt.subplots(2, 2, figsize=(14, 8))
    
    dates_a_tracer = [
        (12, 21, "21 Décembre (Hiver)", axes[0,0]), 
        (3, 21, "21 Mars (Printemps)", axes[0,1]), 
        (6, 15, "15 Juin (Été)", axes[1,0]), 
        (9, 15, "15 Septembre (Automne)", axes[1,1])
    ]

    handles_globaux = []
    labels_globaux = []

    for mois, jour, titre, ax in dates_a_tracer:
        journee = mon_tableau[(mon_tableau['Date&Time'].dt.month == mois) & (mon_tableau['Date&Time'].dt.day == jour)]
        
        # --- LA MOULINETTE DE LISSAGE ---
        # 1. On traduit les heures en chiffres pour les maths
        x_dates = journee['Date&Time']
        x_num = mdates.date2num(x_dates)
        
        # 2. On crée 300 points pour rendre la courbe très fluide
        x_dense_num = np.linspace(x_num.min(), x_num.max(), 300)
        x_dense_dates = mdates.num2date(x_dense_num)

        # 3. La petite fonction magique qui arrondit SANS faire de vagues
        def lisser_courbe(y_vals):
            # On utilise Pchip au lieu de spline pour éviter les faux rebonds
            lisseur = PchipInterpolator(x_num, y_vals)
            return np.clip(lisseur(x_dense_num), 0, None)
        # --- TRACÉ DES COURBES LISSÉES ---
        if afficher_prod:
            ax.plot(x_dense_dates, lisser_courbe(journee['Inverter Output']), label='Production', color='#FFD700', linewidth=2.5)
        if afficher_conso:
            ax.plot(x_dense_dates, lisser_courbe(journee['Consumption']), label='Consommation', color='#2196F3', linewidth=2.5)
        if afficher_auto:
            ax.fill_between(x_dense_dates, lisser_courbe(journee['Autoconsommation']), label='Autoconsommation', color='#4CAF50', alpha=0.5)
        if afficher_import:
            ax.plot(x_dense_dates, lisser_courbe(journee['Import_Reseau']), label='Importé (Réseau)', color='#F44336', linewidth=2, linestyle='--')
        if afficher_export:
            ax.plot(x_dense_dates, lisser_courbe(journee['Export_Reseau']), label='Exporté (Réseau)', color='#FF9800', linewidth=2, linestyle='--')
            
        ax.set_title(titre)
        ax.set_ylabel('Énergie (Wh)')
        ax.grid(True, linestyle='--', alpha=0.6)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
        ax.tick_params(axis='x', rotation=45)
        
        if mois == 12 and jour == 21:
            handles_globaux, labels_globaux = ax.get_legend_handles_labels()

    plt.tight_layout()
    
    if handles_globaux:
        fig1.legend(handles_globaux, labels_globaux, loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=5, fontsize=11)
        fig1.subplots_adjust(top=0.88)

    st.pyplot(fig1, use_container_width=False)








# ------------------------------------------
# ONGLET 3 : LE BILAN MENSUEL
# ------------------------------------------
with tab_mensuel:
    st.header("Bilan Énergétique Mensuel")
    
    # --- LES CASES À COCHER (Avec des 'key' uniques pour ne pas bugger) ---
    st.markdown("**Sélectionnez les données à afficher dans les histogrammes :**")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    aff_m_prod = col1.checkbox("Prod Totale", value=True, key="m_prod")
    aff_m_conso = col2.checkbox("Conso Totale", value=True, key="m_conso")
    aff_m_auto = col3.checkbox("Autoconsommation", value=True, key="m_auto")
    aff_m_import = col4.checkbox("Importé (Réseau)", value=True, key="m_import")
    aff_m_export = col5.checkbox("Exporté (Réseau)", value=True, key="m_export")

    # Calculs mensuels
    bilan_mensuel = mon_tableau.groupby(mon_tableau['Date&Time'].dt.month)[
        ['Consumption', 'Inverter Output', 'Autoconsommation', 'Import_Reseau', 'Export_Reseau']
    ].sum() / 1000  

    mois_noms = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
    x = np.arange(len(mois_noms))
    largeur = 0.35 

    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # ==========================================
    # GRAPHIQUE 1 : LA CONSOMMATION (À GAUCHE)
    # ==========================================
    if aff_m_conso:
        ax1.bar(x - largeur/2, bilan_mensuel['Consumption'], largeur, label='Conso Totale', color='lightgray', edgecolor='black')
    
    # L'astuce mathématique : si Autoconso est décoché, la barre rouge démarre au sol (à 0)
    base_import = bilan_mensuel['Autoconsommation'] if aff_m_auto else 0
    
    if aff_m_auto:
        ax1.bar(x + largeur/2, bilan_mensuel['Autoconsommation'], largeur, label='Solaire (Autoconso)', color='#8BC34A')
    if aff_m_import:
        ax1.bar(x + largeur/2, bilan_mensuel['Import_Reseau'], largeur, bottom=base_import, label='Réseau (Achat)', color='#F44336')
        
    ax1.set_title("D'où vient l'énergie consommée ?")
    ax1.set_ylabel("Énergie (kWh)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(mois_noms)
    # On n'affiche la légende que s'il y a au moins une courbe de cochée
    if aff_m_conso or aff_m_auto or aff_m_import:
        ax1.legend()
    ax1.grid(axis='y', linestyle='--', alpha=0.7)


    # ==========================================
    # GRAPHIQUE 2 : LA PRODUCTION (À DROITE)
    # ==========================================
    if aff_m_prod:
        ax2.bar(x - largeur/2, bilan_mensuel['Inverter Output'], largeur, label='Prod Totale', color='#FFD700', edgecolor='black')
    
    # L'astuce mathématique : si Autoconso est décoché, la barre orange démarre au sol (à 0)
    base_export = bilan_mensuel['Autoconsommation'] if aff_m_auto else 0
    
    if aff_m_auto:
        ax2.bar(x + largeur/2, bilan_mensuel['Autoconsommation'], largeur, label='Maison (Autoconso)', color='#8BC34A')
    if aff_m_export:
        ax2.bar(x + largeur/2, bilan_mensuel['Export_Reseau'], largeur, bottom=base_export, label='Réseau (Vente)', color='#FF9800')
        
    ax2.set_title("Où va l'énergie produite ?")
    ax2.set_ylabel("Énergie (kWh)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(mois_noms)
    if aff_m_prod or aff_m_auto or aff_m_export:
        ax2.legend()
    ax2.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    st.pyplot(fig2, use_container_width=False)










# ------------------------------------------
# ONGLET 4 : LE BILAN ANNUEL
# ------------------------------------------

with tab_annuel:
    st.header("Flux d'Énergie Annuel")

    # =========================
    # 1. CALCULS
    # =========================
    total_prod = mon_tableau['Inverter Output'].sum() / 1000
    total_conso = mon_tableau['Consumption'].sum() / 1000
    total_auto = mon_tableau['Autoconsommation'].sum() / 1000
    total_import = mon_tableau['Import_Reseau'].sum() / 1000
    total_export = mon_tableau['Export_Reseau'].sum() / 1000
    total_ess = mon_tableau['Decharge_Batterie'].sum() / 1000
    total_solaire_direct = max(0, total_auto - total_ess)

    taux_autoconso = (total_auto / total_prod * 100) if total_prod > 0 else 0
    taux_autonomie = (total_auto / total_conso * 100) if total_conso > 0 else 0
    taux_batterie = (total_ess / total_conso * 100) if total_conso > 0 else 0
    taux_reseau = (total_import / total_conso * 100) if total_conso > 0 else 0

    if 'capa_wh' in locals() and capa_wh > 0:
        nombre_cycles = total_ess / (capa_wh / 1000)
        soc_moyen = (mon_tableau['Niveau_Batterie'].mean() / capa_wh * 100)
        soc_moyen = max(0, min(100, soc_moyen))
    else:
        nombre_cycles = 0
        soc_moyen = 0

    batterie_active = total_ess > 0.1

    # =========================
    # 2. FONCTIONS SVG
    # =========================
    def polar_to_cartesian(cx, cy, r, angle_deg):
        import math
        angle_rad = math.radians(angle_deg - 90)
        return cx + r * math.cos(angle_rad), cy + r * math.sin(angle_rad)

    def donut_arc(cx, cy, r, pct, color, bg="#E6E6E6", stroke=16):
        pct = max(0, min(100, pct))
        start_x, start_y = polar_to_cartesian(cx, cy, r, 0)
        end_x, end_y = polar_to_cartesian(cx, cy, r, pct * 3.6)
        large_arc = 1 if pct > 50 else 0

        bg_circle = (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" '
            f'stroke="{bg}" stroke-width="{stroke}" fill="none" />'
        )

        if pct <= 0:
            fg_arc = ""
        elif pct >= 99.999:
            fg_arc = (
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'stroke="{color}" stroke-width="{stroke}" fill="none" '
                f'stroke-linecap="butt" />'
            )
        else:
            fg_arc = (
                f'<path d="M {start_x:.2f} {start_y:.2f} '
                f'A {r} {r} 0 {large_arc} 1 {end_x:.2f} {end_y:.2f}" '
                f'stroke="{color}" stroke-width="{stroke}" fill="none" '
                f'stroke-linecap="butt" />'
            )
        return bg_circle + fg_arc

    def add_segment(cx, cy, r, start_pct, seg_pct, color, stroke=16):
        if seg_pct <= 0:
            return ""

        start_angle = start_pct * 3.6
        end_angle = (start_pct + seg_pct) * 3.6

        x1, y1 = polar_to_cartesian(cx, cy, r, start_angle)
        x2, y2 = polar_to_cartesian(cx, cy, r, end_angle)
        large_arc = 1 if seg_pct > 50 else 0

        if seg_pct >= 99.999:
            return (
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'stroke="{color}" stroke-width="{stroke}" fill="none" />'
            )

        return (
            f'<path d="M {x1:.2f} {y1:.2f} '
            f'A {r} {r} 0 {large_arc} 1 {x2:.2f} {y2:.2f}" '
            f'stroke="{color}" stroke-width="{stroke}" fill="none" />'
        )

    # =========================
    # 3. COULEURS
    # =========================
    c_pv = "#FFAE00"
    c_batt = "#2B9930"
    c_grid = "#957CC5"
    c_direct = "#F5A623"
    c_text = "#303030"
    c_bg = "#FFFFFF"
    c_ring_bg = "#FFF27B"

    # =========================
    # 4. POURCENTAGES
    # =========================
    pv_pct = (total_auto / total_prod * 100) if total_prod > 0 else 0
    grid_pct = (total_import / (total_import + total_export) * 100) if (total_import + total_export) > 0 else 0
    batt_pct = soc_moyen if batterie_active else 0

    direct_pct_charge = (total_solaire_direct / total_conso * 100) if total_conso > 0 else 0
    batt_pct_charge = (total_ess / total_conso * 100) if total_conso > 0 else 0
    grid_pct_charge = (total_import / total_conso * 100) if total_conso > 0 else 0


    pv_injection_pct = (total_export / total_prod * 100) if total_prod > 0 else 0
    pv_auto_pct = (total_auto / total_prod * 100) if total_prod > 0 else 0

    batt_soc_pct = batt_pct
    grid_import_pct_total = grid_pct

    # =========================
    # 5. GÉOMÉTRIE
    # =========================
    W = 1000
    H = 560
    x=40

    pv_x, pv_y = 500, 105+x
    batt_x, batt_y = 205-50, 315-70+x
    load_x, load_y = 500, 355+50+x
    grid_x, grid_y = 795+50, 315-70+x

    r_main = 68
    r_side = 58

    svg_parts = []

    # fond
    svg_parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{c_bg}" rx="18"/>')

    # =========================
    # 6. CONNEXIONS
    # =========================
    svg_parts.append(f'''
        <path d="M {pv_x} {pv_y + 85} L {pv_x} {load_y - 85}"
            stroke="{c_direct}" stroke-width="4" fill="none" stroke-linecap="round"
            marker-end="url(#arrow-direct)"/>
    ''')

    if batterie_active:
        svg_parts.append(f'''
            <path d="M {pv_x - 72} {pv_y + 42}
                    L {batt_x + 78} {batt_y - 30}"
                stroke="{c_batt}" stroke-width="4" fill="none"
                stroke-linecap="round" stroke-linejoin="round"
                marker-end="url(#arrow-batt)"/>
        ''')

        svg_parts.append(f'''
            <path d="M {batt_x + 78} {batt_y + 30}
                    L {load_x - 72} {load_y - 42}"
                stroke="{c_batt}" stroke-width="4" fill="none"
                stroke-linecap="round" stroke-linejoin="round"
                marker-end="url(#arrow-batt)"/>
        ''')

    svg_parts.append(f'''
        <path d="M {pv_x + 72} {pv_y + 42}
                L {grid_x - 78} {grid_y - 30}"
            stroke="{c_grid}" stroke-width="4" fill="none"
            stroke-linecap="round" stroke-linejoin="round"
            marker-end="url(#arrow-grid)"/>
    ''')

    svg_parts.append(f'''
        <path d="M {grid_x - 78} {grid_y + 30}
                L {load_x + 72} {load_y - 42}"
            stroke="{c_grid}" stroke-width="4" fill="none"
            stroke-linecap="round" stroke-linejoin="round"
            marker-end="url(#arrow-grid)"/>
    ''')


    # =========================
    # 7. DONUT PV
    # =========================
    svg_parts.append(donut_arc(pv_x, pv_y, r_main, pv_pct, c_pv, bg=c_ring_bg, stroke=16))
    svg_parts.append(f'''
        <text x="{pv_x}" y="{pv_y - 92}" text-anchor="middle" font-size="22" font-weight="700" fill="{c_text}">PV</text>
        <text x="{pv_x}" y="{pv_y - 4}" text-anchor="middle" font-size="30">☀️</text>
        <text x="{pv_x}" y="{pv_y + 22}" text-anchor="middle" font-size="18" fill="{c_text}">{total_prod:,.0f} kWh</text>
    '''.replace(",", " "))
    svg_parts.append(f'''
    <text x="{pv_x + 92}" y="{pv_y - 8-50}" text-anchor="start" font-size="15" font-weight="600" fill="{c_grid}">
        Injection : {pv_injection_pct:.1f}%
    </text>
    <text x="{pv_x + 92}" y="{pv_y + 16-50}" text-anchor="start" font-size="15" font-weight="600" fill="{c_direct}">
        Direct : {pv_auto_pct:.1f}%
    </text>
    '''.replace(",", " "))

    # =========================
    # 8. DONUT BATTERIE
    # =========================
    if batterie_active:
        svg_parts.append(donut_arc(batt_x, batt_y, r_side, batt_pct, c_batt, bg="#E5EFE5", stroke=13))
        svg_parts.append(f'''
            <text x="{batt_x}" y="{batt_y + 4}" text-anchor="middle" font-size="28">🔋</text>
            <text x="{batt_x}" y="{batt_y + 28}" text-anchor="middle" font-size="17" fill="{c_text}">{total_ess:,.0f} kWh</text>
            <text x="{batt_x}" y="{batt_y + 94}" text-anchor="middle" font-size="18" font-weight="700" fill="{c_text}">Batterie</text>
        '''.replace(",", " "))



    # =========================
    # 9. DONUT RÉSEAU
    # =========================
    svg_parts.append(donut_arc(grid_x, grid_y, r_side, grid_pct, c_grid, bg="#EEE6F5", stroke=13))
    svg_parts.append(f'''
        <text x="{grid_x}" y="{grid_y + 4}" text-anchor="middle" font-size="28">⚡</text>
        <text x="{grid_x}" y="{grid_y + 28}" text-anchor="middle" font-size="17" fill="{c_text}">{total_import:,.0f} kWh</text>
        <text x="{grid_x}" y="{grid_y + 94}" text-anchor="middle" font-size="18" font-weight="700" fill="{c_text}">Réseau</text>
    '''.replace(",", " "))

    # =========================
    # 10. DONUT CHARGE - consommation
    # =========================
    svg_parts.append(
        f'<circle cx="{load_x}" cy="{load_y}" r="{r_main}" '
        f'stroke="{c_ring_bg}" stroke-width="16" fill="none" />'
    )

    start = 0
    svg_parts.append(add_segment(load_x, load_y, r_main, start, direct_pct_charge, c_direct, stroke=16))
    start += direct_pct_charge

    if batterie_active:
        svg_parts.append(add_segment(load_x, load_y, r_main, start, batt_pct_charge, c_batt, stroke=16))
        start += batt_pct_charge

    svg_parts.append(add_segment(load_x, load_y, r_main, start, grid_pct_charge, c_grid, stroke=16))

    svg_parts.append(f'''
        <text x="{load_x}" y="{load_y - 2}" text-anchor="middle" font-size="30">🏠</text>
        <text x="{load_x}" y="{load_y + 24}" text-anchor="middle" font-size="18" fill="{c_text}">{total_conso:,.0f} kWh</text>
        <text x="{load_x}" y="{load_y + 96}" text-anchor="middle" font-size="18" font-weight="700" fill="{c_text}">Consommation</text>
    '''.replace(",", " "))


    svg_parts.append(f'''
    <text x="{load_x + 95}" y="{load_y - 22+50}" text-anchor="start" font-size="15" font-weight="600" fill="{c_batt}">
        Batterie : {batt_pct_charge:.1f}%
    </text>
    <text x="{load_x + 95}" y="{load_y + 2+50}" text-anchor="start" font-size="15" font-weight="600" fill="{c_direct}">
        PV : {direct_pct_charge:.1f}%
    </text>
    <text x="{load_x + 95}" y="{load_y + 26+50}" text-anchor="start" font-size="15" font-weight="600" fill="{c_grid}">
        Réseau : {grid_pct_charge:.1f}%
    </text>
    '''.replace(",", " "))

# =========================
# 11. TEXTES DE FLUX
# =========================
    svg_parts.append(f'''
        <text x="{pv_x + 10}" y="292" font-size="15" fill="{c_direct}">{total_solaire_direct:,.0f} kWh</text>
        <text x="650" y="200" font-size="15" fill="{c_grid}">{total_export:,.0f} kWh</text>
    '''.replace(",", " "))

    if batterie_active:
        svg_parts.append(f'''
            <text x="285" y="390" font-size="15" fill="{c_batt}">{total_ess:,.0f} kWh</text>
        '''.replace(",", " "))
    svg_parts.append(f'''
        <text x="652" y="390" font-size="15" fill="{c_grid}">{total_import:,.0f} kWh</text>
    '''.replace(",", " "))

    # =========================
    # 12. AFFICHAGE HTML / SVG
    # =========================
    svg_html = f"""
    <div style="width:100%; display:flex; justify-content:center; padding:8px 0 0 0;">
        <svg viewBox="0 0 {W} {H}" style="width:100%; max-width:1000px; height:auto;">
            <defs>
                <marker id="arrow-direct" markerWidth="10" markerHeight="10" refX="6.5" refY="3"
                        orient="auto" markerUnits="strokeWidth">
                    <path d="M0,0 L0,6 L8,3 z" fill="{c_direct}" />
                </marker>

                <marker id="arrow-batt" markerWidth="10" markerHeight="10" refX="6.5" refY="3"
                        orient="auto" markerUnits="strokeWidth">
                    <path d="M0,0 L0,6 L8,3 z" fill="{c_batt}" />
                </marker>

                <marker id="arrow-grid" markerWidth="10" markerHeight="10" refX="6.5" refY="3"
                        orient="auto" markerUnits="strokeWidth">
                    <path d="M0,0 L0,6 L8,3 z" fill="{c_grid}" />
                </marker>
            </defs>

            {''.join(svg_parts)}
        </svg>
    </div>
    """

    components.html(svg_html, height=600)

    # =========================
    # 13. KPI DU BAS
    # =========================
    st.divider()
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Taux autoconso", f"{taux_autoconso:.1f}%")
    c2.metric("Taux autonomie", f"{taux_autonomie:.1f}%")
    c3.metric("Solaire direct", f"{total_solaire_direct:,.0f} kWh".replace(",", " "))
    c4.metric("Via batterie", f"{total_ess:,.0f} kWh".replace(",", " "))
    c5.metric("Importé", f"{total_import:,.0f} kWh".replace(",", " "))
    c6.metric("Cycles / an", f"{nombre_cycles:.0f}")









with tab_annuel:
    # ==========================================
    # TABLEAU DE VÉRIFICATION HORAIRE
    # ==========================================
    tableau_verification = pd.DataFrame()

    tableau_verification['Date&Time'] = mon_tableau['Date&Time']
    tableau_verification['Consommation_Wh'] = mon_tableau['Consumption']
    tableau_verification['Production_Wh'] = mon_tableau['Inverter Output']
    tableau_verification['Autoconsommation_Wh'] = mon_tableau['Autoconsommation']
    tableau_verification['Import_Reseau_Wh'] = mon_tableau['Import_Reseau']
    tableau_verification['Export_Reseau_Wh'] = mon_tableau['Export_Reseau']

    # Colonnes batterie si elles existent
    if 'Charge_Batterie' in mon_tableau.columns:
        tableau_verification['Charge_Batterie_Wh'] = mon_tableau['Charge_Batterie']
    else:
        tableau_verification['Charge_Batterie_Wh'] = 0.0

    if 'Decharge_Batterie' in mon_tableau.columns:
        tableau_verification['Decharge_Batterie_Wh'] = mon_tableau['Decharge_Batterie']
    else:
        tableau_verification['Decharge_Batterie_Wh'] = 0.0

    if 'Niveau_Batterie' in mon_tableau.columns:
        tableau_verification['Niveau_Batterie_Wh'] = mon_tableau['Niveau_Batterie']
    else:
        tableau_verification['Niveau_Batterie_Wh'] = 0.0

    # Capacité batterie identique sur toutes les lignes pour rappel
    tableau_verification['Capacite_Batterie_Wh'] = capa_wh if 'capa_wh' in locals() else 0.0

    # Optionnel : niveau batterie en %
    if 'capa_wh' in locals() and capa_wh > 0:
        tableau_verification['Niveau_Batterie_%'] = (tableau_verification['Niveau_Batterie_Wh'] / capa_wh) * 100
    else:
        tableau_verification['Niveau_Batterie_%'] = 0.0

    # Arrondir pour lecture plus propre
    colonnes_a_arrondir = [
        'Consommation_Wh',
        'Production_Wh',
        'Autoconsommation_Wh',
        'Import_Reseau_Wh',
        'Export_Reseau_Wh',
        'Charge_Batterie_Wh',
        'Decharge_Batterie_Wh',
        'Niveau_Batterie_Wh',
        'Capacite_Batterie_Wh',
        'Niveau_Batterie_%'
    ]

    for col in colonnes_a_arrondir:
        tableau_verification[col] = tableau_verification[col].round(2)

    st.divider()
    st.subheader("Tableau horaire de vérification")

    st.markdown("Ce tableau permet de contrôler heure par heure les flux énergétiques calculés.")

    # Affichage du tableau
    st.dataframe(tableau_verification, use_container_width=True, height=400)

    # Export CSV
    csv_verification = tableau_verification.to_csv(index=False, sep=';').encode('utf-8-sig')

    st.download_button(
        label="Télécharger le tableau de vérification (CSV)",
        data=csv_verification,
        file_name="tableau_verification_horaire.csv",
        mime="text/csv",
        key="download_verification_csv"
    )