"""
Tab 4 问题诊断模块 - 快速功能测试脚本
测试所有Tab是否能正常加载和基本交互
"""

import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 测试配置
BASE_URL = "http://localhost:8050"
TIMEOUT = 10

def print_result(test_name, passed, message=""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"    {message}")

def test_page_load(driver):
    """测试1: 页面加载"""
    print("\n" + "="*60)
    print("测试1: 页面基本加载")
    print("="*60)
    
    try:
        driver.get(BASE_URL)
        time.sleep(2)
        
        # 检查页面标题
        title = driver.title
        print_result("页面标题检查", "智能门店" in title or "Dash" in title, f"标题: {title}")
        
        # 检查是否有Tab组件
        tabs = driver.find_elements(By.CLASS_NAME, "tab")
        print_result("Tab组件加载", len(tabs) > 0, f"找到 {len(tabs)} 个Tab")
        
        return True
    except Exception as e:
        print_result("页面加载", False, str(e))
        return False

def test_tab_navigation(driver):
    """测试2: Tab导航"""
    print("\n" + "="*60)
    print("测试2: Tab导航功能")
    print("="*60)
    
    tab_names = [
        ("tab-4-1", "销量下滑诊断"),
        ("tab-4-2", "客单价归因"),
        ("tab-4-3", "负毛利预警"),
        ("tab-4-4", "高配送费诊断"),
        ("tab-4-5", "角色失衡诊断"),
        ("tab-4-6", "异常波动预警")
    ]
    
    for tab_id, tab_name in tab_names:
        try:
            # 查找Tab标签
            tab_element = driver.find_element(By.CSS_SELECTOR, f'[value="{tab_id}"]')
            print_result(f"Tab {tab_name} 存在", True)
            
            # 点击Tab
            tab_element.click()
            time.sleep(1)
            
            # 验证Tab内容区域显示
            # Tab内容应该是可见的
            print_result(f"Tab {tab_name} 可点击", True)
            
        except NoSuchElementException:
            print_result(f"Tab {tab_name}", False, "Tab未找到")
        except Exception as e:
            print_result(f"Tab {tab_name}", False, str(e))

def test_tab_4_1_basic(driver):
    """测试3: Tab 4.1 基本功能"""
    print("\n" + "="*60)
    print("测试3: Tab 4.1 销量下滑诊断")
    print("="*60)
    
    try:
        # 切换到Tab 4.1
        tab_41 = driver.find_element(By.CSS_SELECTOR, '[value="tab-4-1"]')
        tab_41.click()
        time.sleep(1)
        
        # 检查参数配置区域
        try:
            period_selector = driver.find_element(By.ID, "time-period-selector")
            print_result("时间粒度选择器", True)
        except:
            print_result("时间粒度选择器", False)
        
        try:
            threshold_slider = driver.find_element(By.ID, "decline-threshold-slider")
            print_result("下滑阈值滑块", True)
        except:
            print_result("下滑阈值滑块", False)
        
        try:
            diagnose_btn = driver.find_element(By.ID, "btn-diagnose")
            print_result("开始诊断按钮", True)
        except:
            print_result("开始诊断按钮", False)
        
        # 检查图表区域（通过查找Graph组件）
        try:
            graphs = driver.find_elements(By.CLASS_NAME, "js-plotly-plot")
            print_result("图表组件加载", len(graphs) >= 10, f"找到 {len(graphs)} 个图表")
        except:
            print_result("图表组件加载", False)
        
    except Exception as e:
        print_result("Tab 4.1 测试", False, str(e))

def test_tab_4_2_basic(driver):
    """测试4: Tab 4.2 基本功能"""
    print("\n" + "="*60)
    print("测试4: Tab 4.2 客单价归因")
    print("="*60)
    
    try:
        # 切换到Tab 4.2
        tab_42 = driver.find_element(By.CSS_SELECTOR, '[value="tab-4-2"]')
        tab_42.click()
        time.sleep(1)
        
        # 检查参数配置
        try:
            price_period = driver.find_element(By.ID, "price-period-selector")
            print_result("分析粒度选择器", True)
        except:
            print_result("分析粒度选择器", False)
        
        try:
            price_threshold = driver.find_element(By.ID, "price-threshold-slider")
            print_result("客单价阈值滑块", True)
        except:
            print_result("客单价阈值滑块", False)
        
        try:
            price_mode = driver.find_element(By.ID, "price-analysis-mode")
            print_result("分析模式选择器", True)
        except:
            print_result("分析模式选择器", False)
        
        try:
            analyze_btn = driver.find_element(By.ID, "btn-price-analyze")
            print_result("开始归因按钮", True)
        except:
            print_result("开始归因按钮", False)
        
    except Exception as e:
        print_result("Tab 4.2 测试", False, str(e))

