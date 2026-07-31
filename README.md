# Koide3 ROS 2 工作区

本目录是 **ROS 2 Humble** 的 colcon 工作区，用于 [Kenji Koide](https://github.com/koide3) 的 **无靶 LiDAR–相机外参标定** 工具链。

从同步录制的点云与图像估计 `T_lidar_camera`（相机系三维点 → LiDAR 系）。核心算法为 NID 直接配准（[ICRA 2023 官方文档](https://koide3.github.io/direct_visual_lidar_calibration/)）。

## 包含的包

| 包 | 路径 | 作用 |
|----|------|------|
| `iridescence` | [`src/iridescence`](src/iridescence) | 3D / 点云可视化（Dear ImGui + OpenGL） |
| `direct_visual_lidar_calibration` | [`src/direct_visual_lidar_calibration`](src/direct_visual_lidar_calibration) | NID 直接配准的 LiDAR–相机标定 |

> 本仓库是基于 [koide3/direct_visual_lidar_calibration](https://github.com/koide3/direct_visual_lidar_calibration) 与 [koide3/iridescence](https://github.com/koide3/iridescence) 整理的 ROS 2 工作区，并增加了 YAML 配置与一键标定流水线。

## 标定流水线

```text
推荐：编辑 calibration.yaml → run_calibration.py（一键）

等价分步：
  手动初值：preprocess → initial_guess_manual → calibrate → viewer（可选）
  自动初值：preprocess → find_matches_superglue.py → initial_guess_auto → calibrate → viewer（可选）
```

数据目录需自行创建：`mkdir -p ~/Code/koide3/data/{example,recordings}`。

## 快速编译

```bash
source /opt/ros/humble/setup.bash
cd ~/Code/koide3

# 首次必须分两阶段：先 Iridescence，再标定包
colcon build --packages-select iridescence --cmake-clean-cache
source install/setup.bash
colcon build --packages-select direct_visual_lidar_calibration --cmake-clean-cache
source install/setup.bash
```

系统依赖需包含 `libyaml-cpp-dev` 与 `python3-yaml`（供 `--config` 与一键脚本）。完整依赖、submodule、验证步骤见 [docs/install.md](docs/install.md)。

## 用 YAML 一键标定（推荐）

编译并 `source install/setup.bash` 后，用一份 YAML 写清 bag 路径、输出目录、话题和相机内参，再一键跑完整条流水线。

### 1. 准备数据与配置

```bash
SESSION_DIR=~/Code/koide3/data/recordings/2026-07-30_my_sensor
mkdir -p "$SESSION_DIR/raw" "$SESSION_DIR/processed"

# 将 rosbag2 放在 raw/ 下（每个 bag 一个子目录）
# 然后复制示例配置：
cp ~/Code/koide3/src/direct_visual_lidar_calibration/config/calibration.example.yaml \
  "$SESSION_DIR/calibration.yaml"
```

编辑 `calibration.yaml`，至少填写：

| 字段 | 含义 |
|------|------|
| `paths.data_path` | 原始 bag 父目录（如 `.../raw`） |
| `paths.dst_path` | 输出目录（如 `.../processed`） |
| `preprocess.image_topic` / `points_topic` | 图像与点云话题 |
| `preprocess.camera_model` / `camera_intrinsics` / `camera_distortion_coeffs` | 无 CameraInfo 时必填 |
| `initial_guess.method` | `manual`（GUI 选点）或 `auto`（SuperGlue，非商业） |

示例片段：

```yaml
paths:
  data_path: /home/zry/Code/koide3/data/recordings/2026-07-30_my_sensor/raw
  dst_path: /home/zry/Code/koide3/data/recordings/2026-07-30_my_sensor/processed

preprocess:
  auto_topic: false
  image_topic: /camera/image_color/compressed
  points_topic: /lidar/points
  camera_model: plumb_bob
  camera_intrinsics: [fx, fy, cx, cy]
  camera_distortion_coeffs: [k1, k2, p1, p2, k3]

initial_guess:
  method: manual   # 或 auto

calibrate:
  auto_quit: true

viewer:
  enabled: true
```

完整字段说明见示例文件与 [docs/calibration.md](docs/calibration.md)。

### 2. 一键运行

```bash
source /opt/ros/humble/setup.bash
source ~/Code/koide3/install/setup.bash

ros2 run direct_visual_lidar_calibration run_calibration.py \
  "$SESSION_DIR/calibration.yaml"
```

只跑部分阶段：

```bash
ros2 run direct_visual_lidar_calibration run_calibration.py \
  "$SESSION_DIR/calibration.yaml" \
  --steps preprocess,initial_guess,calibrate
```

仅预处理（同一 YAML）：

```bash
ros2 run direct_visual_lidar_calibration preprocess \
  --config "$SESSION_DIR/calibration.yaml"
```

结果写入 `paths.dst_path/calib.json`（含 `results.T_lidar_camera`）。

说明：`method: manual` 时会在初值 GUI 处等待你选点并 Save；CLI 显式参数会覆盖 YAML 同名项；旧版长命令行仍可用，见标定文档。

## 文档索引

| 文档 | 内容 |
|------|------|
| [docs/install.md](docs/install.md) | 环境依赖、目录布局、下载、两阶段编译、更新 |
| [docs/calibration.md](docs/calibration.md) | YAML 一键流程、Livox / Ouster 示例与 CLI 兼容写法 |
| [docs/troubleshooting.md](docs/troubleshooting.md) | 编译中断、submodule、Iridescence / GLM 等常见问题 |

不想本机编译时，可用上游 Docker：`koide3/direct_visual_lidar_calibration:humble`（见 [官方 Docker 说明](https://koide3.github.io/direct_visual_lidar_calibration/docker/)）。
