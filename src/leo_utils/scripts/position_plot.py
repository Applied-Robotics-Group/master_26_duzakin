import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
import re


script_dir = Path(__file__).parent

matrix_rss  = np.load(script_dir / "rss_position_matrix.npy")
matrix_yama = np.load(script_dir / "yamauchi_position_matrix.npy")
matrix_gao = np.load(script_dir / "gao_position_matrix.npy")
display_map = np.load(script_dir / "display_map.npy")

matrices = [matrix_yama, matrix_gao, matrix_rss]


def get_combo_from_index(json_path, index):
    with open(json_path) as f:
        data = json.load(f)
    entry = data[index]
    
    router_x = entry['router_x']
    router_y = entry['router_y']
    
    match = re.search(r'bx([-\d.]+)_by([-\d.]+)', entry['bag_name'])
    robot_x = float(match.group(1))
    robot_y = float(match.group(2))
    
    return {
        'start': (robot_x, robot_y),
        'router': (router_x, router_y),
        'xlim': (-20, 20),
        'ylim': (-20, 20)
    }

from matplotlib.collections import LineCollection
def plot_combo(axes, combo_idx, row_idx=0):
    colors = ['red', 'green', 'blue']
    mode_names = ['Yamauchi', 'Gao', 'RSS']
    linestyles = ['-', '--', ':']

    run = [combo_idx * 3, combo_idx * 3 + 1, combo_idx * 3 + 2]
    combo = get_combo_from_index(script_dir / "yamauchi_position_meta.json", run[0])

    for col_idx, (matrix, color, name) in enumerate(zip(matrices, colors, mode_names)):
        ax = axes[row_idx, col_idx] if axes.ndim == 2 else axes[col_idx]
        ax.imshow(display_map, origin='lower', cmap='gray_r', vmin=0, vmax=100, extent=[-20, 20, -20, 20])

        color_ranges = [(0.2, 0.5), (0.4, 0.7), (0.6, 1.0)]  # light, medium, dark

        for r, ls, crange in zip(run, linestyles, color_ranges):
            x = matrix[r, :, 0]
            y = matrix[r, :, 1]
            step = 10
            x = x[::step]
            y = y[::step]
            points = np.array([x, y]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            n = len(segments)
            colors_grad = plt.get_cmap(f"{color.capitalize()}s")(np.linspace(crange[0], crange[1], n))
            lc = LineCollection(segments, colors=colors_grad, linewidth=2.0, linestyle=ls)
            ax.add_collection(lc)

        ax.plot(*combo['start'], marker='o', color='black', markersize=14)
        ax.plot(*combo['router'], marker='*', color='gold', markersize=20, markeredgecolor='black')
        ax.set_aspect('equal')
        ax.set_xlim(combo['xlim'])
        ax.set_ylim(combo['ylim'])
        ax.set_xticks([])
        ax.set_yticks([])
        if col_idx == 0:
            ax.set_title(f"{combo_idx}", fontsize=16, fontweight='bold', loc='left', pad=6)

def main():
    combos_per_page = 4
    all_combos = list(range(24))
    pages = [all_combos[i:i+combos_per_page] for i in range(0, len(all_combos), combos_per_page)]

    # 6 appendix pages
    for page_idx, page_combos in enumerate(pages):
        fig, axes = plt.subplots(len(page_combos), 3, figsize=(18, 6 * len(page_combos)))

        for row_idx, combo_idx in enumerate(page_combos):
            plot_combo(axes, combo_idx, row_idx)

        plt.tight_layout(h_pad=2.0)
        plt.savefig(script_dir / f"appendix_page_{page_idx + 1}.png", bbox_inches='tight', dpi=150)
        plt.close()
        print(f"Saved page {page_idx + 1}")

    # highlighted combo 16
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    plot_combo(axes, 16)

    plt.tight_layout()
    plt.savefig(script_dir / "highlight_combo_16.png", bbox_inches='tight', dpi=150)
    plt.close()
    print("Saved highlight combo 16")


if __name__ == "__main__":
    main()