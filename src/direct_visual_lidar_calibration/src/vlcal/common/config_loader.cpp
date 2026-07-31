#include <vlcal/common/config_loader.hpp>

#include <sstream>
#include <stdexcept>

#include <yaml-cpp/yaml.h>

namespace vlcal {

namespace {

std::string join_doubles(const YAML::Node& node) {
  if (!node || !node.IsSequence()) {
    throw std::runtime_error("expected a YAML sequence of numbers");
  }

  std::ostringstream oss;
  for (std::size_t i = 0; i < node.size(); i++) {
    if (i) {
      oss << ',';
    }
    oss << node[i].as<double>();
  }
  return oss.str();
}

void push_flag(std::vector<std::string>& args, const char* flag, const YAML::Node& node) {
  if (node && node.as<bool>()) {
    args.emplace_back(flag);
  }
}

void push_string(std::vector<std::string>& args, const char* flag, const YAML::Node& node) {
  if (!node || node.IsNull()) {
    return;
  }
  const std::string value = node.as<std::string>();
  if (value.empty()) {
    return;
  }
  args.emplace_back(flag);
  args.emplace_back(value);
}

}  // namespace

std::vector<std::string> preprocess_args_from_yaml(const std::string& config_path) {
  YAML::Node root;
  try {
    root = YAML::LoadFile(config_path);
  } catch (const std::exception& e) {
    throw std::runtime_error(std::string("failed to load config YAML: ") + e.what());
  }

  std::vector<std::string> args;

  const YAML::Node paths = root["paths"];
  if (!paths) {
    throw std::runtime_error("config missing required 'paths' section");
  }
  if (!paths["data_path"] || !paths["dst_path"]) {
    throw std::runtime_error("config paths must contain 'data_path' and 'dst_path'");
  }

  args.emplace_back("--data_path");
  args.emplace_back(paths["data_path"].as<std::string>());
  args.emplace_back("--dst_path");
  args.emplace_back(paths["dst_path"].as<std::string>());

  const YAML::Node prep = root["preprocess"];
  if (!prep) {
    return args;
  }

  push_flag(args, "--auto_topic", prep["auto_topic"]);
  push_flag(args, "--dynamic_lidar_integration", prep["dynamic_lidar_integration"]);
  push_flag(args, "--visualize", prep["visualize"]);
  push_flag(args, "--verbose", prep["verbose"]);

  push_string(args, "--intensity_channel", prep["intensity_channel"]);
  push_string(args, "--camera_info_topic", prep["camera_info_topic"]);
  push_string(args, "--image_topic", prep["image_topic"]);
  push_string(args, "--points_topic", prep["points_topic"]);
  push_string(args, "--camera_model", prep["camera_model"]);

  if (prep["camera_intrinsics"]) {
    args.emplace_back("--camera_intrinsics");
    if (prep["camera_intrinsics"].IsSequence()) {
      args.emplace_back(join_doubles(prep["camera_intrinsics"]));
    } else {
      args.emplace_back(prep["camera_intrinsics"].as<std::string>());
    }
  }

  if (prep["camera_distortion_coeffs"]) {
    args.emplace_back("--camera_distortion_coeffs");
    if (prep["camera_distortion_coeffs"].IsSequence()) {
      args.emplace_back(join_doubles(prep["camera_distortion_coeffs"]));
    } else {
      args.emplace_back(prep["camera_distortion_coeffs"].as<std::string>());
    }
  }

  if (prep["k_neighbors"]) {
    args.emplace_back("--k_neighbors");
    args.emplace_back(std::to_string(prep["k_neighbors"].as<int>()));
  }
  if (prep["voxel_resolution"]) {
    args.emplace_back("--voxel_resolution");
    args.emplace_back(prep["voxel_resolution"].as<std::string>());
  }
  if (prep["min_distance"]) {
    args.emplace_back("--min_distance");
    args.emplace_back(prep["min_distance"].as<std::string>());
  }
  if (prep["bag_id"]) {
    args.emplace_back("--bag_id");
    args.emplace_back(std::to_string(prep["bag_id"].as<int>()));
  }
  if (prep["first_n_bags"]) {
    args.emplace_back("--first_n_bags");
    args.emplace_back(std::to_string(prep["first_n_bags"].as<int>()));
  }

  return args;
}

}  // namespace vlcal
