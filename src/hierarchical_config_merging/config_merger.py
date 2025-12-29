#!/usr/bin/env python3
"""
Hierarchical config merging implementation.

This module provides functionality to merge hierarchical YAML configurations
based on directory depth priority.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict


def find_yaml_files_in_hierarchy(base_dir: Path, target_path: Path) -> List[Path]:
    """
    Find all YAML files in a directory hierarchy where parent directories 
    are included in the target path.
    
    Args:
        base_dir: The base directory to search from
        target_path: The target path to check inclusion
        
    Returns:
        List of YAML file paths that are included in the hierarchy
        
    Example:
        base = "aaa/"
        target = "aaa/a/a/b"
        Returns files from:
        - "aaa/*.yaml" (included)
        - "aaa/a/a/b/*.yaml" (included)
        - "aaa/a/c/b/*.yaml" (not included - "a/c/b" not in "a/a/b")
    """
    base_dir = base_dir.resolve()
    target_path = target_path.resolve()
    
    # Ensure target_path is within base_dir
    if not str(target_path).startswith(str(base_dir)):
        raise ValueError(f"Target path {target_path} is not within base directory {base_dir}")
    
    yaml_files = []
    
    # Get relative path from base to target
    target_relative = target_path.relative_to(base_dir)
    target_parts = target_relative.parts
    
    # Walk through the directory tree
    for root, dirs, files in os.walk(base_dir):
        root_path = Path(root)
        root_relative = root_path.relative_to(base_dir)
        root_parts = root_relative.parts
        
        # Check if this directory is included in target hierarchy
        # The root should be either:
        # 1. The base directory itself (always included)
        # 2. A parent directory in the target path hierarchy
        if (len(root_parts) == 0 or  # Base directory
            (len(root_parts) <= len(target_parts) and 
             root_parts == target_parts[:len(root_parts)])):
            # This directory is in the hierarchy, add all YAML files
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    yaml_files.append(root_path / file)
    
    return yaml_files


def parse_yaml_configs(yaml_files: List[Path]) -> Dict[str, Dict[str, Any]]:
    """
    Parse all YAML config files into a dictionary mapping.
    
    Args:
        yaml_files: List of YAML file paths
        
    Returns:
        Dictionary mapping file paths to parsed config dictionaries
        
    Raises:
        Exception: If any YAML file cannot be parsed
    """
    configs = {}
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                configs[str(yaml_file)] = config
        except Exception as e:
            raise Exception(f"Failed to parse {yaml_file}: {e}")
    
    return configs


def merge_configs_by_depth(configs: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Merge configs based on directory depth priority.
    
    Deeper directories have higher priority and overwrite collisions.
    Logs errors when key collisions occur at the same priority level.
    
    Args:
        configs: Dictionary mapping file paths to config dictionaries
        
    Returns:
        Tuple of (merged_config, errors) where errors is a list of collision messages
    """
    if not configs:
        return {}, []
    
    # Group configs by depth (directory level)
    depth_groups = defaultdict(list)
    
    for file_path, config in configs.items():
        path_obj = Path(file_path)
        # Count directory depth relative to the common base
        depth = len(path_obj.parts)
        depth_groups[depth].append((file_path, config))
    
    merged_config = {}
    errors = []
    
    # Process configs from shallowest to deepest
    for depth in sorted(depth_groups.keys()):
        depth_configs = depth_groups[depth]
        
        # Check for key collisions at the same depth
        all_keys_at_depth = set()
        key_sources = {}
        
        for file_path, config in depth_configs:
            for key in config.keys():
                if key in all_keys_at_depth:
                    # Collision at same depth
                    existing_source = key_sources[key]
                    errors.append(f"Key collision at depth {depth}: '{key}' found in both {existing_source} and {file_path}")
                else:
                    all_keys_at_depth.add(key)
                    key_sources[key] = file_path
        
        # Merge configs at this depth
        for file_path, config in depth_configs:
            merged_config = _deep_merge(merged_config, config)
    
    return merged_config, errors


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries.
    
    Values from override take precedence over base.
    Nested dictionaries are merged recursively.
    """
    result = base.copy()
    
    for key, value in override.items():
        if (key in result and 
            isinstance(result[key], dict) and 
            isinstance(value, dict)):
            # Recursively merge nested dictionaries
            result[key] = _deep_merge(result[key], value)
        else:
            # Override with new value
            result[key] = value
    
    return result


def merge_hierarchical_configs(base_dir: Path, target_path: Path) -> Tuple[Dict[str, Any], List[str]]:
    """
    Main function to merge hierarchical configurations.
    
    Args:
        base_dir: Base directory to search for YAML configs
        target_path: Target path to determine hierarchy inclusion
        
    Returns:
        Tuple of (merged_config, errors) where errors contains any collision messages
    """
    # Find YAML files in hierarchy
    yaml_files = find_yaml_files_in_hierarchy(base_dir, target_path)
    
    if not yaml_files:
        return {}, [f"No YAML files found in hierarchy from {base_dir} to {target_path}"]
    
    # Parse YAML configs
    configs = parse_yaml_configs(yaml_files)
    
    # Merge configs by depth
    merged_config, errors = merge_configs_by_depth(configs)
    
    return merged_config, errors