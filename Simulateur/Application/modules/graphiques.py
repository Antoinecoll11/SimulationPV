import matplotlib.pyplot as plt

def generer_schema_flux(total_prod, total_conso, total_auto, total_import, total_export, taux_autoconso, taux_injection):
    """Génère le graphique de flux énergétique annuel."""
    fig = plt.figure(figsize=(12, 7))
    
    # Calque invisible anti-zoom
    ax_main = fig.add_axes([0, 0, 1, 1])
    ax_main.axis('off') 
    ax_main.set_xlim(0, 1)
    ax_main.set_ylim(0, 1)

    # Zones des cercles
    ax_pv = fig.add_axes([0.40, 0.65, 0.20, 0.20])
    ax_grid = fig.add_axes([0.15, 0.15, 0.20, 0.20])
    ax_conso = fig.add_axes([0.65, 0.15, 0.20, 0.20])

    # PV
    ax_pv.pie([total_auto, total_export] if total_prod > 0 else [1], 
              colors=['#8BC34A', '#2E7D32'] if total_prod > 0 else ['#E0E0E0'], 
              startangle=90, wedgeprops=dict(width=0.3, edgecolor='w'))
    ax_pv.text(0, 0, f"PV\n{total_prod:,.0f} kWh".replace(',', ' '), ha='center', va='center', fontsize=12, fontweight='bold')

    # Réseau
    ax_grid.pie([1], colors=['#9E9E9E'], startangle=90, wedgeprops=dict(width=0.3, edgecolor='w'))
    ax_grid.text(0, 0, "Réseau", ha='center', va='center', fontsize=12, fontweight='bold', color='white')

    # Conso
    ax_conso.pie([total_auto, total_import] if total_conso > 0 else [1], 
                 colors=['#FF9800', '#FFE0B2'] if total_conso > 0 else ['#E0E0E0'], 
                 startangle=90, wedgeprops=dict(width=0.3, edgecolor='w'))
    ax_conso.text(0, 0, f"Conso\n{total_conso:,.0f} kWh".replace(',', ' '), ha='center', va='center', fontsize=12, fontweight='bold')

    # Flèches
    if total_export > 0:
        ax_main.annotate("", xy=(0.35, 0.35), xytext=(0.42, 0.62), arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.1", color="#2E7D32", lw=3))
        ax_main.text(0.28, 0.50, f"Vente\n{total_export:,.0f} kWh".replace(',', ' '), ha='center', color="#2E7D32", fontweight='bold')
    
    if total_auto > 0:
        ax_main.annotate("", xy=(0.65, 0.35), xytext=(0.58, 0.62), arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.1", color="#8BC34A", lw=3))
        ax_main.text(0.72, 0.50, f"Autoconso\n{total_auto:,.0f} kWh".replace(',', ' '), ha='center', color="#8BC34A", fontweight='bold')

    if total_import > 0:
        ax_main.annotate("", xy=(0.62, 0.25), xytext=(0.38, 0.25), arrowprops=dict(arrowstyle="->", color="#F44336", lw=3))
        ax_main.text(0.50, 0.30, f"Achat\n{total_import:,.0f} kWh".replace(',', ' '), ha='center', color="#F44336", fontweight='bold')

    return fig