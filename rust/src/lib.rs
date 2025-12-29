use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::fs;
use anyhow::{Context, Result};
use serde_yaml;

pub mod python_bindings;

/// Type alias for ConfigValue - we use serde_yaml::Value directly
pub type ConfigValue = serde_yaml::Value;

pub fn find_yaml_files_in_hierarchy(base_dir: &Path, target_path: &Path) -> Result<Vec<PathBuf>> {
    let base_dir = base_dir.canonicalize()?;
    let target_path = target_path.canonicalize()?;

    // Ensure target_path is within base_dir
    if !target_path.starts_with(&base_dir) {
        return Err(anyhow::anyhow!(
            "Target path {} is not within base directory {}",
            target_path.display(),
            base_dir.display()
        ));
    }

    let mut yaml_files = Vec::new();

    // Get relative path from base to target
    let target_relative = target_path.strip_prefix(&base_dir)?;
    let target_parts: Vec<&str> = target_relative
        .components()
        .filter_map(|c| c.as_os_str().to_str())
        .collect();

    // Walk through the directory tree
    for entry in walkdir::WalkDir::new(&base_dir)
        .follow_links(true)
    {
        let entry = entry?;
        let path = entry.path();

        if !path.is_file() {
            continue;
        }

        // Check if it's a YAML file
        if let Some(ext) = path.extension() {
            if ext == "yaml" || ext == "yml" {
                let root_relative = path.strip_prefix(&base_dir)?;
                let root_parts: Vec<&str> = root_relative
                    .components()
                    .filter_map(|c| c.as_os_str().to_str())
                    .collect();

                // Remove the filename from parts
                let root_dir_parts = if root_parts.len() > 0 {
                    &root_parts[..root_parts.len() - 1]
                } else {
                    &[]
                };

                // Check if this directory is included in target hierarchy
                if root_dir_parts.is_empty() || 
                   (root_dir_parts.len() <= target_parts.len() && 
                    root_dir_parts == &target_parts[..root_dir_parts.len()])
                {
                    yaml_files.push(path.to_path_buf());
                }
            }
        }
    }

    Ok(yaml_files)
}

pub fn parse_yaml_configs(yaml_files: &[PathBuf]) -> Result<HashMap<String, ConfigValue>> {
    let mut configs = HashMap::new();

    for yaml_file in yaml_files {
        let content = fs::read_to_string(yaml_file)
            .with_context(|| format!("Failed to read file: {}", yaml_file.display()))?;

        let config_value: ConfigValue = serde_yaml::from_str(&content)
            .with_context(|| format!("Failed to parse YAML: {}", yaml_file.display()))?;

        configs.insert(yaml_file.to_string_lossy().to_string(), config_value);
    }

    Ok(configs)
}

pub fn deep_merge(base: &ConfigValue, r#override: &ConfigValue) -> ConfigValue {
    match (base, r#override) {
        (ConfigValue::Mapping(base_map), ConfigValue::Mapping(override_map)) => {
            let mut result = base_map.clone();
            for (key, value) in override_map {
                if let Some(base_value) = result.get(key) {
                    // Recursively merge if both are mappings
                    result.insert(key.clone(), deep_merge(base_value, value));
                } else {
                    // Insert new value
                    result.insert(key.clone(), value.clone());
                }
            }
            ConfigValue::Mapping(result)
        }
        _ => r#override.clone(), // Override with new value
    }
}

pub fn merge_configs_by_depth(
    configs: &HashMap<String, ConfigValue>
) -> Result<(ConfigValue, Vec<String>)> {
    if configs.is_empty() {
        return Ok((ConfigValue::Mapping(serde_yaml::Mapping::new()), Vec::new()));
    }

    // Group configs by depth (directory level)
    let mut depth_groups: HashMap<usize, Vec<(&String, &ConfigValue)>> = HashMap::new();

    for (file_path, config) in configs {
        let path = Path::new(file_path);
        let depth = path.components().count();
        depth_groups.entry(depth).or_default().push((file_path, config));
    }

    let mut merged_config = ConfigValue::Mapping(serde_yaml::Mapping::new());
    let mut errors = Vec::new();

    // Process configs from shallowest to deepest
    let mut depths: Vec<_> = depth_groups.keys().collect();
    depths.sort();

    for depth in depths {
        let depth_configs = depth_groups.get(depth).unwrap();

        // Check for key collisions at the same depth
        let mut all_keys_at_depth = std::collections::HashSet::new();
        let mut key_sources = HashMap::new();

        for (file_path, config) in depth_configs {
            if let ConfigValue::Mapping(map) = config {
                for (key, _) in map {
                    if let ConfigValue::String(key_str) = key {
                        if all_keys_at_depth.contains(key_str) {
                            // Collision at same depth
                            let existing_source = key_sources.get(key_str).unwrap();
                            errors.push(format!(
                                "Key collision at depth {}: '{}' found in both {} and {}",
                                depth, key_str, existing_source, file_path
                            ));
                        } else {
                            all_keys_at_depth.insert(key_str.clone());
                            key_sources.insert(key_str.clone(), (*file_path).clone());
                        }
                    }
                }
            }
        }

        // Merge configs at this depth
        for (_, config) in depth_configs {
            merged_config = deep_merge(&merged_config, config);
        }
    }

    Ok((merged_config, errors))
}

