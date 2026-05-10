import os
import glob
import json
import numpy as np
import matplotlib.pyplot as plt
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

session_path = "/Volumes/KINGSTON/Lukas Master/Session_final/"

script_dir = os.path.dirname(os.path.abspath(__file__))

META_FILES = [
    "rss_position_meta.json",
    "yamauchi_position_meta.json",
    "gao_position_meta.json",
]


REPROCESS = False  # set to True to re-extract from bags




# Load all meta entries and build bag list
bag_list = []  # list of (bag_path, duration_s)
for meta_file in META_FILES:
    meta_path = os.path.join(script_dir, meta_file)
    if not os.path.exists(meta_path):
        print(f"WARNING: {meta_file} not found, skipping")
        continue
    with open(meta_path) as f:
        meta = json.load(f)
    for m in meta:
        bag_path = os.path.join(session_path, m["folder"], m["bag_name"])
        bag_list.append((bag_path, m["duration_s"]))

# Deduplicate in case a bag appears in multiple meta files
bag_list = list({bp: d for bp, d in bag_list}.items())
print(f"Found {len(bag_list)} unique bags")


def read_last_map(bag_path, duration_s):
    typestore = get_typestore(Stores.ROS2_FOXY)
    last_msg  = None
    try:
        with Reader(bag_path) as reader:
            connections = [c for c in reader.connections if c.topic == '/map']
            if not connections:
                return None
            # Seek to 10 seconds before end
            start_ns = reader.start_time + int(max(0, duration_s - 10) * 1e9)
            for connection, timestamp, rawdata in reader.messages(
                    connections=connections, start=start_ns):
                msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
                last_msg = msg
    except Exception as e:
        print(f"    WARNING: {os.path.basename(bag_path)}: {e}")
        return None
    return last_msg


def add_map_to_grid(msg, sum_grid, count_grid, world_min, resolution, grid_size):
    origin_x = msg.info.origin.position.x
    origin_y = msg.info.origin.position.y
    res      = msg.info.resolution
    width    = msg.info.width
    height   = msg.info.height
    data     = np.array(msg.data, dtype=np.int8).reshape(height, width)

    cols = np.arange(width)
    rows = np.arange(height)
    grid_cols = ((origin_x + cols * res - world_min) / resolution).astype(int)
    grid_rows = ((origin_y + rows * res - world_min) / resolution).astype(int)

    valid_cols = (grid_cols >= 0) & (grid_cols < grid_size)
    valid_rows = (grid_rows >= 0) & (grid_rows < grid_size)

    gc  = grid_cols[valid_cols]
    gr  = grid_rows[valid_rows]
    sub = data[np.ix_(valid_rows, valid_cols)]
    known = sub != -1

    gr_idx, gc_idx = np.where(known)
    np.add.at(sum_grid,   (gr[gr_idx], gc[gc_idx]), sub[known])
    np.add.at(count_grid, (gr[gr_idx], gc[gc_idx]), 1)


def main():
    REPROCESS          = False
    FREE_THRESHOLD     = 15
    OCCUPIED_THRESHOLD = 15

    RESOLUTION = 0.05
    WORLD_MIN  = -20.0
    WORLD_MAX  =  20.0
    GRID_SIZE  = int((WORLD_MAX - WORLD_MIN) / RESOLUTION)

    map_path   = os.path.join(script_dir, "composite_map.npy")
    count_path = os.path.join(script_dir, "composite_count.npy")

    if REPROCESS or not os.path.exists(map_path):
        print("Extracting from bags...")
        N_BAGS = None
        bags_to_use = bag_list[:N_BAGS] if N_BAGS else bag_list

        sum_grid   = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        count_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)

        for i, (bag_path, duration_s) in enumerate(bags_to_use):
            print(f"  {i+1}/{len(bags_to_use)}: {os.path.basename(bag_path)}")
            msg = read_last_map(bag_path, duration_s)
            if msg is None:
                continue
            add_map_to_grid(msg, sum_grid, count_grid, WORLD_MIN, RESOLUTION, GRID_SIZE)

        avg_grid = np.full((GRID_SIZE, GRID_SIZE), -1, dtype=np.float32)
        known = count_grid > 0
        avg_grid[known] = sum_grid[known] / count_grid[known]

        np.save(map_path, avg_grid)
        np.save(count_path, count_grid)
        print("Saved composite_map.npy and composite_count.npy")
    else:
        print("Loading cached map...")
        avg_grid = np.load(map_path)

    known = avg_grid != -1

    display_grid = avg_grid.copy()
    display_grid[known & (avg_grid < FREE_THRESHOLD)]     = 0
    display_grid[known & (avg_grid > OCCUPIED_THRESHOLD)] = 100
    display_grid[~known] = -1

    # Save for later use
    np.save(os.path.join(script_dir, "display_map.npy"), display_grid)

    # Save as image
    plt.imsave(os.path.join(script_dir, "display_map.png"), display_grid, origin='lower', cmap='gray_r', vmin=0, vmax=100)

    plt.figure(figsize=(8, 8))
    plt.imshow(display_grid, origin='lower', cmap='gray_r', vmin=0, vmax=100)
    plt.title('Composite occupancy map')
    plt.show()


if __name__ == '__main__':
    main()