#!/bin/bash

# Script to demonstrate building and running the hierarchical config merging project with uv

echo "🚀 Building and running hierarchical config merging with uv"
echo ""

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first."
    exit 1
fi

# Check if Rust is available
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust is not installed. Please install Rust first."
    exit 1
fi

echo "✅ Prerequisites checked"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
uv sync --dev
echo ""

# Build the Rust extension
echo "🔧 Building Rust extension..."
uv run maturin develop
echo ""

# Run tests
echo "🧪 Running all tests..."
uv run pytest tests/ -v
echo ""

# Demo
# echo todo
echo "🎯 Running CLI demo tests..."
echo ""
echo "📁 Testing Python implementation on test_demo/a..."
uv run cli.py test_demo test_demo/a --implementation python
echo ""
echo "🦀 Testing Rust implementation on test_demo/a..."
uv run cli.py test_demo test_demo/a --implementation rust
echo ""
echo "📁 Testing Python implementation on test_demo/a/b (deeper hierarchy)..."
uv run cli.py test_demo test_demo/a/b --implementation python
echo ""
echo "🦀 Testing Rust implementation on test_demo/a/b (deeper hierarchy)..."
uv run cli.py test_demo test_demo/a/b --implementation rust
echo ""

# Test the Python implementation
echo "🧪 Benchmarking implementations..."
uv run benchmark_deep_hierarchy.py

echo "🎉 All done! The project is successfully built and running with uv."