//! # Capability Discovery Engine for Open-Mind
//!
//! Reads CAPABILITY.toml files from SuperInstance repositories, builds an
//! integration graph, and suggests which crates to add based on what's already
//! present in a project.
//!
//! ## Core Types
//!
//! - [`CapabilityManifest`] — parsed representation of a CAPABILITY.toml
//! - [`CapabilityScanner`] — scans directories for capability manifests
//! - [`DependencyGraph`] — directed graph of crate dependencies
//! - [`IntegrationSuggestion`] — a recommended integration action

use std::collections::{HashMap, HashSet, BTreeMap};
use std::path::{Path, PathBuf};

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

/// Errors that can occur during capability discovery.
#[derive(Debug, Clone)]
pub enum DiscoveryError {
    /// The CAPABILITY.toml file could not be read.
    IoError { path: PathBuf, message: String },
    /// The TOML was malformed or missing required fields.
    ParseError { path: PathBuf, message: String },
    /// A circular dependency was detected.
    CircularDependency { cycle: Vec<String> },
}

impl std::fmt::Display for DiscoveryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::IoError { path, message } => {
                write!(f, "IO error reading {}: {}", path.display(), message)
            }
            Self::ParseError { path, message } => {
                write!(f, "Parse error in {}: {}", path.display(), message)
            }
            Self::CircularDependency { cycle } => {
                write!(f, "Circular dependency: {}", cycle.join(" → "))
            }
        }
    }
}

impl std::error::Error for DiscoveryError {}

// ---------------------------------------------------------------------------
// Core data structures
// ---------------------------------------------------------------------------

/// A parsed CAPABILITY.toml manifest.
///
/// Example TOML:
/// ```toml
/// [capability]
/// name = "spectral-fleet"
/// version = "0.2.0"
/// description = "Eigenvalue-based agent ranking"
/// category = "analytics"
///
/// [capability.integrations]
/// fleet-warden = { kind = "optional", reason = "Feed fleet health into spectral ranking" }
/// conservation-law = { kind = "required", reason = "Energy budgets constrain eigenvalue computation" }
///
/// [capability.exports]
/// eigenvalues = "Vec<f64>"
/// rankings = "Vec<AgentRank>"
/// ```
#[derive(Debug, Clone)]
pub struct CapabilityManifest {
    /// Unique crate / capability name.
    pub name: String,
    /// Semantic version string.
    pub version: String,
    /// Human-readable description.
    pub description: String,
    /// Category tag (e.g. "analytics", "governance", "physics").
    pub category: String,
    /// Path to the directory containing this manifest.
    pub source_path: PathBuf,
    /// Integration requirements keyed by crate name.
    pub integrations: HashMap<String, IntegrationSpec>,
    /// Typed symbols this capability exports.
    pub exports: HashMap<String, String>,
}

/// Specification for a single integration requirement.
#[derive(Debug, Clone)]
pub struct IntegrationSpec {
    /// "required", "optional", or "conflicts".
    pub kind: String,
    /// Why this integration exists.
    pub reason: String,
}

/// A suggestion produced by the discovery engine.
#[derive(Debug, Clone, PartialEq)]
pub struct IntegrationSuggestion {
    /// The crate to add.
    pub crate_name: String,
    /// Why it should be added.
    pub reason: String,
    /// Priority: lower = higher priority.
    pub priority: u32,
    /// Category of the suggested crate.
    pub category: String,
    /// Which existing crates benefit from this integration.
    pub synergizes_with: Vec<String>,
}

// ---------------------------------------------------------------------------
// Dependency graph
// ---------------------------------------------------------------------------

/// Directed acyclic graph of crate dependencies.
#[derive(Debug, Clone, Default)]
pub struct DependencyGraph {
    /// Adjacency list: node → set of nodes it depends on.
    edges: BTreeMap<String, HashSet<String>>,
}

impl DependencyGraph {
    /// Create an empty graph.
    pub fn new() -> Self {
        Self::default()
    }

    /// Insert a node (no-op if it already exists).
    pub fn add_node(&mut self, name: &str) {
        self.edges.entry(name.to_string()).or_default();
    }

