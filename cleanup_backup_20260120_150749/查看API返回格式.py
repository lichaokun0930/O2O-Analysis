"""
查看渠道对比API的实际返回格式
"""
import requests
import json

BASE_URL = "http://localhost:8080"
TEST_STORE = "惠宜选-泰州泰兴店"
START_DATE = "2026-01-12"
END_DATE = "2026-01-18"

print("查看API返回格式...")
print()

params = {
    "store_name": TEST_STORE,
    "start_date": START_DATE,
    "end_date": END_DATE
}

response = requests.get(
    f"{BASE_URL}/api/v1/orders/channel-comparison",
    params=params
)

if response.status_code == 200:
    data = response.json()
    print("API返回数据:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print(f"API请求失败: {response.status_code}")
    print(response.text)
