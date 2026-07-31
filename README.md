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

系统依赖需包含 `libyaml-cpp-dev` 与 `python3-yaml`（供 `--config` 与一键脚本）。完整依赖见 [docs/install.md](docs/install.md)。

## 数据包如何放置

`data/` **不随仓库附带**，需自行创建。推荐布局：

```text
~/Code/koide3/data/
├── example/                          # 官方示例（可选）
│   ├── livox/                        # 解压后的多个 rosbag2
│   └── livox_preprocessed/           # preprocess 输出
└── recordings/                       # 自己的标定任务
    └── 2026-07-30_my_sensor/         # 一次独立任务（建议含日期+传感器名）
        ├── raw/                      # 原始 rosbag2（YAML 里的 data_path）
        │   ├── bag_01/
        │   │   ├── metadata.yaml
        │   │   └── *.db3
        │   └── bag_02/
        │       ├── metadata.yaml
        │       └── *.db3
        ├── processed/                # 预处理与标定结果（YAML 里的 dst_path）
        │   └── calib.json
        └── calibration.yaml          # 本任务的配置文件
```

### 自录 / 外部 bag

```bash
mkdir -p ~/Code/koide3/data/{example,recordings}

SESSION_DIR=~/Code/koide3/data/recordings/2026-07-30_my_sensor
mkdir -p "$SESSION_DIR/raw" "$SESSION_DIR/processed"

# 把每个 rosbag2 目录放进 raw/ 的第一层，例如：
#   raw/bag_01/metadata.yaml + *.db3
#   raw/bag_02/metadata.yaml + *.db3
```

放置规则：

- `preprocess` **只扫描 `raw/` 的第一层子目录**，不会递归更深路径。
- 每个子目录必须是可被 `ros2 bag info` 打开的 rosbag2。
- 同一次任务下所有 bag 应使用相同话题名、相机内参和相机模型。
- 建议最少 1 个 bag，更好从不同视角录 5～10 个。

检查：

```bash
ros2 bag info "$SESSION_DIR/raw/bag_01"
```

### 官方示例数据（可选）

