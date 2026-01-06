# Dash 3.x 兼容性快速参考

## ❌ 不再支持的 API

### html.Style()
```python
# ❌ Dash 2.x（已废弃）
html.Style("body { color: red; }")
html.Style(children="body { color: red; }")
```

## ✅ 推荐的替代方案

### 方案1: 组件 style 属性（最推荐）
```python
# DataTable 样式
dash_table.DataTable(
    style_cell={
        'textAlign': 'left',
        'fontSize': '12px',
        'fontFamily': 'Microsoft YaHei'
    },
    style_header={
        'backgroundColor': '#f0f5ff',
        'fontWeight': 'bold'
    },
    style_data_conditional=[
        {'if': {'column_id': '分类'}, 'color': '#52c41a'}
    ]
)

# Div 样式
html.Div(
    "内容",
    style={
        'color': 'red',
        'fontSize': '14px',
        'padding': '10px'
    }
)
```

### 方案2: assets/custom.css 文件
```css
/* assets/custom.css */
.my-table {
    border-radius: 8px;
    font-family: Microsoft YaHei, sans-serif;
}

.my-table .dash-cell {
    padding: 10px 8px;
    font-size: 12px;
}
```

```python
# Python 代码
dash_table.DataTable(
    className='my-table',
    ...
)
```

### 方案3: app.index_string 注入
```python
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        {%favicon%}
        {%css%}
        <style>
            .my-class { color: red; }
        </style>
    </head>
    <body>
        {%app_entry%}
        {%config%}
        {%scripts%}
        {%renderer%}
    </body>
</html>
'''
```

## 🎯 选择建议

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| 单个组件样式 | 方案1: style 属性 | 简单直接，类型安全 |
| 多个组件共享样式 | 方案2: CSS 文件 | 便于维护，可复用 |
| 全局样式 | 方案2 或 方案3 | 性能好，只加载一次 |
| 动态样式 | 方案1: style 属性 | 可以根据数据动态生成 |

## 📝 迁移检查清单

- [ ] 搜索代码中的 `html.Style(`
- [ ] 将样式迁移到组件属性或 CSS 文件
- [ ] 测试样式是否正确应用
- [ ] 检查浏览器控制台是否有错误
- [ ] 验证功能完全正常

## 🔍 常见错误

### 错误1: AttributeError: module 'dash.html' has no attribute 'Style'
**原因**: 使用了 Dash 2.x 的 `html.Style()`  
**解决**: 使用上述三种方案之一替代

### 错误2: 样式不生效
**原因**: CSS 选择器不正确或优先级问题  
**解决**: 使用浏览器开发者工具检查元素，确认 CSS 类名和选择器

### 错误3: 动态样式无法更新
**原因**: 使用了静态 CSS 文件  
**解决**: 改用方案1（组件 style 属性）或 style_data_conditional

## 📚 参考资源

- [Dash 3.0 Migration Guide](https://dash.plotly.com/migration)
- [Dash DataTable Styling](https://dash.plotly.com/datatable/style)
- [Dash HTML Components](https://dash.plotly.com/dash-html-components)

---
**更新日期**: 2025-12-11  
**Dash 版本**: 3.3.0+  