pub fn merge_hierarchical_configs(
    base_dir: &Path,
    target_path: &Path,
) -> Result<(ConfigValue, Vec<String>)> {
    // Find YAML files in hierarchy
    let yaml_files = find_yaml_files_in_hierarchy(base_dir, target_path)?;

    if yaml_files.is_empty() {
        return Ok((
            ConfigValue::Mapping(serde_yaml::Mapping::new()),
            vec![format!(
                "No YAML files found in hierarchy from {} to {}",
                base_dir.display(),
                target_path.display()
            )],
        ));
    }

    // Parse YAML configs
    let configs = parse_yaml_configs(&yaml_files)?;

    // Merge configs by depth
    let (merged_config, errors) = merge_configs_by_depth(&configs)?;

    Ok((merged_config, errors))
}

#[cfg(test)]
mod tests {
    use super::*;


    #[test]
    fn test_deep_merge_basic() {
        let mut base = serde_yaml::Mapping::new();
        base.insert(serde_yaml::Value::String("a".to_string()), serde_yaml::Value::Number(serde_yaml::Number::from(1)));
        base.insert(serde_yaml::Value::String("b".to_string()), serde_yaml::Value::Number(serde_yaml::Number::from(2)));
        
        let mut nested_base = serde_yaml::Mapping::new();
        nested_base.insert(serde_yaml::Value::String("nested".to_string()), serde_yaml::Value::String("base".to_string()));
        base.insert(serde_yaml::Value::String("c".to_string()), serde_yaml::Value::Mapping(nested_base));

        let mut r#override = serde_yaml::Mapping::new();
        r#override.insert(serde_yaml::Value::String("b".to_string()), serde_yaml::Value::Number(serde_yaml::Number::from(3)));
        r#override.insert(serde_yaml::Value::String("d".to_string()), serde_yaml::Value::Number(serde_yaml::Number::from(4)));
        
        let mut nested_override = serde_yaml::Mapping::new();
        nested_override.insert(serde_yaml::Value::String("nested".to_string()), serde_yaml::Value::String("override".to_string()));
        nested_override.insert(serde_yaml::Value::String("new".to_string()), serde_yaml::Value::String("value".to_string()));
        r#override.insert(serde_yaml::Value::String("c".to_string()), serde_yaml::Value::Mapping(nested_override));

        let result = deep_merge(&ConfigValue::Mapping(base), &ConfigValue::Mapping(r#override));

        if let ConfigValue::Mapping(result_map) = result {
            assert_eq!(result_map.get(&ConfigValue::String("a".to_string())), Some(&ConfigValue::Number(serde_yaml::Number::from(1))));
            assert_eq!(result_map.get(&ConfigValue::String("b".to_string())), Some(&ConfigValue::Number(serde_yaml::Number::from(3))));
            assert_eq!(result_map.get(&ConfigValue::String("d".to_string())), Some(&ConfigValue::Number(serde_yaml::Number::from(4))));

            if let Some(ConfigValue::Mapping(c_map)) = result_map.get(&ConfigValue::String("c".to_string())) {
                assert_eq!(
                    c_map.get(&ConfigValue::String("nested".to_string())),
                    Some(&ConfigValue::String("override".to_string()))
                );
                assert_eq!(
                    c_map.get(&ConfigValue::String("new".to_string())),
                    Some(&ConfigValue::String("value".to_string()))
                );
            } else {
                panic!("Expected nested map for key 'c'");
            }
        } else {
            panic!("Expected result to be a map");
        }
    }

    #[test]
    fn test_merge_configs_by_depth_basic() {
        let mut configs = HashMap::new();

        let mut base_config = serde_yaml::Mapping::new();
        base_config.insert(serde_yaml::Value::String("key1".to_string()), serde_yaml::Value::String("base_value".to_string()));
        base_config.insert(serde_yaml::Value::String("key2".to_string()), serde_yaml::Value::String("base_value2".to_string()));

        let mut level1_config = serde_yaml::Mapping::new();
        level1_config.insert(serde_yaml::Value::String("key2".to_string()), serde_yaml::Value::String("level1_value".to_string()));
        level1_config.insert(serde_yaml::Value::String("key3".to_string()), serde_yaml::Value::String("level1_value3".to_string()));

        let mut level2_config = serde_yaml::Mapping::new();
        level2_config.insert(serde_yaml::Value::String("key3".to_string()), serde_yaml::Value::String("level2_value".to_string()));
        level2_config.insert(serde_yaml::Value::String("key4".to_string()), serde_yaml::Value::String("level2_value4".to_string()));

        configs.insert("/base/config.yaml".to_string(), ConfigValue::Mapping(base_config));
        configs.insert("/base/level1/config.yaml".to_string(), ConfigValue::Mapping(level1_config));
        configs.insert("/base/level1/level2/config.yaml".to_string(), ConfigValue::Mapping(level2_config));

        let (merged_config, errors) = merge_configs_by_depth(&configs).unwrap();

        assert!(errors.is_empty());

        if let ConfigValue::Mapping(merged_map) = merged_config {
            assert_eq!(
                merged_map.get(&ConfigValue::String("key1".to_string())),
                Some(&ConfigValue::String("base_value".to_string()))
            );
            assert_eq!(
                merged_map.get(&ConfigValue::String("key2".to_string())),
                Some(&ConfigValue::String("level1_value".to_string()))
            );
            assert_eq!(
                merged_map.get(&ConfigValue::String("key3".to_string())),
                Some(&ConfigValue::String("level2_value".to_string()))
            );
            assert_eq!(
                merged_map.get(&ConfigValue::String("key4".to_string())),
                Some(&ConfigValue::String("level2_value4".to_string()))
            );
        } else {
            panic!("Expected merged config to be a map");
        }
    }
}