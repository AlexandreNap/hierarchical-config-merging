#!/usr/bin/env python3
"""
Comprehensive tests for hierarchical config merging.

These tests will also be used for the Rust implementation via bindings.
"""

import tempfile
import yaml
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

import hierarchical_config_merging as hcm


def test_find_yaml_files_in_hierarchy_basic():
    """Test basic hierarchy inclusion logic."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "aaa"
        target_dir = base_dir / "a" / "a" / "b"
        
        # Create directory structure
        base_dir.mkdir(parents=True)
        (base_dir / "a").mkdir()
        (base_dir / "a" / "a").mkdir()
        (base_dir / "a" / "a" / "b").mkdir()
        (base_dir / "a" / "c").mkdir()
        (base_dir / "a" / "c" / "b").mkdir()
        
        # Create YAML files
        (base_dir / "config.yaml").write_text("base: config")
        (base_dir / "a" / "config.yaml").write_text("a: config")
        (base_dir / "a" / "a" / "b" / "config.yaml").write_text("target: config")
        (base_dir / "a" / "c" / "b" / "config.yaml").write_text("excluded: config")
        
        # Find files in hierarchy
        found_files = hcm.find_yaml_files_in_hierarchy(base_dir, target_dir)
        
        # Should include base, a, and a/a/b but not a/c/b
        expected_files = [
            base_dir / "config.yaml",
            base_dir / "a" / "config.yaml",
            base_dir / "a" / "a" / "b" / "config.yaml"
        ]
        
        assert len(found_files) == 3
        for expected_file in expected_files:
            assert expected_file in found_files
        
        # Should not include a/c/b
        excluded_file = base_dir / "a" / "c" / "b" / "config.yaml"
        assert excluded_file not in found_files


def test_find_yaml_files_in_hierarchy_target_outside_base():
    """Test error when target is outside base directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "aaa"
        target_dir = Path(temp_dir) / "bbb"
        
        base_dir.mkdir()
        target_dir.mkdir()
        
        with pytest.raises(ValueError, match="Target path .* is not within base directory"):
            hcm.find_yaml_files_in_hierarchy(base_dir, target_dir)


def test_parse_yaml_configs():
    """Test YAML config parsing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_files = []
        
        # Create test YAML files
        for i in range(3):
            config_file = Path(temp_dir) / f"config{i}.yaml"
            config_data = {
                "name": f"config{i}",
                "value": i * 10,
                "nested": {
                    "key": f"nested_value{i}"
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)
            
            config_files.append(config_file)
        
        # Parse configs
        configs = hcm.parse_yaml_configs(config_files)
        
        # Verify parsing
        assert len(configs) == 3
        for i, config_file in enumerate(config_files):
            assert str(config_file) in configs
            config = configs[str(config_file)]
            assert config["name"] == f"config{i}"
            assert config["value"] == i * 10
            assert config["nested"]["key"] == f"nested_value{i}"


def test_parse_yaml_configs_invalid_yaml():
    """Test error handling for invalid YAML."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(Exception, match="Failed to parse"):
            hcm.parse_yaml_configs([config_file])


def test_deep_merge_basic():
    """Test basic dictionary merging."""
    base = {"a": 1, "b": 2, "c": {"nested": "base"}}
    override = {"b": 3, "d": 4, "c": {"nested": "override", "new": "value"}}
    
    result = hcm._deep_merge(base, override)
    
    expected = {
        "a": 1,
        "b": 3,
        "c": {"nested": "override", "new": "value"},
        "d": 4
    }
    
    assert result == expected


def test_deep_merge_nested():
    """Test deep nested merging."""
    base = {
        "app": {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "cache": {"enabled": True}
        }
    }
    
    override = {
        "app": {
            "database": {
                "host": "prod.example.com",
                "ssl": True
            },
            "logging": {"level": "debug"}
        }
    }
    
    result = hcm._deep_merge(base, override)
    
    expected = {
        "app": {
            "database": {
                "host": "prod.example.com",
                "port": 5432,
                "ssl": True
            },
            "cache": {"enabled": True},
            "logging": {"level": "debug"}
        }
    }
    
    assert result == expected