    /// Add a directed edge `from → depends_on`.
    pub fn add_edge(&mut self, from: &str, depends_on: &str) {
        self.add_node(from);
        self.add_node(depends_on);
        self.edges.get_mut(from).unwrap().insert(depends_on.to_string());
    }

    /// All node names.
    pub fn nodes(&self) -> Vec<&str> {
        self.edges.keys().map(|s| s.as_str()).collect()
    }

    /// Direct dependencies of `node`.
    pub fn dependencies_of(&self, node: &str) -> Vec<&str> {
        self.edges
            .get(node)
            .map(|deps| deps.iter().map(|s| s.as_str()).collect())
            .unwrap_or_default()
    }

    /// Reverse lookup: who depends on `node`.
    pub fn dependents_of(&self, node: &str) -> Vec<&str> {
        self.edges
            .iter()
            .filter_map(|(k, deps)| {
                if deps.contains(node) {
                    Some(k.as_str())
                } else {
                    None
                }
            })
            .collect()
    }

    /// Topological sort. Returns `Err` with a cycle on failure.
    pub fn topological_sort(&self) -> Result<Vec<String>, DiscoveryError> {
        let mut in_degree: HashMap<&str, usize> = self
            .edges
            .keys()
            .map(|k| (k.as_str(), 0usize))
            .collect();

        for deps in self.edges.values() {
            for dep in deps {
                // dep is depended upon; the *source* has the outgoing edge,
                // so in-degree counts how many things depend on a node.
                // For a conventional topo sort (deps before dependents),
                // in_degree[node] = number of things node depends on.
            }
        }
        // Recompute: in_degree[node] = len(node.deps)
        for (node, deps) in &self.edges {
            in_degree.insert(node.as_str(), deps.len());
        }

        let mut queue: Vec<&str> = in_degree
            .iter()
            .filter_map(|(&k, &v)| if v == 0 { Some(k) } else { None })
            .collect();
        queue.sort();

        let mut result = Vec::new();
        while let Some(node) = queue.pop() {
            result.push(node.to_string());
            // For every node that depends on `node`, decrement in_degree.
            for (other, deps) in &self.edges {
                if deps.contains(node) {
                    if let Some(deg) = in_degree.get_mut(other.as_str()) {
                        *deg -= 1;
                        if *deg == 0 {
                            queue.push(other.as_str());
                            queue.sort();
                        }
                    }
                }
            }
        }

        if result.len() != self.edges.len() {
            // Find a cycle for the error message
            let remaining: HashSet<&str> = self.edges.keys().map(|s| s.as_str()).collect::<HashSet<_>>()
                .difference(&result.iter().map(|s| s.as_str()).collect::<HashSet<_>>())
                .copied().collect();
            let cycle: Vec<String> = remaining.iter().map(|s| s.to_string()).collect();
            return Err(DiscoveryError::CircularDependency { cycle });
        }

        Ok(result)
    }

    /// Transitive closure of dependencies for `node`.
    pub fn transitive_deps(&self, node: &str) -> HashSet<String> {
        let mut visited = HashSet::new();
        let mut stack = vec![node];
        while let Some(current) = stack.pop() {
            if visited.insert(current.to_string()) {
                if let Some(deps) = self.edges.get(current) {
                    for dep in deps {
                        stack.push(dep.as_str());
                    }
                }
            }
        }
        visited.remove(node);
        visited
    }
}

// ---------------------------------------------------------------------------
// Scanner
// ---------------------------------------------------------------------------

/// Scans directories for CAPABILITY.toml files and produces integration
/// suggestions.
pub struct CapabilityScanner {
    /// Manifests discovered so far.
    manifests: Vec<CapabilityManifest>,
}

impl CapabilityScanner {
    /// Create a new scanner with an empty manifest list.
    pub fn new() -> Self {
        Self {
            manifests: Vec::new(),
        }
    }

    /// Scan a directory recursively for CAPABILITY.toml files.
    pub fn scan_directory<P: AsRef<Path>>(&mut self, path: P) -> Result<Vec<CapabilityManifest>, DiscoveryError> {
        let root = path.as_ref();
        let mut found = Vec::new();

        self.walk_dir(root, &mut found)?;

        self.manifests.extend(found.clone());
        Ok(found)
    }

