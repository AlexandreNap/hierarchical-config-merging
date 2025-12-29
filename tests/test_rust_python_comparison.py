#!/usr/bin/env python3
"""
Comparison tests between Python and Rust implementations.
"""

import tempfile
import yaml
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import hierarchical_config_merging as hcm

def test_python_rust_comparison_basic():
    """Test that Python and Rust implementations produce the same results."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "aaa"
        target_dir = base_dir / "env" / "prod" / "region" / "eu"
        
        # Create directory structure
        base_dir.mkdir(parents=True, exist_ok=True)
        (base_dir / "env").mkdir(exist_ok=True)
        (base_dir / "env" / "prod").mkdir(exist_ok=True)
        (base_dir / "env" / "prod" / "region").mkdir(exist_ok=True)
        (base_dir / "env" / "prod" / "region" / "eu").mkdir(exist_ok=True)
        
        # Create YAML configs
        configs = {
            "": {
                "name": "base_config",
                "settings": {
                    "timeout": 30,
                    "retries": 3
                }
            },
            "env/prod": {
                "name": "production_config",
                "settings": {
                    "timeout": 60,
                    "ssl": True
                },
                "database": {
                    "host": "prod.db.example.com"
                }
            },
            "env/prod/region/eu": {
                "name": "eu_production_config",
                "settings": {
                    "timeout": 90
                },
                "database": {
                    "host": "eu.prod.db.example.com",
                    "region": "eu-west-1"
                }
            }
        }
        
        # Write config files
        for rel_path, config_data in configs.items():
            config_path = base_dir / rel_path / "config.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
        
        # Test Python implementation
        py_merged, py_errors = hcm.merge_hierarchical_configs(base_dir, target_dir)
        
        # Test Rust implementation
        rust_merged, rust_errors = hcm.rust_merge_hierarchical_configs(
            str(base_dir), str(target_dir)
        )
        
        # Convert Rust numbers to int where appropriate for comparison
        def convert_rust_numbers(obj):
            if isinstance(obj, dict):
                return {k: convert_rust_numbers(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_rust_numbers(v) for v in obj]
            elif isinstance(obj, float) and obj.is_integer():
                return int(obj)
            else:
                return obj
        
        rust_merged_converted = convert_rust_numbers(rust_merged)
        
        # Compare results
        assert rust_merged_converted == py_merged, f"Merged configs differ:\nPython: {py_merged}\nRust: {rust_merged_converted}"
        assert rust_errors == py_errors, f"Errors differ:\nPython: {py_errors}\nRust: {rust_errors}"
        
        print("✓ Python and Rust implementations produce identical results")


def test_python_rust_comparison_collision():
    """Test collision handling comparison."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "aaa"
        target_dir = base_dir / "level1" / "level2"
        
        # Create directory structure
        base_dir.mkdir(parents=True, exist_ok=True)
        (base_dir / "level1").mkdir(exist_ok=True)
        (base_dir / "level1" / "level2").mkdir(exist_ok=True)
        
        # Create configs with same key at same depth
        (base_dir / "level1" / "config1.yaml").write_text("key: value1")
        (base_dir / "level1" / "config2.yaml").write_text("key: value2")
        (base_dir / "level1" / "level2" / "config.yaml").write_text("key: value3")
        
        # Test Python implementation
        py_merged, py_errors = hcm.merge_hierarchical_configs(base_dir, target_dir)
        
        # Test Rust implementation
        rust_merged, rust_errors = hcm.rust_merge_hierarchical_configs(
            str(base_dir), str(target_dir)
        )
        
        # Both should detect collision
        assert len(py_errors) > 0, "Python should detect collision"
        assert len(rust_errors) > 0, "Rust should detect collision"
        
        # Both should have same key value (deepest wins)
        assert py_merged["key"] == "value3"
        assert rust_merged["key"] == "value3"
        
        print("✓ Python and Rust collision handling is consistent")


def test_python_rust_comparison_no_files():
    """Test empty directory handling."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "empty"
        target_dir = base_dir / "subdir"
        
        base_dir.mkdir(parents=True)
        target_dir.mkdir(parents=True)
        
        # Test Python implementation
        py_merged, py_errors = hcm.merge_hierarchical_configs(base_dir, target_dir)
        
        # Test Rust implementation
        rust_merged, rust_errors = hcm.rust_merge_hierarchical_configs(
            str(base_dir), str(target_dir)
        )
        
        # Both should return empty config and error message
        assert py_merged == {}
        assert rust_merged == {}
        assert len(py_errors) > 0
        assert len(rust_errors) > 0
        
        print("✓ Python and Rust empty directory handling is consistent")


if __name__ == "__main__":
    test_python_rust_comparison_basic()
    test_python_rust_comparison_collision()
    test_python_rust_comparison_no_files()
    print("\n🎉 All comparison tests passed! Python and Rust implementations are consistent.")