def test_merge_configs_by_depth_basic():
    """Test merging configs by directory depth."""
    configs = {
        "/base/config.yaml": {"key1": "base_value", "key2": "base_value2"},
        "/base/level1/config.yaml": {"key2": "level1_value", "key3": "level1_value3"},
        "/base/level1/level2/config.yaml": {"key3": "level2_value", "key4": "level2_value4"}
    }
    
    merged_config, errors = hcm.merge_configs_by_depth(configs)
    
    # Should have no errors (no collisions at same depth)
    assert len(errors) == 0
    
    # Should merge with deepest values taking precedence
    expected = {
        "key1": "base_value",
        "key2": "level1_value",
        "key3": "level2_value",
        "key4": "level2_value4"
    }
    
    assert merged_config == expected


def test_merge_configs_by_depth_collision():
    """Test error detection for key collisions at same depth."""
    configs = {
        "/base/level1/config1.yaml": {"key": "value1"},
        "/base/level1/config2.yaml": {"key": "value2"},
        "/base/level1/level2/config.yaml": {"key": "value3"}
    }
    
    merged_config, errors = hcm.merge_configs_by_depth(configs)
    
    # Should detect collision at same depth
    assert len(errors) == 1
    assert "Key collision at depth" in errors[0]
    assert "key" in errors[0]
    
    # Should still merge (last one wins for collision)
    assert "key" in merged_config


def test_merge_hierarchical_configs_integration():
    """Test full integration of hierarchical config merging."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "aaa"
        target_dir = base_dir / "env" / "prod" / "region" / "eu"
        
        # Create directory structure
        base_dir.mkdir(parents=True)
        (base_dir / "env").mkdir()
        (base_dir / "env" / "prod").mkdir()
        (base_dir / "env" / "prod" / "region").mkdir()
        (base_dir / "env" / "prod" / "region" / "eu").mkdir()
        
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
        
        # Merge configs
        merged_config, errors = hcm.merge_hierarchical_configs(base_dir, target_dir)
        
        # Should have no errors
        assert len(errors) == 0
        
        # Verify merged result
        expected = {
            "name": "eu_production_config",
            "settings": {
                "timeout": 90,
                "retries": 3,
                "ssl": True
            },
            "database": {
                "host": "eu.prod.db.example.com",
                "region": "eu-west-1"
            }
        }
        
        assert merged_config == expected


def test_merge_hierarchical_configs_no_files():
    """Test handling when no YAML files are found."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "empty"
        target_dir = base_dir / "subdir"
        
        base_dir.mkdir(parents=True)
        
        merged_config, errors = hcm.merge_hierarchical_configs(base_dir, target_dir)
        
        assert merged_config == {}
        assert len(errors) == 1
        assert "No YAML files found" in errors[0]


def test_merge_hierarchical_configs_collision():
    """Test collision detection in full integration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "aaa"
        target_dir = base_dir / "level1" / "level2"
        
        # Create directory structure
        base_dir.mkdir(parents=True)
        (base_dir / "level1").mkdir()
        (base_dir / "level1" / "level2").mkdir()
        
        # Create configs with same key at same depth
        (base_dir / "level1" / "config1.yaml").write_text("key: value1")
        (base_dir / "level1" / "config2.yaml").write_text("key: value2")
        (base_dir / "level1" / "level2" / "config.yaml").write_text("key: value3")
        
        # Merge configs
        merged_config, errors = hcm.merge_hierarchical_configs(base_dir, target_dir)
        
        # Should detect collision
        assert len(errors) == 1
        assert "Key collision" in errors[0]
        
        # Should still merge (deepest value wins)
        assert merged_config["key"] == "value3"