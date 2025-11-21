# 测试 dash-echarts 导入
try:
    from dash_echarts import DashECharts, JsCode
    print("✅ dash-echarts 导入成功!")
    print(f"   DashECharts: {DashECharts}")
    print(f"   JsCode: {JsCode}")
    
    # 测试 JsCode
    js = JsCode("function() { return 'test'; }")
    print(f"✅ JsCode 创建成功: {type(js)}")
    print(f"   js_code 属性: {js.js_code if hasattr(js, 'js_code') else '无此属性'}")
except ImportError as e:
    print(f"❌ dash-echarts 导入失败: {e}")
