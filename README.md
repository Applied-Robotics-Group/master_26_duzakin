# Not All Frontiers Are Equal
### Comparing Frontier Selection Strategies Using the Leo Rover

![Hero GIF](media/combo_X_animation.gif)

---

## Overview

This repository implements and compares three frontier-based exploration strategies on a physical mobile robot platform. The robot explores an unknown environment autonomously, and the question is simple: **does it matter how you choose which frontier to explore next?**

The three strategies compared are:
- **Yamauchi** — always go to the nearest frontier
- **Gao** — prefer frontiers aligned with the robot's current heading
- **RSS-guided** — use WiFi signal strength to bias exploration toward a signal source

RSS-guided frontier selection was evaluated against both baselines in simulation across 72 runs per strategy, and validated on a physical robot platform. The results show that signal-aware selection makes a substantial difference — not just in finding the target, but in how deliberately the robot moves toward it.

This work is the result of a master's thesis at the University of Oslo (2026). The full thesis is available [here](link_to_thesis).

---

## The Platform

![Leo Rover](media/leo_rover.png)

| Component | Model |
|---|---|
| Mobile robot | Leo Rover 1.8 |
| LiDAR | Velodyne VLP-16 |
| Onboard computer | Raspberry Pi 4 |
| Edge computer | Jetson Orin Nano 8GB |
| WiFi adapter | Alfa AWUS036ACS |
| Signal source | TP-Link WR840N router |

---

## How It Works

![Software Pipeline](media/software_pipeline.png)

The system runs a continuous loop: the LiDAR feeds point cloud data into SLAM Toolbox, which produces an occupancy map and pose estimate. Frontier cells — boundaries between known free space and unknown space — are detected and clustered. Each frontier is scored according to the active strategy, and the highest-scoring frontier is sent to Nav2 as the next navigation goal.

The key difference between strategies is the scoring function. RSS-guided selection adds a fourth term: alignment with the estimated WiFi gradient direction, pointing toward the signal source.

---

## Results

### Exploration Behaviour

The animations below show three runs per strategy for the same starting configuration. Yamauchi (blue) and Gao (green) explore without directional bias. RSS (red) consistently moves toward the target.

| Yamauchi | Gao | RSS |
|---|---|---|
| ![Combo A](media/combo_A_animation.gif) | ![Combo B](media/combo_B_animation.gif) | ![Combo C](media/combo_C_animation.gif) |

> Each panel shows 3 runs in different shades. The filled circle is the start position, the star is the signal source.

### Success Rate

![Success Rate](media/success_rate.png)

RSS achieved a success rate of **58.1%** in simulation, compared to 24.4% for Gao and 16.1% for Yamauchi.

### Progression

![Progression](media/progression.png)

RSS reaches roughly **66% of the way to the target** on average within the 600-second window, compared to 28% for Yamauchi and 19% for Gao.

---

## Repository Structure

```
src/
├── leo_bringup/       # Master launch files
├── leo_description/   # URDF robot model
├── leo_exploration/   # Frontier detection, exploration strategies, RSS node
├── leo_gazebo/        # Simulation world
├── leo_nav2/          # Nav2 configuration
├── leo_slam/          # SLAM Toolbox configuration
├── leo_teleop/        # Gamepad teleoperation
├── leo_utils/         # Analysis and recording scripts
└── leo_velodyne/      # Velodyne LiDAR driver configuration
```

---

## Setup

**Dependencies:** ROS2 Foxy, Nav2, SLAM Toolbox, Gazebo Classic

```bash
git clone https://github.com/lukasderia/ros2_leo_ws
cd ros2_leo_ws
colcon build
source install/setup.bash
```

### Simulation

```bash
ros2 launch leo_bringup laptop_sim.launch.py
```

### Physical Robot

On the Jetson:
```bash
ros2 launch leo_bringup jetson_full_exp.launch.py
```

On the laptop:
```bash
ros2 launch leo_bringup laptop_full.launch.py
```

The exploration mode is set via a parameter at launch. Modes: `0` = Yamauchi, `1` = Gao, `2` = RSS.

---

## Citation

If you use this work, please cite:

```
Düzakin, L. D. L. (2026). Not All Frontiers Are Equal: Comparing Frontier Selection
Strategies Using the Leo Rover. Master's thesis, University of Oslo.
```

---

*Department of Technology Systems, University of Oslo, Spring 2026*