def test_tab_4_3_basic(driver):
    """测试5: Tab 4.3 基本功能"""
    print("\n" + "="*60)
    print("测试5: Tab 4.3 负毛利预警")
    print("="*60)
    
    try:
        # 切换到Tab 4.3
        tab_43 = driver.find_element(By.CSS_SELECTOR, '[value="tab-4-3"]')
        tab_43.click()
        time.sleep(1)
        
        # 检查立即检测按钮
        try:
            check_btn = driver.find_element(By.ID, "btn-margin-check")
            print_result("立即检测按钮", True)
        except:
            print_result("立即检测按钮", False)
        
        # 检查数据表格
        try:
            table = driver.find_element(By.ID, "margin-table")
            print_result("负毛利表格", True)
        except:
            print_result("负毛利表格", False)
        
    except Exception as e:
        print_result("Tab 4.3 测试", False, str(e))

def test_tab_4_4_basic(driver):
    """测试6: Tab 4.4 基本功能"""
    print("\n" + "="*60)
    print("测试6: Tab 4.4 高配送费诊断")
    print("="*60)
    
    try:
        # 切换到Tab 4.4
        tab_44 = driver.find_element(By.CSS_SELECTOR, '[value="tab-4-4"]')
        tab_44.click()
        time.sleep(1)
        
        # 检查阈值滑块
        try:
            fee_slider = driver.find_element(By.ID, "fee-threshold-slider")
            print_result("配送费阈值滑块", True)
        except:
            print_result("配送费阈值滑块", False)
        
        # 检查诊断按钮
        try:
            check_btn = driver.find_element(By.ID, "btn-delivery-check")
            print_result("开始诊断按钮", True)
        except:
            print_result("开始诊断按钮", False)
        
    except Exception as e:
        print_result("Tab 4.4 测试", False, str(e))

def test_tab_4_5_basic(driver):
    """测试7: Tab 4.5 基本功能"""
    print("\n" + "="*60)
    print("测试7: Tab 4.5 角色失衡诊断")
    print("="*60)
    
    try:
        # 切换到Tab 4.5
        tab_45 = driver.find_element(By.CSS_SELECTOR, '[value="tab-4-5"]')
        tab_45.click()
        time.sleep(1)
        
        # 检查开始检测按钮
        try:
            check_btn = driver.find_element(By.ID, "btn-balance-check")
            print_result("开始检测按钮", True)
        except:
            print_result("开始检测按钮", False)
        
    except Exception as e:
        print_result("Tab 4.5 测试", False, str(e))

def test_tab_4_6_basic(driver):
    """测试8: Tab 4.6 基本功能"""
    print("\n" + "="*60)
    print("测试8: Tab 4.6 异常波动预警")
    print("="*60)
    
    try:
        # 切换到Tab 4.6
        tab_46 = driver.find_element(By.CSS_SELECTOR, '[value="tab-4-6"]')
        tab_46.click()
        time.sleep(1)
        
        # 检查波动阈值滑块
        try:
            fluctuation_slider = driver.find_element(By.ID, "fluctuation-threshold-slider")
            print_result("波动阈值滑块", True)
        except:
            print_result("波动阈值滑块", False)
        
        # 检查预警按钮
        try:
            check_btn = driver.find_element(By.ID, "btn-fluctuation-check")
            print_result("开始预警按钮", True)
        except:
            print_result("开始预警按钮", False)
        
    except Exception as e:
        print_result("Tab 4.6 测试", False, str(e))

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("🧪 Tab 4 问题诊断模块 - 自动化测试")
    print("="*60)
    print(f"测试地址: {BASE_URL}")
    print(f"超时设置: {TIMEOUT}秒")
    print("="*60)
    
    # 初始化WebDriver（需要安装ChromeDriver或EdgeDriver）
    try:
        # 尝试使用Edge
        from selenium.webdriver.edge.service import Service as EdgeService
        from selenium.webdriver.edge.options import Options as EdgeOptions
        
        options = EdgeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        
        driver = webdriver.Edge(options=options)
        print("✅ 使用 Microsoft Edge 浏览器")
    except:
        try:
            # 尝试使用Chrome
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            
            options = ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            
            driver = webdriver.Chrome(options=options)
            print("✅ 使用 Google Chrome 浏览器")
        except Exception as e:
            print(f"❌ 无法启动浏览器: {e}")
            print("\n提示: 请安装 Selenium WebDriver")
            print("  pip install selenium")
            print("  并下载对应的浏览器驱动 (ChromeDriver 或 EdgeDriver)")
            return
    
    try:
        # 设置隐式等待
        driver.implicitly_wait(TIMEOUT)
        
        # 执行测试
        test_page_load(driver)
        test_tab_navigation(driver)
        test_tab_4_1_basic(driver)
        test_tab_4_2_basic(driver)
        test_tab_4_3_basic(driver)
        test_tab_4_4_basic(driver)
        test_tab_4_5_basic(driver)
        test_tab_4_6_basic(driver)
        
        # 测试总结
        print("\n" + "="*60)
        print("🎉 测试完成！")
        print("="*60)
        print("\n提示: 这只是基本的UI组件测试")
        print("      完整的功能测试请参考 'Tab4_功能测试清单.md'")
        print("      手动测试所有按钮点击和数据交互功能")
        
    finally:
        driver.quit()
        print("\n浏览器已关闭")

if __name__ == "__main__":
    main()
