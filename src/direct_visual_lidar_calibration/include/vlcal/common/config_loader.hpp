#pragma once

#include <string>
#include <vector>

namespace vlcal {

/**
 * Load paths + preprocess sections from a calibration YAML and convert them
 * into boost::program_options-compatible argv tokens (without argv[0]).
 *
 * Example tokens: "--data_path", "/raw", "--camera_intrinsics", "fx,fy,cx,cy"
 */
std::vector<std::string> preprocess_args_from_yaml(const std::string& config_path);

}  // namespace vlcal
