import matplotlib as mpl, matplotlib.pyplot as plt
OKABE = {'Raw feed': '#0072B2', 'Constant shift': '#E69F00', 'ETSY': '#CC79A7', 'ELASTIC': '#009E73'}
MARK = {'Raw feed': 'o', 'Constant shift': 's', 'ETSY': 'D', 'ELASTIC': '^'}
INK, MUTED, GRID = '#222222', '#666666', '#E9E9E9'
def style():
    mpl.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 7.5, 'axes.titlesize': 8, 'axes.labelsize': 7.5,
        'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#888888',
        'axes.linewidth': 0.6, 'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.labelcolor': INK,
        'text.color': INK, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.5,
        'legend.frameon': False, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.03,
        'pdf.fonttype': 42, 'ps.fonttype': 42, 'xtick.major.size': 2.5, 'ytick.major.size': 2.5})
def panel(ax, letter):
    ax.text(-0.02, 1.04, letter, transform=ax.transAxes, fontsize=9, fontweight='bold', ha='right', va='bottom')
