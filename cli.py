#!/usr/bin/env python3
"""
Command-line interface for hierarchical config merging.
"""

import argparse
import json
import yaml
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

import hierarchical_config_merging as hcm

def main():
    parser = argparse.ArgumentParser(
        description="Hierarchical YAML config merger"
    )
    parser.add_argument(
        "base_dir",
        help="Base directory to search for YAML configs"
    )
    parser.add_argument(
        "target_path",
        help="Target path to determine hierarchy inclusion"
    )
    parser.add_argument(
        "--implementation",
        choices=["python", "rust"],
        default="python",
        help="Implementation to use (python or rust)"
    )
    parser.add_argument(
        "--output",
        choices=["json", "yaml"],
        default="json",
        help="Output format (json or yaml)"
    )
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    target_path = Path(args.target_path)
    
    if args.implementation == "python":
        merged_config, errors = hcm.merge_hierarchical_configs(base_dir, target_path)
    else:  # rust
        merged_config, errors = hcm.rust_merge_hierarchical_configs(
            str(base_dir), str(target_path)
        )
    
    # Print any errors
    for error in errors:
        print(f"⚠️  {error}", file=sys.stderr)
    
    # Output the merged config
    if args.output == "json":
        print(json.dumps(merged_config, indent=2, ensure_ascii=False))
    else:  # yaml
        print(yaml.dump(merged_config, default_flow_style=False, sort_keys=False))

if __name__ == "__main__":
    import sys
    main()