    fn walk_dir(&self, dir: &Path, results: &mut Vec<CapabilityManifest>) -> Result<(), DiscoveryError> {
        let entries = std::fs::read_dir(dir).map_err(|e| DiscoveryError::IoError {
            path: dir.to_path_buf(),
            message: e.to_string(),
        })?;

        for entry in entries {
            let entry = entry.map_err(|e| DiscoveryError::IoError {
                path: dir.to_path_buf(),
                message: e.to_string(),
            })?;
            let path = entry.path();

            if path.is_dir() {
                // Skip hidden dirs and common non-source dirs
                let name = path.file_name().unwrap_or_default().to_string_lossy();
                if name.starts_with('.') || name == "target" || name == "node_modules" {
                    continue;
                }
                self.walk_dir(&path, results)?;
            } else if path.file_name().unwrap_or_default() == "CAPABILITY.toml" {
                match Self::parse_manifest(&path) {
                    Ok(manifest) => results.push(manifest),
                    Err(e) => return Err(e),
                }
            }
        }
        Ok(())
    }

    /// Parse a single CAPABILITY.toml into a CapabilityManifest.
    pub fn parse_manifest(path: &Path) -> Result<CapabilityManifest, DiscoveryError> {
        let content = std::fs::read_to_string(path).map_err(|e| DiscoveryError::IoError {
            path: path.to_path_buf(),
            message: e.to_string(),
        })?;

        let toml_value: toml::Value = content.parse::<toml::Value>().map_err(|e: toml::de::Error| DiscoveryError::ParseError {
            path: path.to_path_buf(),
            message: e.to_string(),
        })?;

        let cap_table = toml_value
            .get("capability")
            .ok_or_else(|| DiscoveryError::ParseError {
                path: path.to_path_buf(),
                message: "missing [capability] section".into(),
            })?
            .as_table()
            .ok_or_else(|| DiscoveryError::ParseError {
                path: path.to_path_buf(),
                message: "[capability] must be a table".into(),
            })?;

        let name = cap_table
            .get("name")
            .and_then(|v| v.as_str())
            .ok_or_else(|| DiscoveryError::ParseError {
                path: path.to_path_buf(),
                message: "missing capability.name".into(),
            })?
            .to_string();

        let version = cap_table
            .get("version")
            .and_then(|v| v.as_str())
            .unwrap_or("0.0.0")
            .to_string();

        let description = cap_table
            .get("description")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();

        let category = cap_table
            .get("category")
            .and_then(|v| v.as_str())
            .unwrap_or("uncategorized")
            .to_string();

        let mut integrations = HashMap::new();
        if let Some(int_table) = cap_table.get("integrations").and_then(|v| v.as_table()) {
            for (key, val) in int_table {
                let spec = if let Some(s) = val.as_str() {
                    IntegrationSpec {
                        kind: s.to_string(),
                        reason: String::new(),
                    }
                } else if let Some(t) = val.as_table() {
                    IntegrationSpec {
                        kind: t.get("kind").and_then(|v| v.as_str()).unwrap_or("optional").to_string(),
                        reason: t.get("reason").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                    }
                } else {
                    IntegrationSpec {
                        kind: "optional".to_string(),
                        reason: String::new(),
                    }
                };
                integrations.insert(key.clone(), spec);
            }
        }

        let mut exports = HashMap::new();
        if let Some(exp_table) = cap_table.get("exports").and_then(|v| v.as_table()) {
            for (key, val) in exp_table {
                exports.insert(key.clone(), val.as_str().unwrap_or("unknown").to_string());
            }
        }

        Ok(CapabilityManifest {
            name,
            version,
            description,
            category,
            source_path: path.parent().unwrap_or(path).to_path_buf(),
            integrations,
            exports,
        })
    }

    /// Return all discovered manifests.
    pub fn manifests(&self) -> &[CapabilityManifest] {
        &self.manifests
    }

