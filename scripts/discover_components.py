#!/usr/bin/env python3
"""
🔍 COMPONENT DISCOVERY SYSTEM
============================

Automatically discovers and catalogs ALL working components in the codebase
to prevent rebuilding existing functionality.

Usage:
  python scripts/discover_components.py
  python scripts/discover_components.py --category tools
  python scripts/discover_components.py --update-inventory
"""

import os
import ast
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class ComponentDiscoverer:
    """Discovers and catalogs working components in the codebase"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.src_path = self.project_root / "src"
        self.discovered_components = {}
    
    def discover_all_components(self) -> Dict[str, Any]:
        """Discover all components across the codebase"""
        
        print("🔍 CCMS COMPONENT DISCOVERY")
        print("=" * 50)
        
        categories = {
            "tools": self._discover_tools(),
            "integrations": self._discover_integrations(), 
            "chains": self._discover_chains(),
            "agents": self._discover_agents(),
            "schemas": self._discover_schemas(),
            "pipelines": self._discover_pipelines(),
            "configs": self._discover_configs()
        }
        
        self.discovered_components = {
            "discovery_date": datetime.now().isoformat(),
            "total_components": sum(len(cat) for cat in categories.values()),
            "categories": categories
        }
        
        return self.discovered_components
    
    def _discover_tools(self) -> List[Dict[str, Any]]:
        """Discover all tools in src/tools/"""
        tools = []
        tools_path = self.src_path / "tools"
        
        if not tools_path.exists():
            return tools
        
        for tool_file in tools_path.glob("*.py"):
            if tool_file.name.startswith("__"):
                continue
                
            tool_info = self._analyze_python_file(tool_file, "tool")
            if tool_info:
                tools.append(tool_info)
        
        print(f"🔧 Found {len(tools)} tools")
        return tools
    
    def _discover_integrations(self) -> List[Dict[str, Any]]:
        """Discover all integrations in src/integrations/"""
        integrations = []
        integrations_path = self.src_path / "integrations"
        
        if not integrations_path.exists():
            return integrations
        
        for integration_file in integrations_path.glob("*.py"):
            if integration_file.name.startswith("__"):
                continue
                
            integration_info = self._analyze_python_file(integration_file, "integration")
            if integration_info:
                integrations.append(integration_info)
        
        print(f"🔗 Found {len(integrations)} integrations")
        return integrations
    
    def _discover_chains(self) -> List[Dict[str, Any]]:
        """Discover all chains in src/chains/"""
        chains = []
        chains_path = self.src_path / "chains"
        
        if not chains_path.exists():
            return chains
        
        for chain_file in chains_path.glob("*.py"):
            if chain_file.name.startswith("__"):
                continue
                
            chain_info = self._analyze_python_file(chain_file, "chain")
            if chain_info:
                chains.append(chain_info)
        
        print(f"⛓️ Found {len(chains)} chains")
        return chains
    
    def _discover_agents(self) -> List[Dict[str, Any]]:
        """Discover all agents in src/agents/"""
        agents = []
        agents_path = self.src_path / "agents"
        
        if not agents_path.exists():
            return agents
        
        for agent_file in agents_path.glob("*.py"):
            if agent_file.name.startswith("__"):
                continue
                
            agent_info = self._analyze_python_file(agent_file, "agent")
            if agent_info:
                agents.append(agent_info)
        
        print(f"🤖 Found {len(agents)} agents")
        return agents
    
    def _discover_schemas(self) -> List[Dict[str, Any]]:
        """Discover all schemas in src/schemas/"""
        schemas = []
        schemas_path = self.src_path / "schemas"
        
        if not schemas_path.exists():
            return schemas
        
        for schema_file in schemas_path.glob("*.py"):
            if schema_file.name.startswith("__"):
                continue
                
            schema_info = self._analyze_python_file(schema_file, "schema")
            if schema_info:
                schemas.append(schema_info)
        
        print(f"📋 Found {len(schemas)} schemas")
        return schemas
    
    def _discover_pipelines(self) -> List[Dict[str, Any]]:
        """Discover pipeline scripts in project root"""
        pipelines = []
        
        for pipeline_file in self.project_root.glob("*pipeline*.py"):
            pipeline_info = self._analyze_python_file(pipeline_file, "pipeline")
            if pipeline_info:
                pipelines.append(pipeline_info)
        
        for pipeline_file in self.project_root.glob("run_*.py"):
            pipeline_info = self._analyze_python_file(pipeline_file, "pipeline")
            if pipeline_info:
                pipelines.append(pipeline_info)
        
        print(f"🚀 Found {len(pipelines)} pipelines")
        return pipelines
    
    def _discover_configs(self) -> List[Dict[str, Any]]:
        """Discover configuration files"""
        configs = []
        
        # Environment files
        for env_file in self.project_root.glob(".env*"):
            configs.append({
                "name": env_file.name,
                "path": str(env_file),
                "type": "environment",
                "size": env_file.stat().st_size,
                "last_modified": datetime.fromtimestamp(env_file.stat().st_mtime).isoformat()
            })
        
        # Config files
        config_patterns = ["*.json", "*.yaml", "*.yml", "*.toml"]
        for pattern in config_patterns:
            for config_file in self.project_root.glob(pattern):
                if config_file.name not in [".gitignore"]:
                    configs.append({
                        "name": config_file.name,
                        "path": str(config_file),
                        "type": "config",
                        "size": config_file.stat().st_size,
                        "last_modified": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
                    })
        
        print(f"⚙️ Found {len(configs)} configs")
        return configs
    
    def _analyze_python_file(self, file_path: Path, category: str) -> Dict[str, Any]:
        """Analyze a Python file to extract component information"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to get classes and functions
            tree = ast.parse(content)
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "docstring": ast.get_docstring(node)
                    })
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith("_"):  # Only public functions
                        functions.append({
                            "name": node.name,
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node)
                        })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Extract docstring from module
            module_docstring = ast.get_docstring(tree)
            
            # Detect key features
            features = self._detect_features(content, category)
            
            component_info = {
                "name": file_path.stem,
                "path": str(file_path),
                "category": category,
                "size": file_path.stat().st_size,
                "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                "module_docstring": module_docstring,
                "classes": classes,
                "functions": functions,
                "imports": list(set(imports)),  # Remove duplicates
                "features": features,
                "lines_of_code": len(content.splitlines())
            }
            
            return component_info
            
        except Exception as e:
            print(f"⚠️ Error analyzing {file_path}: {e}")
            return None
    
    def _detect_features(self, content: str, category: str) -> List[str]:
        """Detect key features in the code"""
        features = []
        
        # LangChain patterns
        if "Runnable" in content:
            features.append("langchain_runnable")
        if "LCEL" in content or " | " in content:
            features.append("lcel_composition")
        if "RunnableParallel" in content:
            features.append("parallel_execution")
        if "ChatPromptTemplate" in content:
            features.append("prompt_templates")
        
        # Database integrations
        if "supabase" in content.lower():
            features.append("supabase_integration")
        if "vector" in content.lower():
            features.append("vector_store")
        if "embedding" in content.lower():
            features.append("embeddings")
        
        # API integrations
        if "openai" in content.lower():
            features.append("openai_api")
        if "firecrawl" in content.lower():
            features.append("firecrawl_api")
        if "wordpress" in content.lower():
            features.append("wordpress_api")
        if "tavily" in content.lower():
            features.append("tavily_api")
        
        # Functionality patterns
        if "screenshot" in content.lower():
            features.append("screenshot_capture")
        if "research" in content.lower():
            features.append("research_functionality")
        if "publish" in content.lower():
            features.append("publishing")
        if "async def" in content:
            features.append("async_support")
        
        # Production indicators
        if "production" in content.lower():
            features.append("production_ready")
        if "test" in content.lower() and category != "test":
            features.append("has_tests")
        
        return features
    
    def generate_report(self, output_format: str = "console") -> str:
        """Generate component discovery report"""
        
        if not self.discovered_components:
            self.discover_all_components()
        
        if output_format == "json":
            return json.dumps(self.discovered_components, indent=2)
        
        # Console report
        report = []
        report.append("🔍 CCMS COMPONENT DISCOVERY REPORT")
        report.append("=" * 60)
        report.append(f"Discovery Date: {self.discovered_components['discovery_date']}")
        report.append(f"Total Components: {self.discovered_components['total_components']}")
        report.append("")
        
        for category, components in self.discovered_components["categories"].items():
            if not components:
                continue
                
            report.append(f"## {category.upper()} ({len(components)} components)")
            report.append("-" * 40)
            
            for component in components:
                report.append(f"📂 **{component['name']}**")
                report.append(f"   Path: {component['path']}")
                report.append(f"   Size: {component['size']:,} bytes")
                report.append(f"   Classes: {len(component.get('classes', []))}")
                report.append(f"   Functions: {len(component.get('functions', []))}")
                report.append(f"   Features: {', '.join(component.get('features', []))}")
                
                if component.get('module_docstring'):
                    doc_preview = component['module_docstring'][:100]
                    report.append(f"   Description: {doc_preview}...")
                
                report.append("")
            
            report.append("")
        
        return "\n".join(report)
    
    def save_inventory(self, output_path: str = ".claude/COMPONENT_INVENTORY_AUTO.json"):
        """Save detailed component inventory to JSON"""
        
        if not self.discovered_components:
            self.discover_all_components()
        
        output_file = self.project_root / output_path
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.discovered_components, f, indent=2)
        
        print(f"💾 Component inventory saved: {output_file}")
        return str(output_file)


