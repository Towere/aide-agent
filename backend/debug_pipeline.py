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
print("代码转论文智能体 - 流水线调试")
print("="*60)
print()

# Step 1: Test config
print("[1/6] 测试配置加载...")
from core.config import settings
print(f"   ✓ ARK_API_KEY: {settings.ark_api_key[:15]}..." if settings.ark_api_key else "   ✗ ARK_API_KEY: 未设置")
print(f"   ✓ DOUBA_MODEL: {settings.doubao_model}")
print(f"   ✓ ARK_BASE_URL: {settings.ark_base_url}")
print()

# Step 2: Test LLM client
print("[2/6] 测试 LLM 客户端...")
from utils.llm_client import get_llm_client
try:
    client = get_llm_client()
    print("   ✓ LLM 客户端创建成功")

    print("   测试简单 LLM 调用...")
    response = client.chat_with_system_prompt(
        "你好，请用一句话介绍你自己",
        "你是一个有用的助手",
        temperature=0.7,
        max_tokens=100
    )
    print(f"   ✓ LLM 响应: {response[:80]}...")
    print()
except Exception as e:
    print(f"   ✗ LLM 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test RepoAgent
print("[3/6] 测试代码解析 Agent...")
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
    print("   ✓ RepoAgentAdapter 创建成功")

    # Use fallback analysis since we don't have a real repo
    analysis = repo_agent._fallback_analysis(test_structure)
    print(f"   ✓ 代码解析结果: {analysis}")
    print()
except Exception as e:
    print(f"   ✗ 代码解析测试失败: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Test RDAgent
print("[4/6] 测试实验分析 Agent...")
from adapters.rd_agent import RDAgentAdapter

try:
    rd_agent = RDAgentAdapter(str(backend_dir))
    print("   ✓ RDAgentAdapter 创建成功")

    exp_analysis = rd_agent._fallback_analysis()
    print(f"   ✓ 实验分析结果: {exp_analysis}")
    print()
except Exception as e:
    print(f"   ✗ 实验分析测试失败: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Test PaperGenerator (single section)
print("[5/6] 测试论文章节生成 (单个章节)...")
from agents.paper_generator import PaperGeneratorAgent

try:
    paper_agent = PaperGeneratorAgent()
    print("   ✓ PaperGeneratorAgent 创建成功")

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

    print("   生成摘要...")
    abstract = paper_agent._generate_abstract(test_code_analysis, test_exp_analysis)
    print(f"   ✓ 摘要生成成功: {abstract[:100]}...")
    print()

except Exception as e:
    print(f"   ✗ 论文章节生成失败: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Test full paper generation
print("[6/6] 测试完整论文生成...")
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
    print(f"   ✓ 完整论文生成成功，长度: {len(paper)} 字符")
    print(f"   预览: {paper[:200]}...")
    print()

except Exception as e:
    print(f"   ✗ 完整论文生成失败: {e}")
    import traceback
    traceback.print_exc()

print("="*60)
print("调试完成!")
print("="*60)
