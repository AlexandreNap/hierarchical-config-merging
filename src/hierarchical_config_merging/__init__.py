# Python package for hierarchical config merging
# This package contains both Python and Rust implementations

# Import the Python implementation
from hierarchical_config_merging.config_merger import (
    find_yaml_files_in_hierarchy,
    parse_yaml_configs,
    merge_configs_by_depth,
    merge_hierarchical_configs,
    _deep_merge
)

# Import the Rust implementation
# do not pass python implementation on error, we prefer to raise it
try:
    from .hierarchical_config_merging import rust_merge_hierarchical_configs
except ImportError as e:
   raise e

# Expose all functions at the package level
__all__ = [
    'find_yaml_files_in_hierarchy',
    'parse_yaml_configs', 
    'merge_configs_by_depth',
    'merge_hierarchical_configs',
    '_deep_merge',
    'rust_merge_hierarchical_configs'
]