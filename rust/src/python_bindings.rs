use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use std::path::PathBuf;
use crate::{merge_hierarchical_configs, ConfigValue};

#[pyfunction]
pub fn rust_merge_hierarchical_configs(
    base_dir: String,
    target_path: String,
) -> PyResult<(PyObject, Vec<String>)> {
    let base_path = PathBuf::from(base_dir);
    let target_path = PathBuf::from(target_path);

    match merge_hierarchical_configs(&base_path, &target_path) {
        Ok((config, errors)) => {
            Python::with_gil(|py| {
                let py_config = config_to_python(&config, py)?;
                Ok((py_config, errors))
            })
        }
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
    }
}

fn config_to_python(value: &ConfigValue, py: Python) -> PyResult<PyObject> {
    match value {
        ConfigValue::String(s) => Ok(s.to_object(py)),
        ConfigValue::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.to_object(py))
            } else if let Some(f) = n.as_f64() {
                Ok(f.to_object(py))
            } else {
                Ok(0.to_object(py))
            }
        }
        ConfigValue::Bool(b) => Ok(b.to_object(py)),
        ConfigValue::Null => Ok(py.None()),
        ConfigValue::Mapping(m) => {
            let dict = pyo3::types::PyDict::new(py);
            for (k, v) in m {
                if let ConfigValue::String(key_str) = k {
                    let py_value = config_to_python(v, py)?;
                    dict.set_item(key_str, py_value)?;
                }
            }
            Ok(dict.to_object(py))
        }
        ConfigValue::Sequence(s) => {
            let list = pyo3::types::PyList::empty(py);
            for item in s {
                let py_item = config_to_python(item, py)?;
                list.append(py_item)?;
            }
            Ok(list.to_object(py))
        }
        ConfigValue::Tagged(t) => {
            // Handle tagged values by converting the inner value
            config_to_python(&t.value, py)
        }
    }
}

#[pymodule]
pub fn hierarchical_config_merging(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rust_merge_hierarchical_configs, m)?)?;
    Ok(())
}