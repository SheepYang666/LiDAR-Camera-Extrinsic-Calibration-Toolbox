# 标定教程

> [根 README](../README.md) | [安装](install.md) | [标定](calibration.md) | [故障排查](troubleshooting.md)

在完成 [安装与编译](install.md) 后，按本节流程进行无靶 LiDAR–相机外参标定。

本节根据以下官方资料整理为当前 ROS 2 Humble 工作区可直接执行的流程：

- [官方 Calibration example](https://koide3.github.io/direct_visual_lidar_calibration/example/)
- [官方 Program details](https://koide3.github.io/direct_visual_lidar_calibration/programs/)
- [官方示例数据集（Zenodo）](https://zenodo.org/records/7780490)

## 程序关系

```text
手动初值流程：
preprocess
  → initial_guess_manual
  → calibrate
  → viewer（可选）

自动初值流程：
preprocess
  → find_matches_superglue.py
  → initial_guess_auto
  → calibrate
  → viewer（可选）
```

说明：

- 手动初值与自动初值是两种替代方案，只选择其中一种，不需要两种都执行。
- 自动方案中的 `find_matches_superglue.py` 和 `initial_guess_auto` 必须按顺序执行：前者生成匹配关系，后者根据匹配关系计算初始外参。
- `calibrate` 使用已经保存的初始外参进行精细优化，并将最终结果写入 `calib.json`。
- `viewer` 只读取已有结果进行可视化检查，不会重新标定，因此是可选步骤。

开始前加载环境并创建数据目录（若尚未创建）：

```bash
source /opt/ros/humble/setup.bash
source ~/Code/koide3/install/setup.bash

mkdir -p ~/Code/koide3/data/example
cd ~/Code/koide3/data/example
```

## 1. Livox 与相机标定

### 下载并解压示例数据

Livox ROS 2 数据集约为 2.2 GB：

```bash
cd ~/Code/koide3/data/example

wget -c \
  -O livox.tar.gz \
  "https://zenodo.org/record/7779880/files/livox.tar.gz?download=1"

# 校验值以实际下载文件为准；下列为历史上常用的参考 MD5
echo "d06951014b28da1afa001db93153909d  livox.tar.gz" \
  | md5sum -c -

tar xzvf livox.tar.gz
```

检查数据目录和其中一个 rosbag：

```bash
ls livox

ros2 bag info \
  livox/rosbag2_2023_03_09-13_42_46/
```

官方 Livox 数据集包含 5 个 ROS 2 bag，主要话题为：

- 点云：`/livox/points`
- 图像：`/image`
- 相机参数：`/camera_info`

### 数据预处理

```bash
cd ~/Code/koide3/data/example

ros2 run direct_visual_lidar_calibration preprocess \
  livox \
  livox_preprocessed \
  -av
```

参数含义：

- `-a`：自动检测 PointCloud2、Image 和 CameraInfo 话题。
- `-v`：显示点云累积过程。

处理完成后，`livox_preprocessed/` 中应包含：

- `calib.json`
- 相机图像 `*.png`
- 稠密点云 `*.ply`
- LiDAR 投影索引和强度图

```bash
ls livox_preprocessed
```

### 生成初始外参：手动方式

手动方式和自动方式二选一。手动方式不依赖 SuperGlue，商业使用时也建议采用此方式：

```bash
ros2 run direct_visual_lidar_calibration \
  initial_guess_manual \
  livox_preprocessed
```

在界面中：

1. 在点云上右键选择一个 3D 点。
2. 在图像上右键选择与其对应的 2D 点。
3. 单击 `Add picked points`。
4. 至少添加 3 组对应点；数量越多、分布越均匀越好。
5. 单击 `Estimate` 计算初始外参。
6. 调节 `blend_weight` 检查点云投影是否基本对齐。
7. 单击 `Save` 保存初始外参。

### 生成初始外参：自动方式（可选）

> SuperGlue 的许可证不允许商业用途。商业项目应使用手动初值方式。

自动方式要求先按照 [安装文档](install.md) 中「可选：安装 SuperGlue」配置好 `PYTHONPATH`。下面两条命令属于同一个自动流程，必须按顺序执行。Livox 示例还需要将相机图像旋转 90°：

```bash
ros2 run direct_visual_lidar_calibration \
  find_matches_superglue.py \
  livox_preprocessed \
  --rotate_camera 90

ros2 run direct_visual_lidar_calibration \
  initial_guess_auto \
  livox_preprocessed
```

可以检查 `livox_preprocessed/` 中生成的 `*_superglue.png`，确认自动匹配是否合理。

### 精细标定

使用 NID 配准优化初始外参：

```bash
ros2 run direct_visual_lidar_calibration \
  calibrate \
  livox_preprocessed
```

### 查看标定结果

这一步只用于重新打开已经保存的结果进行检查，不会重新标定，可以不执行：

```bash
ros2 run direct_visual_lidar_calibration \
  viewer \
  livox_preprocessed
```

结果保存在：

```text
~/Code/koide3/data/example/livox_preprocessed/calib.json
```

其中：

```text
results.T_lidar_camera = [x, y, z, qx, qy, qz, qw]
```

该变换将相机坐标系中的三维点转换到 LiDAR 坐标系：

```text
p_lidar = T_lidar_camera * p_camera
```

不要在未确认变换方向的情况下直接将它当作 LiDAR 到相机的变换；反方向需要计算其逆变换。

## 2. Ouster 与相机标定

### 下载并解压示例数据

Ouster ROS 2 数据集约为 1.5 GB：

```bash
cd ~/Code/koide3/data/example

wget -c \
  -O ouster.tar.gz \
  "https://zenodo.org/record/7779880/files/ouster.tar.gz?download=1"

# 校验值以实际下载文件为准；下列为历史上常用的参考 MD5
echo "a0a56bbb93433f729a9e924744ad6b0c  ouster.tar.gz" \
  | md5sum -c -

tar xzvf ouster.tar.gz
```

检查数据：

```bash
ls ouster

ros2 bag info \
  ouster/rosbag2_2023_03_28-16_25_54/
```

官方 Ouster 数据集包含 2 个 ROS 2 bag，主要话题为：

- 点云：`/points`
- 图像：`/image`
- 相机参数：`/camera_info`

### 数据预处理

Ouster 属于旋转式 LiDAR，需要增加 `-d`，在运动补偿的同时进行动态点云积分：

```bash
ros2 run direct_visual_lidar_calibration preprocess \
  ouster \
  ouster_preprocessed \
  -adv
```

参数含义：

- `-a`：自动检测话题。
- `-d`：启用动态 LiDAR 点云积分。
- `-v`：显示处理过程。

### 初始外参

以下手动方式和自动方式二选一。

方式一：手动选择对应点，只执行这一条命令：

```bash
ros2 run direct_visual_lidar_calibration \
  initial_guess_manual \
  ouster_preprocessed
```

方式二：自动计算初值。该方式仅适用于符合 SuperGlue 许可证要求且已完成相关配置的场景。下面两条命令必须按顺序执行：

```bash
# 第一步：使用 SuperGlue 生成匹配关系
ros2 run direct_visual_lidar_calibration \
  find_matches_superglue.py \
  ouster_preprocessed

# 第二步：根据匹配关系计算并保存初始外参
ros2 run direct_visual_lidar_calibration \
  initial_guess_auto \
  ouster_preprocessed
```

### 精细标定与结果查看

先执行 `calibrate` 进行精细优化并保存最终外参：

```bash
ros2 run direct_visual_lidar_calibration \
  calibrate \
  ouster_preprocessed
```

`viewer` 只用于之后重新打开结果进行检查，不会重新标定，因此可以不执行：

```bash
ros2 run direct_visual_lidar_calibration \
  viewer \
  ouster_preprocessed
```

结果保存在：

```text
~/Code/koide3/data/example/ouster_preprocessed/calib.json
```

## 3. 使用自己的 ROS 2 bag

### 创建本次标定的数据目录

一次标定任务使用一个独立目录。目录名建议包含日期和传感器名称：

```bash
SESSION_NAME=2026-07-25_my_sensor
SESSION_DIR=~/Code/koide3/data/recordings/$SESSION_NAME
BAG_DIR=$SESSION_DIR/raw
OUTPUT_DIR=$SESSION_DIR/processed

mkdir -p "$BAG_DIR" "$OUTPUT_DIR"
```

其中：

- `BAG_DIR` 是原始 rosbag2 的父目录。
- `OUTPUT_DIR` 用于保存预处理数据、初始外参和最终标定结果。
- `preprocess` 只检查 `BAG_DIR` 的第一层子目录，不会递归搜索更深的路径。

### 录制数据

录制前应确认：

- 相机内参和畸变参数已经标定。
- 相机与 LiDAR 刚性固定，采集期间两者不能相对移动。
- 每个 bag 开始录制时，传感器应先保持静止，确保第一帧点云和图像处于相同位姿。
- 环境中应同时具有足够的几何结构、图像纹理和有效的 LiDAR 强度变化。

先通过 `ros2 topic list` 确认实际话题，然后设置：

```bash
IMAGE_TOPIC=/camera/image
CAMERA_INFO_TOPIC=/camera/camera_info
POINTS_TOPIC=/lidar/points
```

录制第一组数据：

```bash
ros2 bag record \
  -o "$BAG_DIR/bag_01" \
  "$IMAGE_TOPIC" \
  "$CAMERA_INFO_TOPIC" \
  "$POINTS_TOPIC"
```

按 `Ctrl+C` 停止后，使用新的目录名继续录制：

```bash
ros2 bag record \
  -o "$BAG_DIR/bag_02" \
  "$IMAGE_TOPIC" \
  "$CAMERA_INFO_TOPIC" \
  "$POINTS_TOPIC"
```

采集建议：

- 最少可以使用 1 个 bag，但建议从不同视角录制 5～10 个 bag。
- Livox 等非重复扫描 LiDAR：每个 bag 保持传感器静止约 10～15 秒。
- Ouster 等旋转式 LiDAR：缓慢上下移动传感器约 10 秒；16 线或 32 线设备建议延长到约 20～30 秒。
- 同一次任务下的所有 bag 应使用相同的话题名、相机内参和相机模型。

录制后检查每个 bag：

```bash
ros2 bag info "$BAG_DIR/bag_01"
ros2 bag info "$BAG_DIR/bag_02"
```

预期结构如下：

```text
raw/
├── bag_01/
│   ├── metadata.yaml
│   └── bag_01_0.db3
└── bag_02/
    ├── metadata.yaml
    └── bag_02_0.db3
```

### 用 YAML 配置一键标定（推荐）

录制完成后，复制示例配置并填写路径、话题与相机内参：

```bash
cp ~/Code/koide3/src/direct_visual_lidar_calibration/config/calibration.example.yaml \
  "$SESSION_DIR/calibration.yaml"
```

编辑 `$SESSION_DIR/calibration.yaml`，至少设置：

- `paths.data_path` → `$BAG_DIR`
- `paths.dst_path` → `$OUTPUT_DIR`
- `preprocess` 中的话题，以及（无 CameraInfo 时）`camera_model` / `camera_intrinsics` / `camera_distortion_coeffs`
- `initial_guess.method`：`manual`（GUI 选点）或 `auto`（SuperGlue，有许可证限制）

然后一键跑完整流水线：

```bash
source /opt/ros/humble/setup.bash
source ~/Code/koide3/install/setup.bash

ros2 run direct_visual_lidar_calibration run_calibration.py \
  "$SESSION_DIR/calibration.yaml"
```

只跑部分阶段时可用 `--steps`，例如：

```bash
ros2 run direct_visual_lidar_calibration run_calibration.py \
  "$SESSION_DIR/calibration.yaml" \
  --steps preprocess,initial_guess,calibrate
```

说明：

- `initial_guess.method: manual` 时，流水线会打开 `initial_guess_manual` GUI，需你选点、Estimate、Save 后再继续。
- `method: auto` 会依次调用 `find_matches_superglue.py` 与 `initial_guess_auto`（SuperGlue 不允许商业用途）。
- `calibrate.auto_quit: true`（默认）让精细标定结束后自动退出，便于无人值守。
- `viewer.enabled: false` 可跳过末尾可视化。

也可以只对 preprocess 使用同一配置：

```bash
ros2 run direct_visual_lidar_calibration preprocess \
  --config "$SESSION_DIR/calibration.yaml"
```

显式 CLI 参数会覆盖 YAML 中的同名项。示例文件安装后还在：

```text
install/direct_visual_lidar_calibration/share/direct_visual_lidar_calibration/config/calibration.example.yaml
```

### 预处理自录数据（CLI，兼容写法）

若不使用 YAML，仍可用命令行。自动检测要求每个 bag 中只有一组需要使用的 PointCloud2、Image 和 CameraInfo 话题：

```bash
ros2 run direct_visual_lidar_calibration preprocess \
  "$BAG_DIR" \
  "$OUTPUT_DIR" \
  -av
```

旋转式 LiDAR 通常增加 `-d`：

```bash
ros2 run direct_visual_lidar_calibration preprocess \
  "$BAG_DIR" \
  "$OUTPUT_DIR" \
  -adv
```

如果自动检测选错话题，应明确指定：

```bash
ros2 run direct_visual_lidar_calibration preprocess \
  "$BAG_DIR" \
  "$OUTPUT_DIR" \
  --image_topic /camera/image \
  --camera_info_topic /camera/camera_info \
  --points_topic /lidar/points \
  -v
```

如果 bag 中没有可用的 CameraInfo，还需要根据实际相机标定结果提供相机模型、内参和畸变参数。不要直接复制官方示例数据的相机参数。

例如，针孔相机使用自己的实际标定值：

```bash
ros2 run direct_visual_lidar_calibration preprocess \
  "$BAG_DIR" \
  "$OUTPUT_DIR" \
  --image_topic /camera/image \
  --points_topic /lidar/points \
  --camera_model plumb_bob \
  --camera_intrinsics fx,fy,cx,cy \
  --camera_distortion_coeffs k1,k2,p1,p2,k3 \
  -v
```

内参和畸变参数使用英文逗号分隔，中间不要加入空格。

### 完成初值、标定和检查（CLI，兼容写法）

若未使用 `run_calibration.py`，可逐步执行。手动初值和自动初值二选一。

方式一：手动选择对应点并保存初始外参：

```bash
ros2 run direct_visual_lidar_calibration \
  initial_guess_manual \
  "$OUTPUT_DIR"
```

方式二：自动计算初值。SuperGlue 仅适用于符合其许可证要求且已完成相关配置的场景，下面两条命令必须按顺序执行：

```bash
# 第一步：使用 SuperGlue 生成匹配关系
ros2 run direct_visual_lidar_calibration \
  find_matches_superglue.py \
  "$OUTPUT_DIR"

# 第二步：根据匹配关系计算并保存初始外参
ros2 run direct_visual_lidar_calibration \
  initial_guess_auto \
  "$OUTPUT_DIR"
```

如果相机图像与 LiDAR 图像的向上方向不一致，应根据实际安装方向为第一条命令增加 `--rotate_camera` 或 `--rotate_lidar`。

完成任意一种初值方式后，进行精细优化并保存最终外参：

```bash
ros2 run direct_visual_lidar_calibration \
  calibrate \
  "$OUTPUT_DIR"
```

最后按需使用 `viewer` 重新打开结果进行检查；这一步不会重新标定，可以不执行：

```bash
ros2 run direct_visual_lidar_calibration \
  viewer \
  "$OUTPUT_DIR"
```

最终结果位于：

```text
~/Code/koide3/data/recordings/<本次标定任务>/processed/calib.json
```

同一任务需要重新预处理时，建议先为现有 `processed/` 建立备份，避免覆盖已经确认过的结果。
