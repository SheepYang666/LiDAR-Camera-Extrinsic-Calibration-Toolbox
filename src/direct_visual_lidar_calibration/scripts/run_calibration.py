#!/usr/bin/env python3
"""Run the full LiDAR–camera calibration pipeline from one YAML config."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

try:
  import yaml
except ImportError as exc:  # pragma: no cover
  raise SystemExit(
    'PyYAML is required. Install with: sudo apt install python3-yaml'
  ) from exc

PACKAGE = 'direct_visual_lidar_calibration'
ALL_STEPS = ('preprocess', 'initial_guess', 'calibrate', 'viewer')


def load_config(path: Path) -> dict:
  with path.open('r', encoding='utf-8') as f:
    data = yaml.safe_load(f)
  if not isinstance(data, dict):
    raise SystemExit(f'invalid config: expected a mapping at root ({path})')
  return data


def require_paths(cfg: dict) -> tuple[str, str]:
  paths = cfg.get('paths') or {}
  data_path = paths.get('data_path')
  dst_path = paths.get('dst_path')
  if not data_path or not dst_path:
    raise SystemExit("config 'paths' must define data_path and dst_path")
  return str(data_path), str(dst_path)


def ros2_run(executable: str, args: Sequence[str]) -> None:
  cmd = ['ros2', 'run', PACKAGE, executable, *args]
  print('\n==>', ' '.join(cmd), flush=True)
  result = subprocess.run(cmd, check=False)
  if result.returncode != 0:
    raise SystemExit(f'step failed ({executable}) with exit code {result.returncode}')


def maybe_add(flag: str, value, out: List[str], *, skip_zero: bool = False) -> None:
  if value is None:
    return
  if skip_zero and value == 0:
    return
  out.extend([flag, str(value)])


def run_preprocess(config_path: Path) -> None:
  ros2_run('preprocess', ['--config', str(config_path)])


def run_initial_guess(cfg: dict, dst_path: str) -> None:
  section = cfg.get('initial_guess') or {}
  method = str(section.get('method', 'manual')).lower()

  if method == 'manual':
    print('Opening initial_guess_manual (interact in GUI, then Save / close).')
    ros2_run('initial_guess_manual', [dst_path])
    return

  if method != 'auto':
    raise SystemExit(f"initial_guess.method must be 'auto' or 'manual' (got {method!r})")

  match_args: List[str] = [dst_path]
  maybe_add('--rotate_camera', section.get('rotate_camera'), match_args, skip_zero=True)
  maybe_add('--rotate_lidar', section.get('rotate_lidar'), match_args, skip_zero=True)
  maybe_add('--superglue', section.get('superglue'), match_args)
  if section.get('force_cpu'):
    match_args.append('--force_cpu')
  if section.get('show_keypoints'):
    match_args.append('--show_keypoints')
  ros2_run('find_matches_superglue.py', match_args)

  auto_args: List[str] = [dst_path]
  maybe_add('--ransac_iterations', section.get('ransac_iterations'), auto_args)
  maybe_add('--ransac_error_thresh', section.get('ransac_error_thresh'), auto_args)
  maybe_add('--robust_kernel_width', section.get('robust_kernel_width'), auto_args)
  ros2_run('initial_guess_auto', auto_args)


def run_calibrate(cfg: dict, dst_path: str) -> None:
  section = cfg.get('calibrate') or {}
  args: List[str] = [dst_path]
  maybe_add('--registration_type', section.get('registration_type'), args)
  maybe_add('--nid_bins', section.get('nid_bins'), args)
  maybe_add('--nelder_mead_init_step', section.get('nelder_mead_init_step'), args)
  maybe_add(
    '--nelder_mead_convergence_criteria',
    section.get('nelder_mead_convergence_criteria'),
    args,
  )
  if section.get('disable_culling'):
    args.append('--disable_culling')
  if section.get('auto_quit', True):
    args.append('--auto_quit')
  if section.get('background'):
    args.append('--background')
  ros2_run('calibrate', args)


def run_viewer(cfg: dict, dst_path: str) -> None:
  section = cfg.get('viewer') or {}
  if section.get('enabled', True) is False:
    print('viewer.enabled is false; skipping viewer')
    return
  ros2_run('viewer', [dst_path])


def parse_steps(raw: Optional[str]) -> List[str]:
  if not raw:
    return list(ALL_STEPS)
  steps = [s.strip() for s in raw.split(',') if s.strip()]
  unknown = [s for s in steps if s not in ALL_STEPS]
  if unknown:
    raise SystemExit(f'unknown steps: {unknown}; allowed: {", ".join(ALL_STEPS)}')
  return steps


def main(argv: Optional[Iterable[str]] = None) -> int:
  parser = argparse.ArgumentParser(
    description='Run preprocess → initial_guess → calibrate → viewer from one YAML config',
  )
  parser.add_argument('config', type=Path, help='Path to calibration.yaml')
  parser.add_argument(
    '--steps',
    default=None,
    help=f'Comma-separated subset of: {",".join(ALL_STEPS)}',
  )
  args = parser.parse_args(list(argv) if argv is not None else None)

  if shutil.which('ros2') is None:
    raise SystemExit('ros2 not found on PATH; source ROS and workspace setup.bash first')

  config_path = args.config.expanduser().resolve()
  if not config_path.is_file():
    raise SystemExit(f'config not found: {config_path}')

  cfg = load_config(config_path)
  _, dst_path = require_paths(cfg)
  steps = parse_steps(args.steps)

  print(f'config : {config_path}')
  print(f'dst    : {dst_path}')
  print(f'steps  : {", ".join(steps)}')

  for step in steps:
    if step == 'preprocess':
      run_preprocess(config_path)
    elif step == 'initial_guess':
      run_initial_guess(cfg, dst_path)
    elif step == 'calibrate':
      run_calibrate(cfg, dst_path)
    elif step == 'viewer':
      run_viewer(cfg, dst_path)

  print('\nPipeline finished.')
  return 0


if __name__ == '__main__':
  sys.exit(main())
