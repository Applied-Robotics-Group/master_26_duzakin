# import csv
# from collections import defaultdict

# csv_path = "/Users/lukasderia/Desktop/metrics.csv"  # hardcoded

# counts = defaultdict(lambda: {"router_found": 0, "timeout": 0, "flip": 0})

# with open(csv_path, newline="") as f:
#     reader = csv.reader(f)
#     next(reader)  # skip header
#     for row in reader:
#         mode = row[1].strip().lower()
#         version = row[2].strip()
#         result = row[9].strip().lower()
#         if mode == "rss" and version != "4":
#             continue
#         if result in ("router_found", "timeout", "flip"):
#             counts[mode][result] += 1
#         else:
#             print(f"  Unknown result value: '{result}'")

# print(f"\n{'Mode':<12} {'Total':>6} {'Useful':>7} {'Flips':>6} {'Flips/Useful':>13}")
# print("-" * 48)

# for mode in ("yamauchi", "gao", "rss"):
#     d = counts[mode]
#     useful = d["router_found"] + d["timeout"]
#     flips = d["flip"]
#     total = useful + flips
#     ratio = flips / useful if useful > 0 else float("nan")
#     print(f"{mode:<12} {total:>6} {useful:>7} {flips:>6} {ratio:>13.2f}")

# print()
# for mode in ("yamauchi", "gao", "rss"):
#     d = counts[mode]
#     print(f"{mode}: {d['router_found']} success, {d['timeout']} timeout, {d['flip']} flip")



    ### Map size check ###

# import csv
# from collections import defaultdict
# import numpy as np

# csv_path = "/Users/lukasderia/Desktop/metrics.csv"  # hardcoded

# # Store successful runs per mode: combo_id -> list of map sizes
# successes = defaultdict(lambda: defaultdict(list))

# with open(csv_path, newline="") as f:
#     reader = csv.reader(f)
#     next(reader)  # skip header
#     for row in reader:
#         mode    = row[1].strip().lower()
#         version = row[2].strip()
#         combo   = row[3].strip()
#         success = row[10].strip().lower()
#         mapsize = row[13].strip()

#         # filter rss to version 4 only
#         if mode == "rss" and version != "4":
#             continue

#         if success in ("yes", "true", "1"):
#             try:
#                 successes[mode][combo].append(float(mapsize))
#             except ValueError:
#                 print(f"  Could not parse map size '{mapsize}' for {mode} combo {combo}")

# # find combos where all three strategies had at least one success
# yamauchi_combos = set(successes["yamauchi"].keys())
# gao_combos      = set(successes["gao"].keys())
# rss_combos      = set(successes["rss"].keys())
# shared_combos   = yamauchi_combos & gao_combos & rss_combos

# print(f"Yamauchi succeeded on {len(yamauchi_combos)} unique combos")
# print(f"Gao      succeeded on {len(gao_combos)} unique combos")
# print(f"RSS      succeeded on {len(rss_combos)} unique combos")
# print(f"Shared (all three succeeded): {len(shared_combos)} combos")
# print(f"Shared combos: {sorted(shared_combos, key=int)}\n")

# # collect map sizes for shared combos only
# map_sizes = {"yamauchi": [], "gao": [], "rss": []}
# for combo in shared_combos:
#     for mode in ("yamauchi", "gao", "rss"):
#         map_sizes[mode].extend(successes[mode][combo])

# print(f"{'Mode':<12} {'n':>4} {'Mean (m²)':>10} {'Median (m²)':>12} {'Std':>8}")
# print("-" * 50)
# for mode in ("yamauchi", "gao", "rss"):
#     sizes = map_sizes[mode]
#     print(f"{mode:<12} {len(sizes):>4} {np.mean(sizes):>10.1f} {np.median(sizes):>12.1f} {np.std(sizes):>8.1f}")





    ### Gradient and sucess comp ###
import csv
from collections import defaultdict
import numpy as np

csv_path = "/Users/lukasderia/Desktop/metrics.csv"  # hardcoded

# per version: success/timeout/flip counts, and lists of mean/median errors
data = defaultdict(lambda: {
    "router_found": 0, "timeout": 0, "flip": 0,
    "mean_errors": [], "median_errors": [], "gradient_msgs": []
})

with open(csv_path, newline="") as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        mode    = row[1].strip().lower()
        version = row[2].strip()
        result  = row[9].strip().lower()

        if mode != "rss":
            continue
        if version not in ("1", "2", "3", "4"):
            continue

        if result in ("router_found", "timeout", "flip"):
            data[version][result] += 1

        # only log errors for useful runs (not flips)
        if result in ("router_found", "timeout"):
            try:
                mean_err   = float(row[21].strip())
                median_err = float(row[22].strip())
                grad_msgs  = int(row[23].strip())
                data[version]["mean_errors"].append(mean_err)
                data[version]["median_errors"].append(median_err)
                data[version]["gradient_msgs"].append(grad_msgs)
            except (ValueError, IndexError):
                pass

print(f"\n{'Ver':>4} {'Total':>6} {'Useful':>7} {'Success%':>9} {'Mean err°':>10} {'Median err°':>12} {'Avg grad msgs':>14}")
print("-" * 68)

for v in ("1", "2", "3", "4"):
    d = data[v]
    useful  = d["router_found"] + d["timeout"]
    flips   = d["flip"]
    total   = useful + flips
    success_pct = d["router_found"] / useful * 100 if useful > 0 else float("nan")
    mean_err    = np.mean(d["mean_errors"])   if d["mean_errors"]   else float("nan")
    median_err  = np.mean(d["median_errors"]) if d["median_errors"] else float("nan")
    avg_msgs    = np.mean(d["gradient_msgs"]) if d["gradient_msgs"] else float("nan")
    print(f"RSS-{v:>1} {total:>6} {useful:>7} {success_pct:>8.1f}% {mean_err:>10.2f} {median_err:>12.2f} {avg_msgs:>14.1f}")

print()
for v in ("1", "2", "3", "4"):
    d = data[v]
    print(f"RSS-{v}: {d['router_found']} success, {d['timeout']} timeout, {d['flip']} flip")