    /// Find integration suggestions for a project that already has the given crates.
    pub fn find_integrations(&self, known: &[String]) -> Vec<IntegrationSuggestion> {
        let known_set: HashSet<&str> = known.iter().map(|s| s.as_str()).collect();
        let mut suggestions: Vec<IntegrationSuggestion> = Vec::new();
        let mut seen_names: HashSet<String> = HashSet::new();

        // For each known crate, find manifests that integrate with it
        for manifest in &self.manifests {
            if known_set.contains(manifest.name.as_str()) {
                // Already have this one; suggest its dependencies
                for (dep_name, spec) in &manifest.integrations {
                    if !known_set.contains(dep_name.as_str()) && seen_names.insert(dep_name.clone()) {
                        suggestions.push(IntegrationSuggestion {
                            crate_name: dep_name.clone(),
                            reason: if spec.reason.is_empty() {
                                format!("Required by {}", manifest.name)
                            } else {
                                spec.reason.clone()
                            },
                            priority: if spec.kind == "required" { 0 } else { 5 },
                            category: "dependency".to_string(),
                            synergizes_with: vec![manifest.name.clone()],
                        });
                    }
                }
            } else {
                // Unknown crate — check if it integrates with known ones
                let synergies: Vec<String> = manifest
                    .integrations
                    .keys()
                    .filter(|k| known_set.contains(k.as_str()))
                    .cloned()
                    .collect();

                if !synergies.is_empty() && seen_names.insert(manifest.name.clone()) {
                    suggestions.push(IntegrationSuggestion {
                        crate_name: manifest.name.clone(),
                        reason: format!(
                            "Synergizes with {} — {}",
                            synergies.join(", "),
                            manifest.description
                        ),
                        priority: 3,
                        category: manifest.category.clone(),
                        synergizes_with: synergies,
                    });
                }
            }
        }

        suggestions.sort_by_key(|s| s.priority);
        suggestions
    }

    /// Build a dependency graph from discovered manifests.
    pub fn build_dependency_graph(&self, manifests: &[CapabilityManifest]) -> DependencyGraph {
        let mut graph = DependencyGraph::new();

        for manifest in manifests {
            graph.add_node(&manifest.name);
            for dep_name in manifest.integrations.keys() {
                graph.add_edge(&manifest.name, dep_name);
            }
        }

        graph
    }
}

impl Default for CapabilityScanner {
    fn default() -> Self {
        Self::new()
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    /// Helper: create a temp dir with CAPABILITY.toml files.
    struct TempRepo {
        dir: tempfile::TempDir,
    }

    impl TempRepo {
        fn new() -> Self {
            Self {
                dir: tempfile::tempdir().unwrap(),
            }
        }

        fn root(&self) -> &Path {
            self.dir.path()
        }

        fn add_capability(&self, subdir: &str, toml_content: &str) -> PathBuf {
            let dir = self.root().join(subdir);
            std::fs::create_dir_all(&dir).unwrap();
            let file_path = dir.join("CAPABILITY.toml");
            let mut f = std::fs::File::create(&file_path).unwrap();
            f.write_all(toml_content.as_bytes()).unwrap();
            file_path
        }
    }

    const SPECTRAL_FLEET_TOML: &str = r#"
[capability]
name = "spectral-fleet"
version = "0.2.0"
description = "Eigenvalue-based agent ranking"
category = "analytics"

[capability.integrations]
fleet-warden = { kind = "optional", reason = "Feed fleet health into spectral ranking" }
conservation-law = { kind = "required", reason = "Energy budgets constrain eigenvalue computation" }

[capability.exports]
eigenvalues = "Vec<f64>"
rankings = "Vec<AgentRank>"
"#;

    const FLEET_WARDEN_TOML: &str = r#"
[capability]
name = "fleet-warden"
version = "0.1.0"
description = "Agent fleet health monitoring"
category = "governance"

[capability.integrations]
conservation-law = { kind = "optional", reason = "Track energy budget health" }

[capability.exports]
health_status = "FleetHealth"
agent_count = "usize"
"#;

    const CONSERVATION_TOML: &str = r#"
[capability]
name = "conservation-law"
version = "0.3.0"
description = "Energy conservation law enforcement for agents"
category = "physics"

[capability.integrations]

[capability.exports]
total_energy = "f64"
budget = "EnergyBudget"
"#;

    // ---- Basic parsing tests ----

    #[test]
    fn test_parse_minimal_manifest() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("CAPABILITY.toml");
        std::fs::write(&path, r#"
[capability]
name = "test-crate"
"#).unwrap();
        let m = CapabilityScanner::parse_manifest(&path).unwrap();
        assert_eq!(m.name, "test-crate");
        assert_eq!(m.version, "0.0.0");
        assert_eq!(m.category, "uncategorized");
    }

    #[test]
    fn test_parse_full_manifest() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("CAPABILITY.toml");
        std::fs::write(&path, SPECTRAL_FLEET_TOML).unwrap();
        let m = CapabilityScanner::parse_manifest(&path).unwrap();
        assert_eq!(m.name, "spectral-fleet");
        assert_eq!(m.version, "0.2.0");
        assert_eq!(m.description, "Eigenvalue-based agent ranking");
        assert_eq!(m.category, "analytics");
        assert_eq!(m.integrations.len(), 2);
        assert!(m.integrations.contains_key("fleet-warden"));
        assert!(m.integrations.contains_key("conservation-law"));
        assert_eq!(m.exports.len(), 2);
        assert_eq!(m.exports["eigenvalues"], "Vec<f64>");
    }

