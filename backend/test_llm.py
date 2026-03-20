import sys
from pathlib import Path

backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from core.config import settings

print("=== 配置检查 ===")
print(f"ARK_API_KEY: {settings.ark_api_key[:10]}..." if settings.ark_api_key else "ARK_API_KEY: 未设置")
print(f"DOUBA_MODEL: {settings.doubao_model}")
print(f"ARK_BASE_URL: {settings.ark_base_url}")
print()

from utils.llm_client import get_llm_client

print("=== 测试 LLM 调用 ===")
try:
    client = get_llm_client()
    print("LLM 客户端创建成功")

    response = client.chat_with_system_prompt(
        "你好，请用一句话介绍你自己",
        "你是一个有用的助手",
        temperature=0.7,
        max_tokens=100
    )
    print(f"LLM 响应: {response}")
    print()
    print("✅ LLM 调用成功！")

except Exception as e:
    print(f"❌ LLM 调用失败: {e}")
    import traceback
    traceback.print_exc()
