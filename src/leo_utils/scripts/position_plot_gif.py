import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pathlib import Path
import json
import re

# --- Paths --- adjust to point at your scripts folder
script_dir = Path(__file__).parent

matrix_rss  = np.load(script_dir / "rss_position_matrix.npy")
matrix_yama = np.load(script_dir / "yamauchi_position_matrix.npy")
matrix_gao  = np.load(script_dir / "gao_position_matrix.npy")
display_map  = np.load(script_dir / "display_map.npy")

COMBO_IDX = 8
STEP = 3  # subsample factor, same as original

# Colors: 3 shades per mode (light, mid, dark)
MODE_COLORS = {
    'Yamauchi': ['#6baed6', '#2171b5', '#08306b'],
    'Gao':      ['#74c476', '#238b45', '#00441b'],
    'RSS':      ['#fc8d59', '#d7301f', '#7f0000'],
}
MODE_NAMES = ['Yamauchi', 'Gao', 'RSS']
MATRICES   = [matrix_yama, matrix_gao, matrix_rss]


def get_combo_meta(json_path, run_index):
    with open(json_path) as f:
        data = json.load(f)
    entry = data[run_index]
    router_x = entry['router_x']
    router_y  = entry['router_y']
    match = re.search(r'bx([-\d.]+)_by([-\d.]+)', entry['bag_name'])
    robot_x = float(match.group(1))
    robot_y = float(match.group(2))
    return (robot_x, robot_y), (router_x, router_y)


def load_trajectories(matrix, combo_idx, step=STEP):
    """Return list of 3 (x, y) arrays for the three runs of this combo."""
    runs = [combo_idx * 3 + r for r in range(3)]
    trajs = []
    for r in runs:
        x = matrix[r, ::step, 0]
        y = matrix[r, ::step, 1]
        trajs.append((x, y))
    return trajs


def main():
    first_run = COMBO_IDX * 3
    start, router = get_combo_meta(script_dir / "yamauchi_position_meta.json", first_run)

    # Load all trajectories
    all_trajs = [load_trajectories(m, COMBO_IDX) for m in MATRICES]

    # Max length across all runs and modes
    max_len = max(len(x) for trajs in all_trajs for x, _ in trajs)

    # --- Figure setup ---
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.patch.set_facecolor('white')
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.01, wspace=0.05)

    # Static elements per panel
    for ax, name in zip(axes, MODE_NAMES):
        ax.imshow(display_map, origin='lower', cmap='gray_r',
                  vmin=0, vmax=100, extent=[-20, 20, -20, 20])
        ax.plot(*start,  marker='o', color='black', markersize=12, zorder=5)
        ax.plot(*router, marker='*', color='gold',  markersize=20,
                markeredgecolor='black', zorder=5)
        ax.set_aspect('equal')
        ax.set_xlim(-20, 20)
        ax.set_ylim(-20, 20)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(name, fontsize=16, fontweight='bold')

    # Pre-create line and dot artists for each run in each panel
    lines = []   # lines[mode][run]
    dots  = []   # dots[mode][run]

    for mode_idx, (ax, name) in enumerate(zip(axes, MODE_NAMES)):
        mode_lines = []
        mode_dots  = []
        colors = MODE_COLORS[name]
        for run_idx in range(3):
            ln, = ax.plot([], [], color=colors[run_idx], linewidth=2.0, zorder=3)
            dt, = ax.plot([], [], marker='o', color=colors[run_idx],
                          markersize=10, zorder=4)
            mode_lines.append(ln)
            mode_dots.append(dt)
        lines.append(mode_lines)
        dots.append(mode_dots)

    def init():
        for mode_idx in range(3):
            for run_idx in range(3):
                lines[mode_idx][run_idx].set_data([], [])
                dots[mode_idx][run_idx].set_data([], [])
        return [l for ml in lines for l in ml] + [d for md in dots for d in md]

    def update(frame):
        for mode_idx, trajs in enumerate(all_trajs):
            for run_idx, (x, y) in enumerate(trajs):
                end = min(frame + 1, len(x))
                lines[mode_idx][run_idx].set_data(x[:end], y[:end])
                final = end - 1  # always last drawn point
                dots[mode_idx][run_idx].set_data([x[final]], [y[final]])
        return [l for ml in lines for l in ml] + [d for md in dots for d in md]

    ani = animation.FuncAnimation(
        fig, update, frames=max_len,
        init_func=init, blit=True, interval=30  # ~33 fps
    )

    out_path = script_dir / f"combo_{COMBO_IDX}_animation.gif"
    ani.save(out_path, writer='pillow', fps=30, dpi=100)
    print(f"Saved: {out_path}")
    plt.close()


if __name__ == "__main__":
    main()