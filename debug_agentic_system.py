#!/usr/bin/env python3
"""
🔧 Agentic System Debug and Setup Script
=======================================

Systematically debug and fix issues in the LangGraph multi-agent workflow:
1. Schema validation errors
2. Tool integration problems  
3. Agent initialization issues
4. Missing dependencies

This script identifies problems and provides fixes.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgenticSystemDebugger:
    """Debug and fix agentic system issues"""
    
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    def log_issue(self, category: str, issue: str, severity: str = "ERROR"):
        """Log an issue found"""
        self.issues_found.append({
            "category": category,
            "issue": issue,
            "severity": severity,
            "timestamp": datetime.now()
        })
        print(f"🔍 {severity}: [{category}] {issue}")
        
    def log_fix(self, fix: str):
        """Log a fix applied"""
        self.fixes_applied.append({
            "fix": fix,
            "timestamp": datetime.now()
        })
        print(f"🔧 FIX APPLIED: {fix}")

    async def debug_schema_imports(self):
        """Debug schema import issues"""
        print("\n📋 DEBUGGING SCHEMA IMPORTS")
        print("=" * 50)
        
        try:
            # Test basic schema imports
            print("Testing schema imports...")
            
            # Try to import schemas directly
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            
            try:
                from schemas.casino_review import (
                    CasinoResearchPack, CasinoReviewDoc, ScreenshotResult,
                    QAReport, PublishResult
                )
                print("✅ Core schema imports successful")
            except Exception as e:
                self.log_issue("SCHEMA", f"Core schema import failed: {e}")
                
            # Test schema field requirements
            try:
                # Check CasinoResearchPack required fields
                from schemas.casino_review import CasinoResearchPack
                import inspect
                
                # Get the model fields
                if hasattr(CasinoResearchPack, '__fields__'):
                    fields = CasinoResearchPack.__fields__
                elif hasattr(CasinoResearchPack, 'model_fields'):
                    fields = CasinoResearchPack.model_fields
                else:
                    fields = {}
                    
                print(f"✅ CasinoResearchPack fields: {len(fields)}")
                
                # Check for the missing license_type field mentioned in error
                if 'license_type' in fields:
                    print("✅ license_type field found in CasinoResearchPack")
                else:
                    self.log_issue("SCHEMA", "license_type field missing from CasinoResearchPack")
                    
            except Exception as e:
                self.log_issue("SCHEMA", f"Schema field analysis failed: {e}")
                
        except Exception as e:
            self.log_issue("SCHEMA", f"Schema debugging failed: {e}")
    
    async def debug_agent_creation(self):
        """Debug agent creation and initialization"""
        print("\n🤖 DEBUGGING AGENT CREATION")
        print("=" * 50)
        
        try:
            # Test individual agent imports
            agent_modules = [
                "agents.research_agent",
                "agents.screenshot_agent", 
                "agents.content_agent",
                "agents.qa_agent",
                "agents.publishing_agent"
            ]
            
            for module_name in agent_modules:
                try:
                    # Test import
                    module = __import__(module_name, fromlist=[''])
                    print(f"✅ {module_name} imported successfully")
                    
                    # Check for factory functions
                    expected_factories = {
                        "agents.research_agent": "create_casino_research_agent",
                        "agents.screenshot_agent": "create_casino_screenshot_agent",
                        "agents.content_agent": "create_casino_content_agent", 
                        "agents.qa_agent": "create_casino_qa_agent",
                        "agents.publishing_agent": "create_casino_publishing_agent"
                    }
                    
                    if module_name in expected_factories:
                        factory_name = expected_factories[module_name]
                        if hasattr(module, factory_name):
                            print(f"✅ {factory_name} factory function found")
                        else:
                            self.log_issue("AGENT", f"{factory_name} factory function missing from {module_name}")
                            
                except ImportError as e:
                    self.log_issue("AGENT", f"Failed to import {module_name}: {e}")
                except Exception as e:
                    self.log_issue("AGENT", f"Error testing {module_name}: {e}")
                    
        except Exception as e:
            self.log_issue("AGENT", f"Agent debugging failed: {e}")
    
    async def debug_tool_orchestrator(self):
        """Debug tool orchestrator and external service integration"""
        print("\n🛠️ DEBUGGING TOOL ORCHESTRATOR") 
        print("=" * 50)
        
        try:
            # Test tool orchestrator import
            try:
                from tools import create_tool_orchestrator, ToolOrchestrator
                print("✅ ToolOrchestrator imports successful")
                
                # Try to create orchestrator
                orchestrator = create_tool_orchestrator()
                print(f"✅ ToolOrchestrator created: {type(orchestrator)}")
                
                # Test individual tools
                tools_to_test = ['supabase', 'dataforseo', 'firecrawl', 'wordpress']
                for tool_name in tools_to_test:
                    if hasattr(orchestrator, tool_name):
                        tool = getattr(orchestrator, tool_name)
                        print(f"✅ {tool_name} tool available: {type(tool)}")
                    else:
                        self.log_issue("TOOL", f"{tool_name} tool missing from orchestrator", "WARN")
                        
            except Exception as e:
                self.log_issue("TOOL", f"ToolOrchestrator creation failed: {e}")
                
        except Exception as e:
            self.log_issue("TOOL", f"Tool orchestrator debugging failed: {e}")
    
    async def debug_environment_setup(self):
        """Debug environment variables and dependencies"""
        print("\n🌍 DEBUGGING ENVIRONMENT SETUP")
        print("=" * 50)
        
        # Check critical environment variables
        critical_env_vars = [
            'OPENAI_API_KEY',
            'SUPABASE_URL', 
            'SUPABASE_ANON_KEY',
            'FIRECRAWL_API_KEY'
        ]
        
        print("Checking environment variables:")
        for var in critical_env_vars:
            value = os.getenv(var)
            if value:
                masked = value[:10] + "..." if len(value) > 10 else value
                print(f"✅ {var}: {masked}")
            else:
                self.log_issue("ENV", f"Missing environment variable: {var}")
        
        # Check Python dependencies
        critical_deps = [
            'langgraph', 'langchain', 'langchain_core', 'langchain_openai',
            'supabase', 'aiohttp', 'pydantic'
        ]
        
        print("\nChecking Python dependencies:")
        for dep in critical_deps:
            try:
                __import__(dep)
                print(f"✅ {dep} installed")
            except ImportError:
                self.log_issue("DEPS", f"Missing Python dependency: {dep}")
    
    async def test_minimal_workflow(self):
        """Test minimal workflow execution"""
        print("\n🔬 TESTING MINIMAL WORKFLOW")
        print("=" * 50)
        
        try:
            # Import workflow with absolute imports
            PYTHONPATH = str(Path(__file__).parent)
            if PYTHONPATH not in sys.path:
                sys.path.insert(0, PYTHONPATH)
                
            # Try to create workflow instance
            from src.agents.casino_review_workflow import CasinoReviewWorkflow
            
            workflow = CasinoReviewWorkflow(tenant_id="test", max_retries=1)
            print("✅ Workflow instance created successfully")
            
            # Test graph structure
            if hasattr(workflow, 'graph'):
                print("✅ LangGraph available")
                
                # Check nodes
                try:
                    if hasattr(workflow.graph, 'nodes'):
                        nodes = list(workflow.graph.nodes.keys())
                        print(f"✅ Graph nodes ({len(nodes)}): {nodes}")
                    else:
                        print("⚠️ Graph nodes not accessible")
                except Exception as e:
                    self.log_issue("WORKFLOW", f"Graph node access failed: {e}")
            else:
                self.log_issue("WORKFLOW", "No graph attribute on workflow")
                
            # Test agent method availability
            agent_methods = ['_research_agent', '_screenshot_agent', '_content_agent', '_qa_agent', '_publishing_agent']
            for method in agent_methods:
                if hasattr(workflow, method):
                    print(f"✅ {method} method available")
                else:
                    self.log_issue("WORKFLOW", f"{method} method missing")
                    
        except Exception as e:
            self.log_issue("WORKFLOW", f"Minimal workflow test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def generate_debug_report(self):
        """Generate comprehensive debug report"""
        print(f"\n📊 DEBUG REPORT SUMMARY")
        print("=" * 80)
        
        # Count issues by category and severity
        categories = {}
        severities = {}
        
        for issue in self.issues_found:
            cat = issue['category']
            sev = issue['severity']
            categories[cat] = categories.get(cat, 0) + 1
            severities[sev] = severities.get(sev, 0) + 1
        
        print(f"Total issues found: {len(self.issues_found)}")
        print(f"Total fixes applied: {len(self.fixes_applied)}")
        
        if categories:
            print(f"\nIssues by category:")
            for cat, count in categories.items():
                print(f"  • {cat}: {count}")
                
        if severities:
            print(f"\nIssues by severity:")
            for sev, count in severities.items():
                print(f"  • {sev}: {count}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        
        if 'SCHEMA' in categories:
            print("• Fix schema validation errors - check required fields")
            
        if 'AGENT' in categories:
            print("• Fix agent factory functions and imports")
            
        if 'TOOL' in categories:
            print("• Set up tool orchestrator with proper service configs")
            
        if 'ENV' in categories:
            print("• Configure missing environment variables")
            
        if 'DEPS' in categories:
            print("• Install missing Python dependencies")
            
        if not self.issues_found:
            print("🎉 No critical issues found! System appears ready.")
        elif len([i for i in self.issues_found if i['severity'] == 'ERROR']) == 0:
            print("✅ Only minor warnings - system should work with some limitations")
        else:
            print("⚠️ Critical errors found - system needs fixes before full operation")
    
    async def run_full_debug(self):
        """Run complete debugging sequence"""
        print("🔧 STARTING COMPREHENSIVE AGENTIC SYSTEM DEBUG")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Run all debug phases
        await self.debug_environment_setup()
        await self.debug_schema_imports()
        await self.debug_agent_creation()
        await self.debug_tool_orchestrator()
        await self.test_minimal_workflow()
        
        # Generate report
        await self.generate_debug_report()
        
        duration = (datetime.now() - start_time).total_seconds()
        print(f"\n✨ Debug completed in {duration:.1f} seconds")
        
        return len([i for i in self.issues_found if i['severity'] == 'ERROR']) == 0

async def main():
    """Main debug execution"""
    debugger = AgenticSystemDebugger()
    
    try:
        success = await debugger.run_full_debug()
        
        if success:
            print(f"\n🎉 AGENTIC SYSTEM DEBUG: COMPLETED - SYSTEM READY")
            sys.exit(0)
        else:
            print(f"\n⚠️ AGENTIC SYSTEM DEBUG: COMPLETED - ISSUES NEED FIXING")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Debug execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
