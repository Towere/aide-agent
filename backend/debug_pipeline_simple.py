import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

print("="*60)
print("Code to Paper Agent - Pipeline Debug")
print("="*60)
print()

# Step 1: Test config
print("[1/6] Testing config loading...")
from core.config import settings
print(f"   OK ARK_API_KEY: {settings.ark_api_key[:15]}..." if settings.ark_api_key else "   ERROR ARK_API_KEY: not set")
print(f"   OK DOUBA_MODEL: {settings.doubao_model}")
print(f"   OK ARK_BASE_URL: {settings.ark_base_url}")
print()

# Step 2: Test LLM client
print("[2/6] Testing LLM client...")
from utils.llm_client import get_llm_client
try:
    client = get_llm_client()
    print("   OK LLM client created")

    print("   Testing simple LLM call...")
    response = client.chat_with_system_prompt(
        "Hello, please introduce yourself in one sentence",
        "You are a helpful assistant",
        temperature=0.7,
        max_tokens=100
    )
    print(f"   OK LLM response: {response[:80]}...")
    print()
except Exception as e:
    print(f"   ERROR LLM test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test RepoAgent
print("[3/6] Testing code parser Agent...")
from adapters.repo_agent import RepoAgentAdapter

# Create a simple test repo structure
test_structure = {
    "files": ["README.md", "main.py", "utils.py"],
    "directories": ["src"],
    "readme": "# Test Project\nThis is a test project",
    "requirements": "requests\nfastapi"
}

try:
    repo_agent = RepoAgentAdapter(str(backend_dir))
    print("   OK RepoAgentAdapter created")

    # Use fallback analysis since we don't have a real repo
    analysis = repo_agent._fallback_analysis(test_structure)
    print(f"   OK Code analysis done")
    print()
except Exception as e:
    print(f"   ERROR Code parser test failed: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Test RDAgent
print("[4/6] Testing experiment analyzer Agent...")
from adapters.rd_agent import RDAgentAdapter

try:
    rd_agent = RDAgentAdapter(str(backend_dir))
    print("   OK RDAgentAdapter created")

    exp_analysis = rd_agent._fallback_analysis()
    print(f"   OK Experiment analysis done")
    print()
except Exception as e:
    print(f"   ERROR Experiment analyzer test failed: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Test PaperGenerator (single section)
print("[5/6] Testing paper section generation (single section)...")
from agents.paper_generator import PaperGeneratorAgent

try:
    paper_agent = PaperGeneratorAgent()
    print("   OK PaperGeneratorAgent created")

    # Test with simple data
    test_code_analysis = {
        "project_overview": {
            "name": "Test Project",
            "description": "A test project",
            "tech_stack": ["Python", "FastAPI"]
        }
    }
    test_exp_analysis = {
        "experiment_setup": {"framework": "PyTorch"},
        "metrics": [],
        "results": {"main_result": "Test result"},
        "conclusion": "Test conclusion"
    }

    print("   Generating abstract...")
    abstract = paper_agent._generate_abstract(test_code_analysis, test_exp_analysis)
    print(f"   OK Abstract generated: {abstract[:100]}...")
    print()

except Exception as e:
    print(f"   ERROR Paper section generation failed: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Test full paper generation
print("[6/6] Testing full paper generation...")
try:
    test_code_analysis = {
        "project_overview": {
            "name": "Weather Agent",
            "description": "A weather forecasting agent",
            "tech_stack": ["Python", "FastAPI"]
        },
        "structure": {"main_modules": [], "key_files": []},
        "algorithms": [],
        "dependencies": [],
        "experiments": {"has_experiments": False, "experiment_files": [], "metrics": []}
    }
    test_exp_analysis = {
        "experiment_setup": {"framework": "Unknown", "hardware": "Unknown", "dataset": "Unknown"},
        "metrics": [],
        "results": {"main_result": "待补充", "baseline_comparison": "待补充"},
        "conclusion": "待补充"
    }

    paper = paper_agent._generate_full_paper(test_code_analysis, test_exp_analysis)
    print(f"   OK Full paper generated, length: {len(paper)} chars")
    print(f"   Preview: {paper[:200]}...")
    print()

except Exception as e:
    print(f"   ERROR Full paper generation failed: {e}")
    import traceback
    traceback.print_exc()

print("="*60)
print("Debug complete!")
print("="*60)
