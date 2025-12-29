#!/usr/bin/env python3
"""
Deep Hierarchy Benchmark with Multiple Targets
Tests complex organizational structures:
company/continent/country/size/employee_resource/employee_person
Evaluates inheritance and collisions at each hierarchy level.
"""

import os
import sys
import time
import tempfile
import yaml
import random
import string
import statistics
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

import hierarchical_config_merging as hcm


class DeepHierarchyGenerator:
    """Generate deep organizational hierarchies with inheritance and collisions."""
    
    def __init__(self):
        self.config_id = 0
    
    def generate_realistic_string(self, prefix: str = "config", length: int = 12) -> str:
        """Generate realistic business-like strings."""
        business_terms = ["corp", "inc", "llc", "ltd", "group", "solutions", "tech", "systems"]
        return f"{prefix}_{random.choice(business_terms)}_{''.join(random.choices(string.ascii_lowercase, k=length))}"
    
    def generate_config_section(self, section_type: str, level: int) -> Dict[str, Any]:
        """Generate configuration section with level-specific settings."""
        base_settings = {
            "timeout_seconds": 30 + (level * 5),
            "retries": 3 + (level % 3),
            "logging_level": random.choice(["debug", "info", "warning", "error"]),
            "max_connections": 50 + (level * 10)
        }
        
        if section_type == "global":
            return {
                **base_settings,
                "company_policy": {
                    "compliance_level": random.choice(["low", "medium", "high", "strict"]),
                    "audit_interval_days": 30 + (level * 7),
                    "data_retention_years": 1 + (level % 5)
                }
            }
        
        elif section_type == "security":
            return {
                **base_settings,
                "security": {
                    "encryption": random.choice(["AES-256", "RSA-2048", "ChaCha20"]),
                    "mfa_required": random.choice([True, False]),
                    "session_timeout_minutes": 15 + (level * 5),
                    "password_policy": random.choice(["basic", "medium", "strong"])
                }
            }
        
        elif section_type == "network":
            return {
                **base_settings,
                "network": {
                    "protocol": random.choice(["http", "https", "grpc"]),
                    "timeout_ms": 1000 + (level * 100),
                    "retries": 2 + (level % 4),
                    "compression": random.choice(["none", "gzip", "brotli"])
                }
            }
        
        else:  # resources
            return {
                **base_settings,
                "resources": {
                    "cpu": {
                        "min": 0.5 + (level * 0.25),
                        "max": 2.0 + (level * 0.5)
                    },
                    "memory_mb": {
                        "min": 256 + (level * 128),
                        "max": 1024 + (level * 256)
                    }
                }
            }
    
    def create_deep_hierarchy(self, base_dir: Path) -> Dict[str, List[Path]]:
        """Create deep organizational hierarchy: company/continent/country/size/resource/person."""
        
        print("  Creating deep hierarchy: company → continent → country → size → resource → person")
        
        # Company level (1 company)
        company_dir = base_dir / "acme_corporation"
        company_dir.mkdir(parents=True)
        
        # Company-wide configs (will be inherited)
        company_configs = []
        for config_type in ["global", "security", "network", "resources"]:
            config_file = company_dir / f"{config_type}_policy.yaml"
            config = self.generate_config_section(config_type, 0)  # Level 0
            
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            company_configs.append(config_file)
        
        # Continents (5 continents)
        continents = ["north_america", "south_america", "europe", "asia", "africa"]
        continent_dirs = []
        
        for continent in continents:
            continent_dir = company_dir / "regions" / continent
            continent_dir.mkdir(parents=True)
            
            # Continent-level configs (override some company settings)
            for config_type in ["global", "security", "network"]:
                config_file = continent_dir / f"{config_type}_policy.yaml"
                config = self.generate_config_section(config_type, 1)  # Level 1
                
                # Create intentional collisions with company level
                if config_type == "security":
                    config["security"]["mfa_required"] = True  # Override company policy
                
                with open(config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
            
            continent_dirs.append(continent_dir)
        
        # Countries (3 per continent)
        countries_per_continent = 3
        country_dirs = []
        
        for continent_dir in continent_dirs:
            continent_name = continent_dir.name.split('_')[-1].capitalize()
            
            for country_id in range(countries_per_continent):
                country_code = f"{continent_name[:2]}{country_id:02d}"
                country_dir = continent_dir / f"country_{country_code}"
                country_dir.mkdir(parents=True)
                
                # Country-level configs (override continent settings)
                for config_type in ["global", "network"]:
                    config_file = country_dir / f"{config_type}_policy.yaml"
                    config = self.generate_config_section(config_type, 2)  # Level 2
                    
                    # Create collisions
                    if config_type == "network":
                        config["network"]["timeout_ms"] = 2000 + (country_id * 100)  # Override
                    
                    with open(config_file, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                
                country_dirs.append(country_dir)
        
        # Company sizes (small, medium, large per country)
        size_dirs = []
        
        for country_dir in country_dirs:
            for size in ["small", "medium", "large"]:
                size_dir = country_dir / f"size_{size}"
                size_dir.mkdir(parents=True)
                
                # Size-specific configs
                config_file = size_dir / "resources_policy.yaml"
                config = self.generate_config_section("resources", 3)  # Level 3
                
                # Size-specific overrides
                multiplier = {"small": 0.5, "medium": 1.0, "large": 2.0}[size]
                if "resources" in config:
                    config["resources"]["cpu"]["min"] *= multiplier
                    config["resources"]["cpu"]["max"] *= multiplier
                    config["resources"]["memory_mb"]["min"] = int(config["resources"]["memory_mb"]["min"] * multiplier)
                    config["resources"]["memory_mb"]["max"] = int(config["resources"]["memory_mb"]["max"] * multiplier)
                
                with open(config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                
                size_dirs.append(size_dir)
        
        # Employee resources (5 per size)
        resource_dirs = []
        
        for size_dir in size_dirs:
            for resource_id in range(5):
                resource_dir = size_dir / f"resource_{resource_id:02d}"
                resource_dir.mkdir(parents=True)
                
                # Resource-specific configs
                for config_type in ["global", "security"]:
                    config_file = resource_dir / f"{config_type}_policy.yaml"
                    config = self.generate_config_section(config_type, 4)  # Level 4
                    
                    with open(config_file, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                
                resource_dirs.append(resource_dir)
        
        # Individual employees (3 per resource) - leaf nodes
        employee_dirs = []
        
        for resource_dir in resource_dirs:
            for employee_id in range(3):
                employee_dir = resource_dir / f"employee_{employee_id:03d}"
                employee_dir.mkdir(parents=True)
                
                # Employee-specific configs (multiple files per employee)
                for config_type in ["main", "personal", "security", "network"]:
                    config_file = employee_dir / f"{config_type}_config.yaml"
                    
                    if config_type == "main":
                        config = {
                            "employee_id": f"EMP-{employee_id:06d}",
                            "name": f"Employee {employee_id}",
                            "role": random.choice(["developer", "manager", "analyst", "designer"]),
                            "department": random.choice(["engineering", "sales", "marketing", "support"])
                        }
                    elif config_type == "personal":
                        config = {
                            "preferences": {
                                "theme": random.choice(["light", "dark", "system"]),
                                "language": random.choice(["en", "es", "fr", "de", "ja"]),
                                "notifications": random.choice(["email", "sms", "push", "none"])
                            },
                            "timezone": random.choice(["UTC-8", "UTC-5", "UTC+1", "UTC+9"])
                        }
                    else:
                        config = self.generate_config_section(config_type, 5)  # Level 5
                    
                    with open(config_file, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                
                employee_dirs.append(employee_dir)
        
        # Define multiple target paths for testing
        targets = {
            "company_root": company_dir,
            "continent_middle": continent_dirs[len(continent_dirs) // 2],
            "country_middle": country_dirs[len(country_dirs) // 2],
            "size_large": next(d for d in size_dirs if "large" in str(d)),
            "resource_middle": resource_dirs[len(resource_dirs) // 2],
            "employee_leaf": employee_dirs[len(employee_dirs) // 2]
        }
        
        return {
            'base_dir': company_dir,
            'targets': targets,
            'stats': {
                'companies': 1,
                'continents': len(continents),
                'countries': len(country_dirs),
                'sizes': len(size_dirs),
                'resources': len(resource_dirs),
                'employees': len(employee_dirs),
                'total_files': (
                    len(company_configs) + 
                    len(continent_dirs) * 3 + 
                    len(country_dirs) * 2 + 
                    len(size_dirs) * 1 + 
                    len(resource_dirs) * 2 + 
                    len(employee_dirs) * 4
                )
            }
        }


class MultiTargetBenchmark:
    """Run benchmarks on multiple targets in deep hierarchy."""
    
    def __init__(self):
        self.results = {}
    
    def run_benchmark(self, base_dir: Path, target_path: Path, target_name: str, implementation: str) -> float:
        """Run single benchmark execution."""
        start_time = time.time()
        
        if implementation == "python":
            config, errors = hcm.merge_hierarchical_configs(base_dir, target_path)
        else:
            config, errors = hcm.rust_merge_hierarchical_configs(str(base_dir), str(target_path))
        
        return time.time() - start_time
    
    def run_multi_target_benchmark(self, scenario_name: str, hierarchy_info: Dict, executions: int = 50):
        """Run benchmark on multiple targets."""
        print(f"\n🎯 Running {scenario_name} Benchmark")
        print("=" * 60)
        
        base_dir = hierarchy_info['base_dir']
        targets = hierarchy_info['targets']
        stats = hierarchy_info['stats']
        
        print(f"Hierarchy complexity:")
        print(f"  Companies: {stats['companies']}")
        print(f"  Continents: {stats['continents']}")
        print(f"  Countries: {stats['countries']}")
        print(f"  Sizes: {stats['sizes']}")
        print(f"  Resources: {stats['resources']}")
        print(f"  Employees: {stats['employees']}")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Targets to test: {len(targets)}")
        
        # Test each target
        all_python_times = []
        all_rust_times = []
        
        for target_name, target_path in targets.items():
            print(f"\n  Testing target: {target_name}")
            
            # Python executions
            python_times = []
            for i in range(executions):
                if i % 10 == 0:
                    print(f"    Python execution {i+1}/{executions}...", end="\r")
                
                time_taken = self.run_benchmark(base_dir, target_path, target_name, "python")
                python_times.append(time_taken)
            
            # Rust executions
            rust_times = []
            for i in range(executions):
                if i % 10 == 0:
                    print(f"    Rust execution {i+1}/{executions}...", end="\r")
                
                time_taken = self.run_benchmark(base_dir, target_path, target_name, "rust")
                rust_times.append(time_taken)
            
            print(f"    ✅ Completed {executions} executions each")
            
            # Calculate statistics for this target
            py_stats = self.calculate_statistics(python_times)
            rust_stats = self.calculate_statistics(rust_times)
            
            # Calculate speedups
            speedups = [py / rust for py, rust in zip(python_times, rust_times) if rust > 0]
            speedup_stats = self.calculate_statistics(speedups)
            
            # Store results
            self.results[(scenario_name, target_name)] = {
                'python': py_stats,
                'rust': rust_stats,
                'speedup': speedup_stats
            }
            
            # Display summary for this target
            self.display_target_results(target_name, py_stats, rust_stats, speedup_stats)
            
            # Add to overall collections
            all_python_times.extend(python_times)
            all_rust_times.extend(rust_times)
        
        # Calculate overall statistics
        overall_py_stats = self.calculate_statistics(all_python_times)
        overall_rust_stats = self.calculate_statistics(all_rust_times)
        overall_speedups = [py / rust for py, rust in zip(all_python_times, all_rust_times) if rust > 0]
        overall_speedup_stats = self.calculate_statistics(overall_speedups)
        
        # Display overall results
        print(f"\n📈 Overall Results for {scenario_name}")
        print("=" * 60)
        self.display_target_results("OVERALL", overall_py_stats, overall_rust_stats, overall_speedup_stats)
        
        return {
            'targets': len(targets),
            'executions_per_target': executions,
            'total_executions': len(targets) * executions * 2,
            'overall': {
                'python': overall_py_stats,
                'rust': overall_rust_stats,
                'speedup': overall_speedup_stats
            }
        }
    
    def calculate_statistics(self, times: List[float]) -> Dict[str, float]:
        """Calculate statistical metrics."""
        if not times:
            return self.get_empty_stats()
        
        times_sorted = sorted(times)
        
        return {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'p99': self.percentile(times_sorted, 99),
            'p95': self.percentile(times_sorted, 95),
            'p50': self.percentile(times_sorted, 50),
            'min': min(times),
            'max': max(times),
            'stddev': statistics.stdev(times) if len(times) > 1 else 0.0
        }
    
    def get_empty_stats(self) -> Dict[str, float]:
        """Return empty statistics."""
        return {
            'mean': 0.0,
            'median': 0.0,
            'p99': 0.0,
            'p95': 0.0,
            'p50': 0.0,
            'min': 0.0,
            'max': 0.0,
            'stddev': 0.0
        }
    
    def percentile(self, sorted_times: List[float], percentile: int) -> float:
        """Calculate percentile."""
        if not sorted_times:
            return 0.0
        
        index = (percentile / 100.0) * (len(sorted_times) - 1)
        lower = int(index)
        upper = min(lower + 1, len(sorted_times) - 1)
        fraction = index - lower
        
        return sorted_times[lower] + fraction * (sorted_times[upper] - sorted_times[lower])
    
    def display_target_results(self, target_name: str, py_stats: Dict[str, float], 
                              rust_stats: Dict[str, float], speedup_stats: Dict[str, float]):
        """Display results for a specific target."""
        
        print(f"\n  {target_name} Results:")
        print(f"  {'Metric':<10} {'Python':>10} {'Rust':>10} {'Speedup':>10}")
        print(f"  {'-'*45}")
        
        metrics = ['mean', 'median', 'p99', 'p95', 'p50', 'min', 'max']
        for metric in metrics:
            py_val = py_stats[metric]
            rust_val = rust_stats[metric]
            speedup = py_val / rust_val if rust_val > 0 else float('inf')
            
            print(f"  {metric:<10} {py_val:>10.6f} {rust_val:>10.6f} {speedup:>10.2f}x")
        
        # Performance rating
        mean_speedup = speedup_stats['mean']
        if mean_speedup > 10:
            rating = "🚀🚀🚀 EXCEPTIONAL"
        elif mean_speedup > 5:
            rating = "🚀🚀 EXCELLENT"
        elif mean_speedup > 2:
            rating = "🚀 VERY GOOD"
        elif mean_speedup > 1.5:
            rating = "👍 GOOD"
        else:
            rating = "⚡ MODERATE"
        
        print(f"  Rating: {rating} (Mean: {mean_speedup:.2f}x)")


def main():
    print("🌍 Deep Hierarchy Benchmark with Multiple Targets")
    print("=" * 60)
    print("Testing complex organizational structure:")
    print("company → continent → country → size → resource → employee")
    print("Evaluating inheritance and collisions at each level")
    
    # Create hierarchy
    generator = DeepHierarchyGenerator()
    benchmark = MultiTargetBenchmark()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "corporate_hierarchy"
        base_dir.mkdir(parents=True)
        
        hierarchy_info = generator.create_deep_hierarchy(base_dir)
        
        # Run multi-target benchmark
        results = benchmark.run_multi_target_benchmark(
            "Deep Corporate Hierarchy", 
            hierarchy_info,
            executions=50  # 50 executions per target
        )
    
    # Summary
    print(f"\n🎉 Deep Hierarchy Benchmark Completed!")
    print(f"   Total targets tested: {results['targets']}")
    print(f"   Executions per target: {results['executions_per_target']}")
    print(f"   Total executions: {results['total_executions']}")
    print(f"   Hierarchy depth: 6 levels")
    print(f"   Total config files: {hierarchy_info['stats']['total_files']}")
    
    # Overall performance rating
    overall_speedup = results['overall']['speedup']['mean']
    if overall_speedup > 8:
        rating = "🚀🚀🚀 EXCEPTIONAL"
    elif overall_speedup > 4:
        rating = "🚀🚀 EXCELLENT"
    elif overall_speedup > 2:
        rating = "🚀 VERY GOOD"
    else:
        rating = "👍 GOOD"
    
    print(f"   Overall Rating: {rating} ({overall_speedup:.2f}x mean speedup)")


if __name__ == "__main__":
    main()