    #[test]
    fn test_parse_missing_capability_section() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("CAPABILITY.toml");
        std::fs::write(&path, "[other]\nkey = 'val'").unwrap();
        let result = CapabilityScanner::parse_manifest(&path);
        assert!(matches!(result, Err(DiscoveryError::ParseError { .. })));
    }

    #[test]
    fn test_parse_missing_name() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("CAPABILITY.toml");
        std::fs::write(&path, "[capability]\nversion = \"1.0\"").unwrap();
        let result = CapabilityScanner::parse_manifest(&path);
        assert!(matches!(result, Err(DiscoveryError::ParseError { .. })));
    }

    #[test]
    fn test_parse_invalid_toml() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("CAPABILITY.toml");
        std::fs::write(&path, "this is not {{{{ valid toml").unwrap();
        let result = CapabilityScanner::parse_manifest(&path);
        assert!(matches!(result, Err(DiscoveryError::ParseError { .. })));
    }

    #[test]
    fn test_parse_nonexistent_file() {
        let result = CapabilityScanner::parse_manifest(Path::new("/no/such/file.toml"));
        assert!(matches!(result, Err(DiscoveryError::IoError { .. })));
    }

    #[test]
    fn test_parse_string_integration_shorthand() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("CAPABILITY.toml");
        std::fs::write(&path, r#"
[capability]
name = "shorthand-test"
[capability.integrations]
some-dep = "optional"
"#).unwrap();
        let m = CapabilityScanner::parse_manifest(&path).unwrap();
        assert_eq!(m.integrations["some-dep"].kind, "optional");
    }

    // ---- Scanner / directory scanning tests ----

    #[test]
    fn test_scan_empty_directory() {
        let dir = tempfile::tempdir().unwrap();
        let mut scanner = CapabilityScanner::new();
        let result = scanner.scan_directory(dir.path()).unwrap();
        assert!(result.is_empty());
    }

    #[test]
    fn test_scan_single_capability() {
        let repo = TempRepo::new();
        repo.add_capability("spectral-fleet", SPECTRAL_FLEET_TOML);
        let mut scanner = CapabilityScanner::new();
        let result = scanner.scan_directory(repo.root()).unwrap();
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].name, "spectral-fleet");
    }

    #[test]
    fn test_scan_multiple_capabilities() {
        let repo = TempRepo::new();
        repo.add_capability("spectral-fleet", SPECTRAL_FLEET_TOML);
        repo.add_capability("fleet-warden", FLEET_WARDEN_TOML);
        repo.add_capability("conservation-law", CONSERVATION_TOML);
        let mut scanner = CapabilityScanner::new();
        let result = scanner.scan_directory(repo.root()).unwrap();
        assert_eq!(result.len(), 3);
        let names: HashSet<&str> = result.iter().map(|m| m.name.as_str()).collect();
        assert!(names.contains("spectral-fleet"));
        assert!(names.contains("fleet-warden"));
        assert!(names.contains("conservation-law"));
    }

    #[test]
    fn test_scan_skips_hidden_dirs() {
        let repo = TempRepo::new();
        repo.add_capability(".hidden/repo", SPECTRAL_FLEET_TOML);
        let mut scanner = CapabilityScanner::new();
        let result = scanner.scan_directory(repo.root()).unwrap();
        assert!(result.is_empty());
    }

    #[test]
    fn test_scan_skips_target_dir() {
        let repo = TempRepo::new();
        repo.add_capability("target/debug", SPECTRAL_FLEET_TOML);
        let mut scanner = CapabilityScanner::new();
        let result = scanner.scan_directory(repo.root()).unwrap();
        assert!(result.is_empty());
    }

    #[test]
    fn test_scan_accumulates_manifests() {
        let repo = TempRepo::new();
        repo.add_capability("a", SPECTRAL_FLEET_TOML);
        let mut scanner = CapabilityScanner::new();
        scanner.scan_directory(repo.root()).unwrap();
        assert_eq!(scanner.manifests().len(), 1);
        // Scan again from different dir
        let repo2 = TempRepo::new();
        repo2.add_capability("b", FLEET_WARDEN_TOML);
        scanner.scan_directory(repo2.root()).unwrap();
        assert_eq!(scanner.manifests().len(), 2);
    }

    // ---- Integration suggestion tests ----

    #[test]
    fn test_find_integrations_no_known_crates() {
        let repo = TempRepo::new();
        repo.add_capability("spectral-fleet", SPECTRAL_FLEET_TOML);
        repo.add_capability("fleet-warden", FLEET_WARDEN_TOML);
        let mut scanner = CapabilityScanner::new();
        scanner.scan_directory(repo.root()).unwrap();
        let suggestions = scanner.find_integrations(&[]);
        assert!(suggestions.is_empty());
    }

    #[test]
    fn test_find_integrations_discovers_dependencies() {
        let repo = TempRepo::new();
        repo.add_capability("spectral-fleet", SPECTRAL_FLEET_TOML);
        repo.add_capability("fleet-warden", FLEET_WARDEN_TOML);
        repo.add_capability("conservation-law", CONSERVATION_TOML);
        let mut scanner = CapabilityScanner::new();
        scanner.scan_directory(repo.root()).unwrap();

        let known = vec!["spectral-fleet".to_string()];
        let suggestions = scanner.find_integrations(&known);

        // Should suggest fleet-warden (optional dep of spectral-fleet) and conservation-law (required dep)
        let suggested_names: Vec<&str> = suggestions.iter().map(|s| s.crate_name.as_str()).collect();
        assert!(suggested_names.contains(&"conservation-law"));
        assert!(suggested_names.contains(&"fleet-warden"));
    }

    #[test]
    fn test_find_integrations_required_has_higher_priority() {
        let repo = TempRepo::new();
        repo.add_capability("spectral-fleet", SPECTRAL_FLEET_TOML);
        repo.add_capability("conservation-law", CONSERVATION_TOML);
        let mut scanner = CapabilityScanner::new();
        scanner.scan_directory(repo.root()).unwrap();

        let known = vec!["spectral-fleet".to_string()];
        let suggestions = scanner.find_integrations(&known);

        let conservation = suggestions.iter().find(|s| s.crate_name == "conservation-law").unwrap();
        assert_eq!(conservation.priority, 0); // required → priority 0
    }

    #[test]
    fn test_find_integrations_synergy_discovery() {
        let repo = TempRepo::new();
        repo.add_capability("spectral-fleet", SPECTRAL_FLEET_TOML);
        repo.add_capability("fleet-warden", FLEET_WARDEN_TOML);
        let mut scanner = CapabilityScanner::new();
        scanner.scan_directory(repo.root()).unwrap();

        // fleet-warden integrates with nothing we have → but spectral-fleet references it
        let known = vec!["conservation-law".to_string()];
        let suggestions = scanner.find_integrations(&known);

        // fleet-warden has optional dep on conservation-law → synergy
        let warden = suggestions.iter().find(|s| s.crate_name == "fleet-warden");
        // spectral-fleet requires conservation-law → synergy
        let spectral = suggestions.iter().find(|s| s.crate_name == "spectral-fleet");
        assert!(warden.is_some() || spectral.is_some());
    }

    // ---- Dependency graph tests ----

    #[test]
    fn test_build_dependency_graph() {
        let repo = TempRepo::new();
        repo.add_capability("spectral-fleet", SPECTRAL_FLEET_TOML);
        repo.add_capability("fleet-warden", FLEET_WARDEN_TOML);
        repo.add_capability("conservation-law", CONSERVATION_TOML);
        let mut scanner = CapabilityScanner::new();
        scanner.scan_directory(repo.root()).unwrap();

        let graph = scanner.build_dependency_graph(&scanner.manifests().to_vec());
        let deps = graph.dependencies_of("spectral-fleet");
        assert!(deps.contains(&"fleet-warden"));
        assert!(deps.contains(&"conservation-law"));
        assert!(graph.dependencies_of("conservation-law").is_empty());
    }

    #[test]
    fn test_dependency_graph_topological_sort() {
        let mut graph = DependencyGraph::new();
        graph.add_edge("spectral-fleet", "conservation-law");
        graph.add_edge("fleet-warden", "conservation-law");
        let sorted = graph.topological_sort().unwrap();
        let cl_pos = sorted.iter().position(|s| s == "conservation-law").unwrap();
        let sf_pos = sorted.iter().position(|s| s == "spectral-fleet").unwrap();
        assert!(cl_pos < sf_pos);
    }

    #[test]
    fn test_dependency_graph_circular_detection() {
        let mut graph = DependencyGraph::new();
        graph.add_edge("a", "b");
        graph.add_edge("b", "c");
        graph.add_edge("c", "a");
        let result = graph.topological_sort();
        assert!(matches!(result, Err(DiscoveryError::CircularDependency { .. })));
    }

    #[test]
    fn test_dependency_graph_transitive_deps() {
        let mut graph = DependencyGraph::new();
        graph.add_edge("a", "b");
        graph.add_edge("b", "c");
        let deps = graph.transitive_deps("a");
        assert!(deps.contains("b"));
        assert!(deps.contains("c"));
        assert!(!deps.contains("a"));
    }

    #[test]
    fn test_dependency_graph_dependents_of() {
        let mut graph = DependencyGraph::new();
        graph.add_edge("spectral-fleet", "conservation-law");
        graph.add_edge("fleet-warden", "conservation-law");
        let deps = graph.dependents_of("conservation-law");
        assert!(deps.contains(&"spectral-fleet"));
        assert!(deps.contains(&"fleet-warden"));
    }

    // ---- Error display tests ----

    #[test]
    fn test_error_display_io() {
        let err = DiscoveryError::IoError {
            path: PathBuf::from("/foo/CAPABILITY.toml"),
            message: "permission denied".into(),
        };
        assert!(err.to_string().contains("/foo/CAPABILITY.toml"));
        assert!(err.to_string().contains("permission denied"));
    }

    #[test]
    fn test_error_display_parse() {
        let err = DiscoveryError::ParseError {
            path: PathBuf::from("/bar/CAPABILITY.toml"),
            message: "missing name".into(),
        };
        assert!(err.to_string().contains("Parse error"));
    }

    #[test]
    fn test_error_display_circular() {
        let err = DiscoveryError::CircularDependency {
            cycle: vec!["a".into(), "b".into(), "a".into()],
        };
        assert!(err.to_string().contains("a → b → a"));
    }

    // ---- Edge case tests ----

    #[test]
    fn test_empty_dependency_graph_topo_sort() {
        let graph = DependencyGraph::new();
        let sorted = graph.topological_sort().unwrap();
        assert!(sorted.is_empty());
    }

    #[test]
    fn test_single_node_topo_sort() {
        let mut graph = DependencyGraph::new();
        graph.add_node("solo");
        let sorted = graph.topological_sort().unwrap();
        assert_eq!(sorted, vec!["solo".to_string()]);
    }

    #[test]
    fn test_manifest_source_path() {
        let repo = TempRepo::new();
        let path = repo.add_capability("my-crate", SPECTRAL_FLEET_TOML);
        let m = CapabilityScanner::parse_manifest(&path).unwrap();
        assert_eq!(m.source_path, repo.root().join("my-crate"));
    }
}
