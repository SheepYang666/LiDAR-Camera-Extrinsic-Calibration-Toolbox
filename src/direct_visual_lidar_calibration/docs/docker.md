# Docker images

本仓库仅维护 **ROS 2 Humble** Docker 镜像：

- [koide3/direct_visual_lidar_calibration:humble ![Docker Image Size (tag)](https://img.shields.io/docker/image-size/koide3/direct_visual_lidar_calibration/humble)](https://hub.docker.com/repository/docker/koide3/direct_visual_lidar_calibration)

本地构建：

```bash
docker build -f docker/humble/Dockerfile -t direct_visual_lidar_calibration:humble .
# 可选（含 SuperGlue，注意许可证）:
# docker build -f docker/humble/Dockerfile_with_superglue -t direct_visual_lidar_calibration:humble-superglue .
```

!!!warning
    We avoided including SuperGlue in our images to avoid contamination of its strict license.
    If you need the automatic image matching, you must build a docker image with [Dockerfile_with_superglue](https://github.com/koide3/direct_visual_lidar_calibration/tree/main/docker/humble) at your own risk.

## Pull image

```bash
docker pull koide3/direct_visual_lidar_calibration:humble
```

## Run programs

**Example1**: Run preprocessing
```bash
docker run \
  --rm \
  -v /path/to/input/bags:/tmp/input_bags \
  -v /path/to/save/result:/tmp/preprocessed \
  koide3/direct_visual_lidar_calibration:humble \
  ros2 run direct_visual_lidar_calibration preprocess -a /tmp/input_bags /tmp/preprocessed
```

**Example2**: Run preprocessing with GUI
```bash
docker run \
  --rm \
  --net host \
  --gpus all \
  -e DISPLAY=$DISPLAY \
  -v $HOME/.Xauthority:/root/.Xauthority \
  -v /path/to/input/bags:/tmp/input_bags \
  -v /path/to/save/result:/tmp/preprocessed \
  koide3/direct_visual_lidar_calibration:humble \
  ros2 run direct_visual_lidar_calibration preprocess -a -v /tmp/input_bags /tmp/preprocessed
```

## Examples

See also [Calibration example](example.md) page.

<details>
  <summary>Full commands for Livox-camera calibration example on docker (ROS2)</summary>
```bash
bag_path=$(realpath livox)
preprocessed_path=$(realpath livox_preprocessed)

# Preprocessing
docker run \
  --rm \
  --net host \
  --gpus all \
  -e DISPLAY=$DISPLAY \
  -v $HOME/.Xauthority:/root/.Xauthority \
  -v $bag_path:/tmp/input_bags \
  -v $preprocessed_path:/tmp/preprocessed \
  koide3/direct_visual_lidar_calibration:humble \
  ros2 run direct_visual_lidar_calibration preprocess -av /tmp/input_bags /tmp/preprocessed

# Initial guess
docker run \
  --rm \
  --net host \
  --gpus all \
  -e DISPLAY=$DISPLAY \
  -v $HOME/.Xauthority:/root/.Xauthority \
  -v $preprocessed_path:/tmp/preprocessed \
  koide3/direct_visual_lidar_calibration:humble \
  ros2 run direct_visual_lidar_calibration initial_guess_manual /tmp/preprocessed

# Fine registration
docker run \
  --rm \
  --net host \
  --gpus all \
  -e DISPLAY=$DISPLAY \
  -v $HOME/.Xauthority:/root/.Xauthority \
  -v $preprocessed_path:/tmp/preprocessed \
  koide3/direct_visual_lidar_calibration:humble \
  ros2 run direct_visual_lidar_calibration calibrate /tmp/preprocessed

# Result inspection
docker run \
  --rm \
  --net host \
  --gpus all \
  -e DISPLAY=$DISPLAY \
  -v $HOME/.Xauthority:/root/.Xauthority \
  -v $preprocessed_path:/tmp/preprocessed \
  koide3/direct_visual_lidar_calibration:humble \
  ros2 run direct_visual_lidar_calibration viewer /tmp/preprocessed
```
</details>