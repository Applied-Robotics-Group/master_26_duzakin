#!/usr/bin/env python3
"""
extract_positions.py  —  Extract robot trajectories into position matrices.

Uses the same run selection as progression_sampling.py (first_indices,
MAX_RUNS per combination), then filters to router_found only.

Requires progression_meta JSON files to already exist next to this script.

Output: yamauchi_position_matrix.npy, gao_position_matrix.npy,
        rss_position_matrix.npy  — shape (n_runs, 1200, 2), NaN-padded.

Usage:
    python3 extract_positions.py <session_root_path>
"""

import sys, os, json, re
import numpy as np

try:
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore
except ImportError:
    print("ERROR: rosbags not found.  pip install rosbags")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

SAMPLE_HZ      = 2
MAX_DURATION   = 600.0
N_COLS         = int(SAMPLE_HZ * MAX_DURATION)   # 1200
MAX_RUNS       = 3                                # must match progression_sampling.py
SKIP_REASONS = {"flip"}

# mode -> which progression meta file to load
META_FILES = {
    "yamauchi": "yamauchi_progression_meta.json",
    "gao":      "gao_progression_meta.json",
    "rss":      "rss_4_progression_meta.json",
}

# ── Run selection (identical logic to progression_sampling.py) ────────────────

def parse_combo_key(bag_name):
    rx = re.search(r'rx(-?[0-9.]+)', bag_name)
    ry = re.search(r'ry(-?[0-9.]+)', bag_name)
    bx = re.search(r'bx(-?[0-9.]+)', bag_name)
    by = re.search(r'by(-?[0-9.]+)', bag_name)
    if rx and ry and bx and by:
        return (float(rx.group(1)), float(ry.group(1)),
                float(bx.group(1)), float(by.group(1)))
    return (None, None, None, None)

def first_indices(meta):
    combos = {}
    for i, m in enumerate(meta):
        key = parse_combo_key(m["bag_name"])
        if key == (None, None, None, None):
            key = (m["router_x"], m["router_y"])
        combos.setdefault(key, []).append(i)
    selected = []
    for key, indices in sorted(combos.items()):
        selected.extend(indices[:MAX_RUNS])
    return selected

# ── TF helpers (identical to progression_sampling.py) ────────────────────────

def quat_to_mat(q):
    x, y, z, w = q
    return np.array([
        [1-2*(y*y+z*z),   2*(x*y-w*z),   2*(x*z+w*y)],
        [  2*(x*y+w*z), 1-2*(x*x+z*z),   2*(y*z-w*x)],
        [  2*(x*z-w*y),   2*(y*z+w*x), 1-2*(x*x+y*y)],
    ])

def compose_transforms(t1_xyz, q1, t2_xyz, q2):
    R1    = quat_to_mat(q1)
    R2    = quat_to_mat(q2)
    t_out = R1 @ np.array(t2_xyz) + np.array(t1_xyz)
    R_out = R1 @ R2
    tr    = R_out[0,0] + R_out[1,1] + R_out[2,2]
    if tr > 0:
        s = 0.5 / np.sqrt(tr + 1.0)
        w = 0.25 / s
        x = (R_out[2,1] - R_out[1,2]) * s
        y = (R_out[0,2] - R_out[2,0]) * s
        z = (R_out[1,0] - R_out[0,1]) * s
    else:
        w, x, y, z = 1, 0, 0, 0
    return t_out, np.array([x, y, z, w])

def read_tf(bag_path):
    typestore = get_typestore(Stores.ROS2_FOXY)
    results   = []
    try:
        with Reader(bag_path) as reader:
            connections = [c for c in reader.connections if c.topic == '/tf']
            if not connections:
                return []
            for connection, timestamp, rawdata in reader.messages(connections=connections):
                msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
                results.append((timestamp, msg))
    except Exception as e:
        print(f"    WARNING: failed to read bag ({e})")
        return []
    return results

