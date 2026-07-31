# 故障排查

> [根 README](../README.md) | [安装](install.md) | [标定](calibration.md) | [故障排查](troubleshooting.md)

## 编译被中断或 `install` 中没有可执行文件

若 `colcon build` 被 `Ctrl+C` / `SIGINT` 打断，或日志显示 iridescence 尚在配置（例如下载 GLM）时结束，`install/` 里可能只有空壳脚本、没有真正的标定二进制。此时 `ros2 pkg executables direct_visual_lidar_calibration` 会为空。

不要依赖半截的并行构建结果。按两阶段重来：

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

ros2 pkg executables direct_visual_lidar_calibration
```

## 找不到 `thirdparty/imgui/imgui.cpp`

典型错误：

```text
Cannot find source file:
  thirdparty/imgui/imgui.cpp
```

Iridescence 的 submodule 没有下载完整：

```bash
cd ~/Code/koide3/src/iridescence
git submodule sync --recursive
git submodule update --init --recursive

cd ~/Code/koide3
colcon build --packages-select iridescence --cmake-clean-cache
```

## Sophus、json 或 nanoflann 缺失

标定包的 submodule 没有下载完整：

```bash
cd ~/Code/koide3/src/direct_visual_lidar_calibration
git submodule sync --recursive
git submodule update --init --recursive

cd ~/Code/koide3
source install/setup.bash
colcon build \
  --packages-select direct_visual_lidar_calibration \
  --cmake-clean-cache
```

## 找不到 Iridescence

典型错误：

```text
Could not find a package configuration file provided by "Iridescence"
```

常见原因：第一次构建时两个包并行编译，标定包在 Iridescence 安装完成前就开始配置；或构建被中断后直接重跑 `colcon build`。

先单独构建 Iridescence，然后加载工作区：

```bash
cd ~/Code/koide3
source /opt/ros/humble/setup.bash
colcon build --packages-select iridescence --cmake-clean-cache
source install/setup.bash
colcon build \
  --packages-select direct_visual_lidar_calibration \
  --cmake-clean-cache
```

## CMake 提示找不到 GLM

系统未安装 `libglm-dev` 时，Iridescence 的 CMake 可能输出：

```text
Could not find a package configuration file provided by "glm"
```

当前 Iridescence 会继续通过 CMake FetchContent 下载 GLM 1.0.1。只要后续下载成功并继续编译，这条信息不是 `imgui.cpp` 缺失的原因。若在下载 GLM 时被中断，按上文「编译被中断」一节重新构建 Iridescence。

## 出现不存在的旧安装路径警告

如果 `AMENT_PREFIX_PATH` 或 `CMAKE_PREFIX_PATH` 指向已删除的旧安装目录，打开新终端后重新加载 ROS 2 并构建：

```bash
source /opt/ros/humble/setup.bash
cd ~/Code/koide3
colcon build --cmake-clean-cache
source install/setup.bash
```
