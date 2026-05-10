import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

script_dir = Path(__file__).parent

matrix_rss  = np.load(script_dir / "rss_position_matrix.npy")
matrix_yama = np.load(script_dir / "yamauchi_position_matrix.npy")
matrix_gao = np.load(script_dir / "gao_position_matrix.npy")
display_map = np.load(script_dir / "display_map.npy")

fig, ax = plt.subplots(figsize=(8, 8))

ax.imshow(display_map, origin='lower', cmap='gray_r', vmin=0, vmax=100,
          extent=[-20, 20, -20, 20])

x = matrix_rss[49, :, 0]
y = matrix_rss[49, :, 1]
ax.scatter(x, y, c=np.arange(len(x)), cmap='Blues', s=6, vmin=-500, vmax=1200)

x = matrix_yama[49, :, 0]
y = matrix_yama[49, :, 1]
ax.scatter(x, y, c=np.arange(len(x)), cmap='Reds', s=6, vmin=-500, vmax=1200)

x = matrix_gao[49, :, 0]
y = matrix_gao[49, :, 1]
ax.scatter(x, y, c=np.arange(len(x)), cmap='Greens', s=6, vmin=-500, vmax=1200)

# Router position
ax.plot(18.0, 18.0, marker='*', color='gold', markersize=15, 
        markeredgecolor='black', markeredgewidth=0.5, label='Router', zorder=5)

# Start position
ax.plot(-19.0, -19.0, marker='^', color='black', markersize=10,
        markeredgecolor='white', markeredgewidth=0.5, label='Start', zorder=5)

ax.legend(loc='upper left')

ax.set_aspect('equal')
ax.set_xlim(-20, 20)
ax.set_ylim(-20, 20)
plt.tight_layout()
plt.show()