def extract_robot_trajectory(tf_messages):
    map_odom, odom_base = [], []
    for ts, msg in tf_messages:
        for tf in msg.transforms:
            p = tf.transform.translation
            r = tf.transform.rotation
            entry = (ts, p.x, p.y, p.z, r.x, r.y, r.z, r.w)
            if tf.header.frame_id == 'map' and tf.child_frame_id == 'odom':
                map_odom.append(entry)
            elif tf.header.frame_id == 'odom' and tf.child_frame_id == 'base_link':
                odom_base.append(entry)

    if not map_odom or not odom_base:
        return np.array([]).reshape(0, 3)

    map_odom.sort(key=lambda x: x[0])
    odom_base.sort(key=lambda x: x[0])
    mo_ts = np.array([e[0] for e in map_odom])

    trajectory = []
    for ob in odom_base:
        ts  = ob[0]
        idx = min(np.searchsorted(mo_ts, ts), len(map_odom) - 1)
        mo  = map_odom[idx]
        t_out, _ = compose_transforms(
            [mo[1], mo[2], mo[3]], [mo[4], mo[5], mo[6], mo[7]],
            [ob[1], ob[2], ob[3]], [ob[4], ob[5], ob[6], ob[7]],
        )
        trajectory.append((ts / 1e9, t_out[0], t_out[1]))

    trajectory.sort(key=lambda x: x[0])
    return np.array(trajectory)

# ── Position row builder ──────────────────────────────────────────────────────

def build_position_row(bag_path):
    tf_messages = read_tf(bag_path)
    if not tf_messages:
        return None
    trajectory = extract_robot_trajectory(tf_messages)
    if len(trajectory) < 2:
        return None

    t_raw        = trajectory[:, 0] - trajectory[0, 0]
    duration     = t_raw[-1]
    sample_times = np.arange(0, min(duration, MAX_DURATION), 1.0 / SAMPLE_HZ)
    n_samples    = len(sample_times)

    row = np.full((N_COLS, 2), np.nan)
    row[:n_samples, 0] = np.interp(sample_times, t_raw, trajectory[:, 1])
    row[:n_samples, 1] = np.interp(sample_times, t_raw, trajectory[:, 2])
    return row

# ── Per-mode extraction ───────────────────────────────────────────────────────

def extract_mode(session_root, mode, meta_file, out_dir):
    npy_path = os.path.join(out_dir, f"{mode}_position_matrix.npy")

    if os.path.exists(npy_path):
        matrix = np.load(npy_path)
        print(f"  [{mode}] Cache found — {matrix.shape[0]} runs loaded.")
        return matrix

    meta_path = os.path.join(out_dir, meta_file)
    if not os.path.exists(meta_path):
        print(f"  [{mode}] ERROR: meta file not found: {meta_path}")
        print(f"           Run progression_sampling.py first.")
        return None

    with open(meta_path) as f:
        meta = json.load(f)

    # Same selection as progression plots
    selected = first_indices(meta)
    # Then filter to successful runs only
    selected = [i for i in selected if meta[i]["termination"] not in SKIP_REASONS]

    print(f"  [{mode}] {len(selected)} successful runs selected (from {len(meta)} in meta)")

    rows, skipped = [], 0
    for i in selected:
        m        = meta[i]
        bag_path = os.path.join(session_root, m["folder"], m["bag_name"])
        if not os.path.isdir(bag_path):
            print(f"    WARNING: bag not found: {bag_path}")
            skipped += 1
            continue
        row = build_position_row(bag_path)
        if row is None:
            print(f"    WARNING: could not extract trajectory from {m['bag_name']}")
            skipped += 1
            continue
        rows.append(row)

    if not rows:
        print(f"  [{mode}] ERROR: no valid runs extracted.")
        return None

    matrix = np.stack(rows)   # (n_runs, 1200, 2)
    np.save(npy_path, matrix)
    print(f"  [{mode}] Saved {len(rows)} runs (skipped {skipped}). Shape: {matrix.shape}")
    return matrix

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    session_root = sys.argv[1].rstrip('/')
    if not os.path.isdir(session_root):
        print(f"ERROR: not found: {session_root}")
        sys.exit(1)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"\n── Position extraction  ({SAMPLE_HZ} Hz, {N_COLS} cols, {SKIP_REASONS} only)")
    print(f"   Session root : {session_root}")
    print(f"   Script dir   : {out_dir}\n")

    for mode, meta_file in META_FILES.items():
        extract_mode(session_root, mode, meta_file, out_dir)

    print("\nDone.")

if __name__ == '__main__':
    main()