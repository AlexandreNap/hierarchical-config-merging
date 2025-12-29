# Hierarchical Config Merging

This repository is a test project for Mistral Vibe coding on a simple utility: deep hierarchical configuration directory merging, implemented in both Python and Rust.

## Overview

The goal of this project is to explore and compare implementations of a hierarchical configuration merging system that:

1. Recursively traverses a directory structure
2. Merges YAML configuration files found at different hierarchy levels
3. Handles deep nesting and complex merge scenarios
4. Provides implementations in both Python and Rust for comparison

## Features

- **Deep Hierarchy Support**: Merge configurations from arbitrarily nested directory structures
- **YAML Format**: Uses YAML for human-readable configuration files
- **Dual Implementation**: Both Python and Rust implementations available
- **Benchmarking**: Compare performance between implementations
- **Test Suite**: Comprehensive tests to ensure correctness

## Structure

```
.
├── rust/                  # Rust implementation
├── src/                   # Python implementation
├── test_demo/             # Example configuration hierarchy
├── tests/                 # Test suite
├── benchmark_deep_hierarchy.py  # Performance benchmarking
├── cli.py                 # Simple cli to test util
└── Readme.md              # This file
```

## Getting Started

### Prerequisites

- uv with Python 3.12+
- Rust (for Rust implementation)

### Installation (+test+benchmarks)

```bash
# Clone the repository
git clone https://github.com/yourusername/hierarchical_config_merging.git
cd hierarchical_config_merging
bash build_and_run.sh
```

### Running Tests only

```bash
uv run pytest
```

### Running Benchmarks only

```bash
uv run benchmark_deep_hierarchy.py
```

## Usage

### Python API

```python
from hierarchical_config_merging import merge_hierarchical_configs
from pathlib import Path

# Merge configs for a specific target path within a base directory
base_dir = Path("test_demo")
target_path = Path("test_demo/a/b")
merged_config, errors = merge_hierarchical_configs(base_dir, target_path)

# Handle any errors
for error in errors:
    print(f"Warning: {error}")

print(merged_config)
```

### Rust API

```python
from hierarchical_config_merging import rust_merge_hierarchical_configs

# Rust implementation with same interface
merged_config, errors = rust_merge_hierarchical_configs("test_demo", "test_demo/a/b")
```

### Command Line Interface

```bash
# Basic usage
python cli.py base_dir target_path

# Example with test_demo
python cli.py test_demo test_demo/a/b

# Use Rust implementation and YAML output
python cli.py test_demo test_demo/a/b --implementation rust --output yaml
```

## Configuration Format

Configuration files should be named `config.yaml` and placed in directories. The merger will:

1. Start from the root directory
2. Recursively traverse subdirectories
3. Merge all `config.yaml` files found
4. Apply deep merge semantics (later values override earlier ones), merge is applied even on nested configs

Example structure:

```
test_demo/               # (base="test_demo")
├── config.yaml          # Base configuration
├── a/
│   ├── config.yaml      # Overrides base (use target="test_demo/a" to get this config as last config)
│   └── b/
│       └── config.yaml  # Further overrides (use target="test_demo/a/b" to get this config as last config)
```