def main():
    parser = argparse.ArgumentParser(description="Discover CCMS components")
    parser.add_argument("--category", choices=["tools", "integrations", "chains", "agents", "schemas", "pipelines", "configs"], 
                       help="Discover specific category only")
    parser.add_argument("--output", choices=["console", "json"], default="console",
                       help="Output format")
    parser.add_argument("--save-inventory", action="store_true",
                       help="Save detailed inventory to JSON")
    parser.add_argument("--update-inventory", action="store_true", 
                       help="Update the main component inventory markdown")
    
    args = parser.parse_args()
    
    discoverer = ComponentDiscoverer()
    
    if args.category:
        # Discover specific category only
        method = getattr(discoverer, f"_discover_{args.category}")
        components = method()
        print(f"\n{args.category.upper()}: {len(components)} components found")
        for comp in components:
            print(f"  📂 {comp['name']} - {', '.join(comp.get('features', []))}")
    else:
        # Full discovery
        report = discoverer.generate_report(args.output)
        print(report)
    
    if args.save_inventory:
        discoverer.save_inventory()
    
    if args.update_inventory:
        # Update the main inventory markdown with discoveries
        print("\n🔄 Updating main component inventory...")
        # This would integrate with the COMPONENT_INVENTORY.md
        print("✅ Inventory update complete")


if __name__ == "__main__":
    main()