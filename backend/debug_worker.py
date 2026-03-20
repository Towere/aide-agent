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
print("Testing Worker Pipeline")
print("="*60)
print()

# Test 1: Test config loading
print("[1/5] Testing config loading...")
from core.config import settings
print(f"   ARK_API_KEY: {settings.ark_api_key[:15]}..." if settings.ark_api_key else "   ERROR: No API key")
print(f"   DOUBA_MODEL: {settings.doubao_model}")
print()

# Test 2: Test LLM client
print("[2/5] Testing LLM client...")
from utils.llm_client import get_llm_client
try:
    client = get_llm_client()
    print("   OK LLM client created")

    response = client.chat_with_system_prompt(
        "Hello, please respond with 'OK'",
        "You are a helpful assistant",
        max_tokens=50
    )
    print(f"   OK LLM response: {response}")
    print()
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test CodeParserAgent with fallback
print("[3/5] Testing CodeParserAgent (fallback)...")
from agents.code_parser import CodeParserAgent
try:
    parser = CodeParserAgent()
    print("   OK CodeParserAgent created")

    # Use simple test structure
    test_result = parser.run({
        "repo_dir": str(backend_dir)
    })
    print(f"   OK Parser result success: {test_result.get('success')}")
    print()
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test ExperimentAnalyzerAgent
print("[4/5] Testing ExperimentAnalyzerAgent...")
from agents.experiment_analyzer import ExperimentAnalyzerAgent
try:
    analyzer = ExperimentAnalyzerAgent()
    print("   OK ExperimentAnalyzerAgent created")

    test_code_analysis = {
        "project_overview": {
            "name": "Test",
            "description": "Test",
            "tech_stack": ["Python"]
        }
    }

    result = analyzer.run({
        "repo_dir": str(backend_dir),
        "code_analysis": test_code_analysis
    })
    print(f"   OK Analyzer result success: {result.get('success')}")
    print()
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test PaperGeneratorAgent
print("[5/5] Testing PaperGeneratorAgent...")
from agents.paper_generator import PaperGeneratorAgent
try:
    generator = PaperGeneratorAgent()
    print("   OK PaperGeneratorAgent created")

    test_code_analysis = {
        "project_overview": {
            "name": "Weather Agent",
            "description": "A weather agent",
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
        "results": {"main_result": "Test", "baseline_comparison": "Test"},
        "conclusion": "Test"
    }

    result = generator.run({
        "code_analysis": test_code_analysis,
        "experiment_analysis": test_exp_analysis
    })
    print(f"   OK Generator result success: {result.get('success')}")
    if result.get('success'):
        paper = result.get('paper_content', '')
        print(f"   OK Paper length: {len(paper)} chars")
        print(f"   OK Paper preview: {paper[:200]}...")
    print()
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print("="*60)
print("All tests complete!")
print("="*60)
