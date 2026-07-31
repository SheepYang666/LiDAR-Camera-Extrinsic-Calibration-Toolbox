# Installation

!!!note
    We provide docker images so that the user can do calibration without installation: [Docker images](docker.md)

## Dependencies

- [ROS 2 Humble](https://docs.ros.org/en/humble/)
- [PCL](https://pointclouds.org/)
- [OpenCV](https://opencv.org/)
- [GTSAM](https://gtsam.org/)
- [Ceres](http://ceres-solver.org/)
- [Iridescence](https://github.com/koide3/iridescence)
- [SuperGlue](https://github.com/magicleap/SuperGluePretrainedNetwork) [optional]

## Install Common dependencies

```bash
# Install dependencies
sudo apt install libomp-dev libboost-all-dev libglm-dev libglfw3-dev libpng-dev libjpeg-dev

# Install GTSAM
git clone https://github.com/borglab/gtsam
cd gtsam && git checkout 4.2a9
mkdir build && cd build
# For Ubuntu 22.04, add -DGTSAM_USE_SYSTEM_EIGEN=ON
cmake .. -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF \
         -DGTSAM_BUILD_TESTS=OFF \
         -DGTSAM_WITH_TBB=OFF \
         -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF
make -j$(nproc)
sudo make install

# Install Ceres
git clone --recurse-submodules https://github.com/ceres-solver/ceres-solver
cd ceres-solver
git checkout e47a42c2957951c9fafcca9995d9927e15557069
mkdir build && cd build
cmake .. -DBUILD_EXAMPLES=OFF -DBUILD_TESTING=OFF -DUSE_CUDA=OFF
make -j$(nproc)
sudo make install

# Install Iridescence for visualization
git clone https://github.com/koide3/iridescence --recursive
mkdir iridescence/build && cd iridescence/build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
```

## Install SuperGlue (Optional)

!!!warning
    [SuperGlue](https://github.com/magicleap/SuperGluePretrainedNetwork.git) is not allowed to be used for commercial purposes. You must carefully check and follow its licensing conditions.

```bash
pip3 install numpy opencv-python torch matplotlib
git clone https://github.com/magicleap/SuperGluePretrainedNetwork.git

echo 'export PYTHONPATH=$PYTHONPATH:/path/to/SuperGluePretrainedNetwork' >> ~/.bashrc
source ~/.bashrc
```

## Build direct_visual_lidar_calibration

本仓库仅支持 **ROS 2 Humble**：

```bash
cd ~/ros2_ws/src
git clone https://github.com/SheepYang666/LiDAR-Camera-Extrinsic-Calibration-Toolbox.git
# 或将 direct_visual_lidar_calibration 放进工作区 src/
cd .. && colcon build --packages-select direct_visual_lidar_calibration
```

工作区级安装与编译步骤见仓库根目录 [docs/install.md](../../../docs/install.md)。
