# PowerShell 7+ 快速启动指南

## 启动方法

### 方法1: 命令行启动 (最快)
```powershell
pwsh
```

### 方法2: Windows Terminal (推荐)
1. 打开 Windows Terminal
2. 点击顶部的下拉箭头 ▼
3. 选择 "PowerShell 7"

### 方法3: 开始菜单
1. 按 Win 键
2. 搜索 "PowerShell 7" 或 "pwsh"
3. 点击打开

### 方法4: 运行对话框
1. 按 Win + R
2. 输入: pwsh
3. 回车

### 方法5: 从文件资源管理器
在任意文件夹的地址栏输入: pwsh

## 验证安装

在终端中运行以下命令验证:
```powershell
pwsh --version
```

或查看详细信息:
```powershell
pwsh
$PSVersionTable
```

## 设置为默认终端

### 在 VS Code 中设置
1. Ctrl + Shift + P
2. 搜索 "Terminal: Select Default Profile"
3. 选择 "PowerShell"

### 在 Windows Terminal 中设置
1. 打开 Windows Terminal
2. 按 Ctrl + , (打开设置)
3. 在"启动"选项卡中
4. "默认配置文件" 选择 "PowerShell"

## 区别

| 特性 | Windows PowerShell 5.1 | PowerShell 7+ |
|------|------------------------|---------------|
| 命令 | `powershell` 或 `powershell.exe` | `pwsh` 或 `pwsh.exe` |
| 版本类型 | Desktop | Core |
| 图标颜色 | 蓝色 | 黑色/白色 |
| 平台支持 | 仅 Windows | Windows/Linux/macOS |

## 常用命令对比

```powershell
# 查看版本
powershell -Command '$PSVersionTable'  # PowerShell 5.1
pwsh -Command '$PSVersionTable'        # PowerShell 7+

# 启动交互式会话
powershell                              # PowerShell 5.1
pwsh                                    # PowerShell 7+

# 执行脚本
powershell -File script.ps1            # PowerShell 5.1
pwsh -File script.ps1                  # PowerShell 7+
```

## 测试新特性

启动 PowerShell 7+ 后,试试这些新功能:

```powershell
# 三元运算符
$status = $true ? "成功" : "失败"
Write-Host $status

# null 合并运算符
$value = $null ?? "默认值"
Write-Host $value

# 并行处理
1..10 | ForEach-Object -Parallel {
    Start-Sleep -Seconds 1
    "处理项目 $_"
}

# 链式运算符 (需要 PowerShell 7+)
Test-Path "test.txt" && Write-Host "文件存在"
```

## 提示

- 两个版本可以同时存在,互不影响
- 大多数脚本在两个版本中都能运行
- VS Code 默认使用 PowerShell 5.1,需要手动切换
- 推荐日常使用 PowerShell 7+

## 如果遇到问题

如果 `pwsh` 命令不可用:
1. 重启终端/VS Code
2. 检查环境变量 PATH
3. 重新安装: `winget install Microsoft.PowerShell`
