"""
📦 字段检测工具 - 傻瓜式操作

功能：
1. 扫描 Excel 文件，检测新字段
2. 自动生成 models.py 代码片段
3. 自动生成 data_source_manager.py 映射代码
4. 一键复制到剪贴板

使用方法：
    直接运行此脚本，按提示操作即可

作者: GitHub Copilot
日期: 2025-12-04
"""

import sys
import os
import re
from pathlib import Path

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from typing import Dict, List, Tuple


# ========================================
# 配置
# ========================================
DEFAULT_EXCEL_PATH = r"门店数据\比价看板模块\订单数据-本店.xlsx"


def get_existing_fields() -> set:
    """获取 models.py 中已定义的字段（通过解析代码）"""
    models_file = PROJECT_ROOT / "database" / "models.py"
    
    if not models_file.exists():
        print("❌ 找不到 database/models.py")
        return set()
    
    with open(models_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 Order 类中的字段定义
    # 匹配模式: field_name = Column(...)
    pattern = r"^\s+(\w+)\s*=\s*Column\("
    fields = set(re.findall(pattern, content, re.MULTILINE))
    
    return fields


def get_existing_chinese_mappings() -> Dict[str, str]:
    """获取已有的中文字段映射"""
    manager_file = PROJECT_ROOT / "database" / "data_source_manager.py"
    
    if not manager_file.exists():
        return {}
    
    with open(manager_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 DB_FIELD_MAPPING 中的映射
    # 匹配模式: '中文名': ('english_name', ...)
    pattern = r"'([^']+)':\s*\('(\w+)',"
    matches = re.findall(pattern, content)
    
    return {chinese: english for chinese, english in matches}


def get_import_mappings() -> Dict[str, str]:
    """获取智能导入中的字段映射"""
    import_file = PROJECT_ROOT / "智能导入门店数据.py"
    
    if not import_file.exists():
        return {}
    
    with open(import_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取映射: 'db_field': row.get('中文名', ...)
    pattern = r"'(\w+)':\s*(?:str|float|int)?\(?row\.get\('([^']+)'"
    matches = re.findall(pattern, content)
    
    return {chinese: english for english, chinese in matches}


def infer_field_type(series: pd.Series, field_name: str) -> Tuple[str, str]:
    """
    推断字段类型
    
    返回: (SQLAlchemy类型, 默认值)
    """
    # 先根据字段名推断
    name_lower = field_name.lower()
    
    # 日期时间类字段
    if any(kw in name_lower for kw in ['日期', '时间', 'date', 'time']):
        return "DateTime", "None"
    
    # ID类字段
    if any(kw in name_lower for kw in ['id', '编号', '编码', '条码']):
        return "String(100)", "''"
    
    # 名称类字段
    if any(kw in name_lower for kw in ['名称', '名', '地址', 'name', 'address']):
        return "String(500)", "''"
    
    # 分类字段
    if any(kw in name_lower for kw in ['分类', '类型', '平台', '渠道', 'category', 'type', 'channel']):
        return "String(100)", "''"
    
    # 根据数据类型推断
    if series.dtype == 'object':
        # 检查是否可能是日期
        try:
            pd.to_datetime(series.dropna().head(10))
            return "DateTime", "None"
        except:
            pass
        
        # 字符串类型
        max_len = series.astype(str).str.len().max()
        if pd.isna(max_len):
            max_len = 100
        if max_len > 500:
            return "Text", "''"
        elif max_len > 200:
            return "String(500)", "''"
        else:
            return "String(100)", "''"
    
    elif series.dtype in ['int64', 'int32']:
        return "Integer", "0"
    
    elif series.dtype in ['float64', 'float32']:
        return "Float", "0.0"
    
    elif series.dtype == 'bool':
        return "Boolean", "False"
    
    else:
        return "String(100)", "''"


def chinese_to_english(chinese_name: str) -> str:
    """将中文字段名转换为英文变量名"""
    # 常见映射
    mappings = {
        '订单': 'order',
        '编号': 'number',
        '商品': 'product',
        '名称': 'name',
        '价格': 'price',
        '成本': 'cost',
        '销量': 'quantity',
        '金额': 'amount',
        '利润': 'profit',
        '门店': 'store',
        '渠道': 'channel',
        '平台': 'platform',
        '配送': 'delivery',
        '物流': 'logistics',
        '费用': 'fee',
        '费': 'fee',
        '日期': 'date',
        '时间': 'time',
        '分类': 'category',
        '一级': 'level1',
        '二级': 'level2',
        '三级': 'level3',
        '库存': 'stock',
        '用户': 'user',
        '支付': 'payment',
        '满减': 'full_reduction',
        '优惠': 'discount',
        '券': 'voucher',
        '活动': 'activity',
        '商家': 'merchant',
        '距离': 'distance',
        '地址': 'address',
        '城市': 'city',
        '减免': 'discount',
        '承担': 'share',
        '部分': 'part',
        '实收': 'actual',
        '原价': 'original',
        '实售': 'selling',
        '采购': 'purchase',
        '佣金': 'commission',
        '服务': 'service',
        '打包': 'packaging',
        '袋': 'bag',
        '新客': 'new_customer',
        '后返': 'rebate',
        '企客': 'corporate',
    }
    
    result = chinese_name
    for cn, en in mappings.items():
        result = result.replace(cn, f'_{en}_')
    
    # 清理
    result = re.sub(r'[^\w]', '_', result)
    result = re.sub(r'_+', '_', result)
    result = result.strip('_').lower()
    
    # 如果全是中文没有转换成功，使用拼音首字母
    if not result or result == chinese_name:
        result = f"field_{abs(hash(chinese_name)) % 10000}"
    
    return result


def scan_excel(excel_path: str = None) -> Dict[str, pd.Series]:
    """扫描Excel文件，返回所有字段"""
    if excel_path is None:
        excel_path = DEFAULT_EXCEL_PATH
    
    full_path = PROJECT_ROOT / excel_path
    
    if not full_path.exists():
        print(f"❌ 找不到文件: {full_path}")
        return {}
    
    print(f"📂 读取文件: {full_path}")
    
    try:
        df = pd.read_excel(full_path)
        print(f"✅ 读取成功，共 {len(df)} 行, {len(df.columns)} 列")
        return {col: df[col] for col in df.columns}
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return {}


def detect_new_fields(excel_fields: Dict[str, pd.Series]) -> List[dict]:
    """检测新字段"""
    existing_db_fields = get_existing_fields()
    existing_mappings = get_existing_chinese_mappings()
    import_mappings = get_import_mappings()
    
    # 合并所有已知的中文字段名
    known_chinese = set(existing_mappings.keys()) | set(import_mappings.keys())
    
    new_fields = []
    
    for chinese_name, series in excel_fields.items():
        # 检查是否已存在
        if chinese_name in known_chinese:
            continue
        
        # 推断英文名和类型
        english_name = chinese_to_english(chinese_name)
        field_type, default_value = infer_field_type(series, chinese_name)
        
        # 检查英文名是否已存在
        if english_name in existing_db_fields:
            english_name = f"{english_name}_new"
        
        new_fields.append({
            'chinese': chinese_name,
            'english': english_name,
            'type': field_type,
            'default': default_value,
            'sample': str(series.dropna().head(3).tolist())[:50]
        })
    
    return new_fields


def generate_models_code(new_fields: List[dict]) -> str:
    """生成 models.py 代码片段"""
    lines = []
    lines.append("    # ========== 新增字段（复制到 Order 类中） ==========")
    
    for field in new_fields:
        comment = field['chinese']
        if 'DateTime' in field['type']:
            line = f"    {field['english']} = Column({field['type']}, comment='{comment}')"
        elif 'String' in field['type'] or 'Text' in field['type']:
            line = f"    {field['english']} = Column({field['type']}, comment='{comment}')"
        else:
            default = f", default={field['default']}" if field['default'] != 'None' else ""
            line = f"    {field['english']} = Column({field['type']}{default}, comment='{comment}')"
        
        lines.append(line)
    
    return '\n'.join(lines)


def generate_mapping_code(new_fields: List[dict]) -> str:
    """生成 data_source_manager.py 映射代码片段"""
    lines = []
    lines.append("    # ========== 新增字段映射（复制到 DB_FIELD_MAPPING 中） ==========")
    
    for field in new_fields:
        need_hasattr = "True"  # 新字段都需要 hasattr 检查
        line = f"    '{field['chinese']}': ('{field['english']}', {field['default']}, {need_hasattr}),"
        lines.append(line)
    
    return '\n'.join(lines)


def generate_import_code(new_fields: List[dict]) -> str:
    """生成 智能导入门店数据.py 映射代码片段"""
    lines = []
    lines.append("            # ========== 新增字段映射（复制到导入映射中） ==========")
    
    for field in new_fields:
        if 'String' in field['type'] or 'Text' in field['type']:
            line = f"            '{field['english']}': str(row.get('{field['chinese']}', '')),"
        elif 'Float' in field['type']:
            line = f"            '{field['english']}': float(row.get('{field['chinese']}', 0) or 0),"
        elif 'Integer' in field['type']:
            line = f"            '{field['english']}': int(row.get('{field['chinese']}', 0) or 0),"
        else:
            line = f"            '{field['english']}': row.get('{field['chinese']}', None),"
        
        lines.append(line)
    
    return '\n'.join(lines)


def copy_to_clipboard(text: str):
    """复制到剪贴板"""
    try:
        import subprocess
        process = subprocess.Popen(['clip'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        return True
    except:
        return False


def main():
    """主函数 - 傻瓜式操作流程"""
    print("\n" + "="*70)
    print("📦 字段检测工具 - 傻瓜式操作")
    print("="*70)
    
    # 步骤1: 选择Excel文件
    print("\n📌 步骤1: 选择Excel文件")
    print("-"*50)
    print(f"默认文件: {DEFAULT_EXCEL_PATH}")
    
    user_input = input("\n按回车使用默认文件，或输入其他路径: ").strip()
    excel_path = user_input if user_input else DEFAULT_EXCEL_PATH
    
    # 步骤2: 扫描Excel
    print("\n📌 步骤2: 扫描Excel文件")
    print("-"*50)
    
    excel_fields = scan_excel(excel_path)
    if not excel_fields:
        print("❌ 无法读取Excel文件，请检查路径")
        return
    
    # 步骤3: 检测新字段
    print("\n📌 步骤3: 检测新字段")
    print("-"*50)
    
    new_fields = detect_new_fields(excel_fields)
    
    if not new_fields:
        print("✅ 没有检测到新字段，所有字段都已存在！")
        return
    
    print(f"🔍 检测到 {len(new_fields)} 个新字段:\n")
    
    for i, field in enumerate(new_fields, 1):
        print(f"  {i}. {field['chinese']}")
        print(f"     → 英文名: {field['english']}")
        print(f"     → 类型: {field['type']}")
        print(f"     → 示例: {field['sample']}")
        print()
    
    # 步骤4: 确认字段
    print("\n📌 步骤4: 确认要添加的字段")
    print("-"*50)
    
    print("请输入要添加的字段序号（多个用逗号分隔，输入 all 添加全部，输入 q 退出）")
    user_input = input(">>> ").strip().lower()
    
    if user_input == 'q':
        print("👋 已取消")
        return
    
    if user_input == 'all':
        selected_fields = new_fields
    else:
        try:
            indices = [int(x.strip()) - 1 for x in user_input.split(',')]
            selected_fields = [new_fields[i] for i in indices if 0 <= i < len(new_fields)]
        except:
            print("❌ 输入格式错误")
            return
    
    if not selected_fields:
        print("❌ 没有选择任何字段")
        return
    
    print(f"\n✅ 已选择 {len(selected_fields)} 个字段")
    
    # 步骤5: 生成代码
    print("\n📌 步骤5: 生成代码")
    print("-"*50)
    
    models_code = generate_models_code(selected_fields)
    mapping_code = generate_mapping_code(selected_fields)
    import_code = generate_import_code(selected_fields)
    
    # 显示代码
    print("\n" + "="*70)
    print("📄 1. models.py 代码（复制到 Order 类中）:")
    print("="*70)
    print(models_code)
    
    print("\n" + "="*70)
    print("📄 2. data_source_manager.py 代码（复制到 DB_FIELD_MAPPING 中）:")
    print("="*70)
    print(mapping_code)
    
    print("\n" + "="*70)
    print("📄 3. 智能导入门店数据.py 代码（复制到导入映射中）:")
    print("="*70)
    print(import_code)
    
    # 步骤6: 复制到剪贴板
    print("\n📌 步骤6: 复制代码")
    print("-"*50)
    
    all_code = f"""
# ============ models.py ============
{models_code}

# ============ data_source_manager.py ============
{mapping_code}

# ============ 智能导入门店数据.py ============
{import_code}
"""
    
    if copy_to_clipboard(all_code):
        print("✅ 所有代码已复制到剪贴板！")
    else:
        print("⚠️ 无法复制到剪贴板，请手动复制上面的代码")
    
    # 步骤7: 后续操作提示
    print("\n" + "="*70)
    print("📌 后续操作步骤:")
    print("="*70)
    print("""
1. 打开 database/models.py
   → 找到 Order 类
   → 粘贴第1段代码

2. 打开 database/data_source_manager.py
   → 找到 DB_FIELD_MAPPING 字典
   → 粘贴第2段代码

3. 打开 智能导入门店数据.py
   → 找到字段映射部分
   → 粘贴第3段代码

4. 运行迁移脚本:
   python 数据库迁移.py

5. 重新导入数据:
   python 智能导入门店数据.py

6. 重启看板服务
""")
    
    input("\n按回车键退出...")


if __name__ == '__main__':
    main()