Livox / Ouster 示例可从 [Zenodo](https://zenodo.org/records/7780490) 下载，解压到 `data/example/`。详细步骤见 [docs/calibration.md](docs/calibration.md)。解压后同样是「父目录下多个 bag 子目录」结构，YAML 的 `data_path` 指到该父目录即可。

## YAML 配置说明

示例模板：

[`src/direct_visual_lidar_calibration/config/calibration.example.yaml`](src/direct_visual_lidar_calibration/config/calibration.example.yaml)

为每次任务复制一份再改：

```bash
cp ~/Code/koide3/src/direct_visual_lidar_calibration/config/calibration.example.yaml \
  "$SESSION_DIR/calibration.yaml"
```

### 完整示例

```yaml
paths:
  data_path: /home/zry/Code/koide3/data/recordings/2026-07-30_my_sensor/raw
  dst_path: /home/zry/Code/koide3/data/recordings/2026-07-30_my_sensor/processed

preprocess:
  auto_topic: false
  dynamic_lidar_integration: false
  visualize: true
  intensity_channel: auto
  image_topic: /camera/image_color/compressed
  points_topic: /lidar/points
  # camera_info_topic: /camera/camera_info
  camera_model: plumb_bob
  camera_intrinsics: [fx, fy, cx, cy]
  camera_distortion_coeffs: [k1, k2, p1, p2, k3]

initial_guess:
  method: manual          # manual | auto
  rotate_camera: 0
  rotate_lidar: 0

calibrate:
  registration_type: nid_bfgs
  nid_bins: 16
  auto_quit: true
  background: false

viewer:
  enabled: true
```

把 `camera_intrinsics` / `camera_distortion_coeffs` 换成你自己的标定数值；不要照抄占位符。

### 参数说明

#### `paths`（必填）

| 参数 | 作用 |
|------|------|
| `data_path` | 原始 rosbag2 的**父目录**（如 `.../raw`） |
| `dst_path` | 预处理图像/点云、`calib.json` 的输出目录（如 `.../processed`） |

#### `preprocess`

| 参数 | 默认/示例 | 作用 |
|------|-----------|------|
| `auto_topic` | `false` | `true` 时自动选 Image / PointCloud2 / CameraInfo；bag 里话题不唯一时请设 `false` 并手写话题 |
| `dynamic_lidar_integration` | `false` | 旋转式 LiDAR（Ouster、Velodyne 等）设 `true`，做动态点云积分；Livox 等静止扫描一般 `false` |
| `visualize` | `true` | 预处理时弹出可视化窗口 |
| `intensity_channel` | `auto` | 点云强度字段名；`auto` 会在 `intensity` / `reflectivity` 等中自动选 |
| `image_topic` | 话题名 | 图像话题（支持 compressed） |
| `points_topic` | 话题名 | 点云 `PointCloud2` 话题 |
| `camera_info_topic` | 可选 | CameraInfo 话题；没有可省略，改用下方内参 |
| `camera_model` | `plumb_bob` 等 | 相机模型：`plumb_bob` / `fisheye` / `equidistant` / `omnidir` / `equirectangular` / `auto` |
| `camera_intrinsics` | `[fx, fy, cx, cy]` | 针孔内参；无 CameraInfo 时必填 |
| `camera_distortion_coeffs` | `[k1, k2, p1, p2, k3]` | 畸变系数；无 CameraInfo 时必填 |
| `voxel_resolution` | `0.002` | 点云体素分辨率（米） |
| `min_distance` | `1.0` | 丢弃过近点的距离阈值（米） |
| `k_neighbors` | `20` | CT-ICP 协方差估计用的邻域点数 |

#### `initial_guess`

| 参数 | 默认/示例 | 作用 |
|------|-----------|------|
| `method` | `manual` / `auto` | `manual`：打开 GUI 手动选 2D–3D 对应点；`auto`：SuperGlue 匹配 + 自动初值（**不可商用**） |
| `rotate_camera` | `0` | 匹配前将相机图顺时针旋转 `0/90/180/270`（仅 `auto`） |
| `rotate_lidar` | `0` | 匹配前将 LiDAR 强度图旋转同样角度（仅 `auto`） |
| `superglue` | `outdoor` | SuperGlue 权重：`indoor` 或 `outdoor` |
| `ransac_iterations` | `8192` | 自动初值 RANSAC 迭代次数 |
| `ransac_error_thresh` | `10.0` | RANSAC 重投影误差阈值（像素） |
| `robust_kernel_width` | `10.0` | 精化时 Cauchy 核宽度（像素） |

#### `calibrate`

| 参数 | 默认/示例 | 作用 |
|------|-----------|------|
| `registration_type` | `nid_bfgs` | 优化器：`nid_bfgs` 或 `nid_nelder_mead` |
| `nid_bins` | `16` | NID 直方图 bin 数 |
| `auto_quit` | `true` | 标定结束后自动退出（一键流水线建议保持 `true`） |
| `background` | `false` | `true` 时隐藏标定界面、后台跑优化 |
| `disable_culling` | — | 若设置，关闭基于深度缓冲的遮挡剔除 |

#### `viewer`

| 参数 | 默认/示例 | 作用 |
|------|-----------|------|
| `enabled` | `true` | 流水线末尾是否打开 `viewer` 检查投影；不需要可设 `false` |

优先级：**命令行显式参数 > YAML > 程序内置默认值**。

## 一键运行

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

仅预处理：

```bash
ros2 run direct_visual_lidar_calibration preprocess \
  --config "$SESSION_DIR/calibration.yaml"
```

结果在 `paths.dst_path/calib.json`，其中：

```text
results.T_lidar_camera = [x, y, z, qx, qy, qz, qw]
```

表示相机系点到 LiDAR 系：`p_lidar = T_lidar_camera * p_camera`。

`method: manual` 时流水线会停在初值 GUI，选点 → Estimate → Save 后再继续。更细的录制建议与 CLI 兼容写法见 [docs/calibration.md](docs/calibration.md)。

## 文档索引

| 文档 | 内容 |
|------|------|
| [docs/install.md](docs/install.md) | 环境依赖、目录布局、下载、两阶段编译、更新 |
| [docs/calibration.md](docs/calibration.md) | Livox / Ouster 示例、自录 bag、YAML / CLI 全流程 |
| [docs/troubleshooting.md](docs/troubleshooting.md) | 编译中断、submodule、Iridescence / GLM 等常见问题 |

不想本机编译时，可用 Docker（**仅 Humble**）：镜像标签 `humble`，本地构建见 [`src/direct_visual_lidar_calibration/docker/humble/`](src/direct_visual_lidar_calibration/docker/humble/)，说明见 [`docs/docker.md`](src/direct_visual_lidar_calibration/docs/docker.md)。
