# 安装与编译

> [根 README](../README.md) | [安装](install.md) | [标定](calibration.md) | [故障排查](troubleshooting.md)

本文说明如何在 ROS 2 Humble 工作区中下载、编译 `iridescence` 与 `direct_visual_lidar_calibration`。

两个仓库都使用了 Git submodule。全新下载时必须使用 `--recurse-submodules`，否则会缺少第三方源码并导致编译失败。

本指南以 **本机 ROS 2 Humble 源码编译** 为主。若不想安装依赖，也可使用上游 [Docker 镜像](https://koide3.github.io/direct_visual_lidar_calibration/docker/)（Hub：`koide3/direct_visual_lidar_calibration:humble`）；详见包内 [`docs/docker.md`](../src/direct_visual_lidar_calibration/docs/docker.md)。

## 目录结构与数据位置

本文档以 ROS 2 Humble 和以下工作区路径为例。推荐将源码、原始数据和预处理结果分开。

`data/` **不会**随源码仓库附带，需自行创建：

```bash
mkdir -p ~/Code/koide3/data/{example,recordings}
```

推荐布局：

```text
~/Code/koide3/
├── README.md                             # 工作区简短入口
├── docs/                                 # 本工作区详细文档
│   ├── install.md
│   ├── calibration.md
│   └── troubleshooting.md
├── .vscode/                              # 可选：编辑器配置
├── src/                                  # 只放源码
│   ├── README.md                         # 跳转到 docs/
│   ├── iridescence/
│   │   └── thirdparty/                   # Iridescence 的 submodule
│   └── direct_visual_lidar_calibration/
│       ├── docs/                         # 上游文档
│       └── thirdparty/                   # Sophus、json、nanoflann
├── data/                                 # 所有标定数据（需自行 mkdir，默认不存在）
│   ├── example/                          # 官方示例数据
│   │   ├── livox.tar.gz                  # 下载包，可验证后删除
│   │   ├── livox/                        # Livox 原始 rosbag2 集合
│   │   │   ├── rosbag2_.../
│   │   │   │   ├── metadata.yaml
│   │   │   │   └── *.db3
│   │   │   └── ...
│   │   ├── livox_preprocessed/           # Livox 预处理及标定结果
│   │   │   ├── calib.json
│   │   │   ├── *.png
│   │   │   └── *.ply
│   │   ├── ouster.tar.gz
│   │   ├── ouster/                       # Ouster 原始 rosbag2 集合
│   │   └── ouster_preprocessed/          # Ouster 预处理及标定结果
│   └── recordings/                       # 自己录制的数据
│       └── 2026-07-25_my_sensor/         # 一次独立标定任务
│           ├── raw/                      # preprocess 的输入目录
│           │   ├── bag_01/
│           │   │   ├── metadata.yaml
│           │   │   └── bag_01_0.db3
│           │   ├── bag_02/
│           │   │   ├── metadata.yaml
│           │   │   └── bag_02_0.db3
│           │   └── ...
│           └── processed/                # preprocess 的输出目录
│               ├── calib.json            # 初值和最终外参都保存在这里
│               ├── *.png
│               └── *.ply
├── build/                                # colcon 自动生成的编译目录
├── install/                              # colcon 自动生成的安装目录
└── log/                                  # colcon 自动生成的日志目录
```

数据放置规则：

- `data/` 需自行创建；工作区默认只包含 `src/`、以及 colcon 生成的 `build/` / `install/` / `log/`。
- 不要把自己录制的 bag 放进 `src/` 或两个 Git 仓库内部。
- `src/iridescence/data/` 是 Iridescence 自身的资源目录，不是标定数据目录。
- 官方示例数据放在 `~/Code/koide3/data/example/`。
- 自录数据放在 `~/Code/koide3/data/recordings/<本次标定任务>/`。
- 每次标定任务使用独立目录，避免覆盖其他设备或其他日期的 `calib.json`。
- `raw/` 的第一层子目录必须分别是可被 `ros2 bag info` 打开的 rosbag2 目录。
- `processed/` 与 `raw/` 分开；不要把预处理输出写进输入目录。
- `build/`、`install/` 和 `log/` 由 colcon 管理，不用于存放数据。

## 1. 准备环境

确认 ROS 2 Humble 已安装：

```bash
source /opt/ros/humble/setup.bash
```

确认 GitHub SSH 密钥可用：

```bash
ssh -T git@github.com
```

认证成功时会看到类似下面的信息：

```text
Hi <用户名>! You've successfully authenticated, but GitHub does not provide shell access.
```

GitHub 不提供 SSH Shell，因此该命令即使认证成功也可能返回非零状态；应以上述认证信息为判断依据。

安装上游文档列出的通用系统依赖：

```bash
sudo apt update
sudo apt install \
  libomp-dev \
  libboost-all-dev \
  libglm-dev \
  libglfw3-dev \
  libpng-dev \
  libjpeg-dev \
  libyaml-cpp-dev \
  python3-yaml
```

`libyaml-cpp-dev` 供 `preprocess --config` 解析 YAML；`python3-yaml` 供一键流水线脚本 `run_calibration.py` 使用。

`direct_visual_lidar_calibration` 还依赖 PCL、OpenCV、GTSAM、Ceres 和 Iridescence。PCL / OpenCV 一般可通过 `rosdep` 安装；**GTSAM 与 Ceres 不会由 rosdep 安装**，需按下面步骤为本机 Humble（Ubuntu 22.04）编译安装。更完整说明见：[上游安装说明](../src/direct_visual_lidar_calibration/docs/installation.md)。

### 安装 GTSAM（Humble / Ubuntu 22.04）

```bash
git clone https://github.com/borglab/gtsam
cd gtsam && git checkout 4.2a9
mkdir build && cd build
cmake .. \
  -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF \
  -DGTSAM_BUILD_TESTS=OFF \
  -DGTSAM_WITH_TBB=OFF \
  -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF \
  -DGTSAM_USE_SYSTEM_EIGEN=ON
make -j$(nproc)
sudo make install
sudo ldconfig
```

Ubuntu 22.04 必须加上 `-DGTSAM_USE_SYSTEM_EIGEN=ON`。

### 安装 Ceres

```bash
git clone --recurse-submodules https://github.com/ceres-solver/ceres-solver
cd ceres-solver
git checkout e47a42c2957951c9fafcca9995d9927e15557069
mkdir build && cd build
cmake .. -DBUILD_EXAMPLES=OFF -DBUILD_TESTING=OFF -DUSE_CUDA=OFF
make -j$(nproc)
sudo make install
sudo ldconfig
```

### Iridescence 的安装方式（本工作区）

上游文档中有 `sudo make install` 安装 Iridescence 的步骤。**本工作区不要那样做**：把 `iridescence` 放在 `src/` 中，用 colcon 安装到 `install/`，再 `source install/setup.bash`。这样与标定包共用同一前缀，也避免与系统路径混用。

### 可选：安装 SuperGlue（仅自动初值）

> SuperGlue **不允许商业用途**。商业项目请使用 `initial_guess_manual`。使用前请自行核对 [其许可证](https://github.com/magicleap/SuperGluePretrainedNetwork)。

```bash
pip3 install numpy opencv-python torch matplotlib

# 建议放在工作区外，避免混入 colcon 源码树
git clone https://github.com/magicleap/SuperGluePretrainedNetwork.git \
  ~/opt/SuperGluePretrainedNetwork

echo 'export PYTHONPATH=$PYTHONPATH:$HOME/opt/SuperGluePretrainedNetwork' \
  >> ~/.bashrc
source ~/.bashrc
```

将路径换成你实际的 clone 目录即可。配置完成后，才能运行 `find_matches_superglue.py` 与 `initial_guess_auto`。

## 2. 推荐：全新递归下载

```bash
mkdir -p ~/Code/koide3/src
cd ~/Code/koide3/src

git clone --recurse-submodules \
  git@github.com:koide3/iridescence.git

git clone --recurse-submodules \
  git@github.com:koide3/direct_visual_lidar_calibration.git
```

`--recursive` 也可以使用，但推荐含义更明确的 `--recurse-submodules`。

不要在同名目录已经存在时重复执行 `git clone`。如果仓库已经通过普通方式克隆，请按照下一节补拉 submodule。

下载两个仓库后，可以通过 rosdep 安装其清单中已经声明的 ROS 依赖：

```bash
cd ~/Code/koide3
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

rosdep 不会替代上游文档要求的 GTSAM、Ceres 安装步骤。

## 3. 已经普通克隆：补拉 submodule

如果之前使用的是：

```bash
git clone git@github.com:koide3/iridescence.git
git clone git@github.com:koide3/direct_visual_lidar_calibration.git
```

不需要重新克隆仓库，分别初始化 submodule：

```bash
cd ~/Code/koide3/src/iridescence
git submodule sync --recursive
git submodule update --init --recursive

cd ~/Code/koide3/src/direct_visual_lidar_calibration
git submodule sync --recursive
git submodule update --init --recursive
```

其中：

- Iridescence 会下载 ImGuizmo、imgui、implot、portable-file-dialogs 和 pybind11。
- direct_visual_lidar_calibration 会下载 Sophus、json 和 nanoflann。
- submodule 的具体提交由各自主仓库锁定，不要手动切换到第三方仓库的最新提交。

## 4. 验证源码是否完整

检查两个仓库的 submodule：

```bash
git -C ~/Code/koide3/src/iridescence \
  submodule status --recursive

git -C ~/Code/koide3/src/direct_visual_lidar_calibration \
  submodule status --recursive
```

状态判断：

- 每行开头为空格：submodule 已正确检出。
- 每行开头为 `-`：submodule 尚未初始化。
- 每行开头为 `+`：当前提交与主仓库锁定的提交不一致。

检查关键源码文件：

```bash
test -f ~/Code/koide3/src/iridescence/thirdparty/imgui/imgui.cpp \
  && echo "Iridescence submodule 正常"

test -f ~/Code/koide3/src/direct_visual_lidar_calibration/thirdparty/Sophus/CMakeLists.txt \
  && echo "direct_visual_lidar_calibration submodule 正常"
```

确认 colcon 能发现两个包：

```bash
cd ~/Code/koide3
colcon list
```

预期至少包含：

```text
direct_visual_lidar_calibration
iridescence
```

## 5. 第一次编译

全新工作区建议分两阶段编译。先安装 Iridescence，再加载其环境并编译标定包：

```bash
cd ~/Code/koide3
source /opt/ros/humble/setup.bash

colcon build \
  --packages-select iridescence \
  --cmake-clean-cache

source install/setup.bash

colcon build \
  --packages-select direct_visual_lidar_calibration \
  --cmake-clean-cache

source install/setup.bash
```

分阶段构建很重要：`direct_visual_lidar_calibration` 的 CMake 会查找 `Iridescence`，必须先完成 Iridescence 的安装并加载 `install/setup.bash`。不要在第一次编译时并行同时编两个包——标定包会因找不到 Iridescence 而失败。

编译完成后验证可执行文件已安装：

```bash
source /opt/ros/humble/setup.bash
source ~/Code/koide3/install/setup.bash

ros2 pkg executables direct_visual_lidar_calibration
```

预期至少包含：`preprocess`、`initial_guess_manual`、`initial_guess_auto`、`calibrate`、`viewer`、`find_matches_superglue.py`、`run_calibration.py`。若列表为空，说明安装未完成（常见原因：构建被中断），请按 [故障排查](troubleshooting.md) 中「编译被中断或 install 中没有可执行文件」恢复。

完成第一次安装后，可以在工作区根目录构建两个包：

```bash
cd ~/Code/koide3
source /opt/ros/humble/setup.bash
source install/setup.bash
colcon build
source install/setup.bash
```

如果当前 Shell 已配置以下别名：

```bash
alias cbd='colcon build && source install/setup.bash'
```

也可以执行：

```bash
cd ~/Code/koide3
cbd
```

## 6. 更新仓库

更新主仓库后，也要同步其锁定的 submodule：

```bash
cd ~/Code/koide3/src/iridescence
git pull --ff-only
git submodule sync --recursive
git submodule update --init --recursive

cd ~/Code/koide3/src/direct_visual_lidar_calibration
git pull --ff-only
git submodule sync --recursive
git submodule update --init --recursive
```

下一步：按 [标定教程](calibration.md) 跑官方示例或自录数据。
