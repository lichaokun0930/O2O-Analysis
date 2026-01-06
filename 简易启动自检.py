#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简易启动自检
避免复杂导入，只检查最关键的项目
"""

import sys


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        return False, f"Python版本过低（{version.major}.{version.minor}）"
    return True, f"Python {version.major}.{version.minor}.{version.micro}"


def check_redis_service():
    """检查Redis服务"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
        r.ping()
        return True, "Redis服务正常"
    except ImportError:
        return False, "Redis模块未安装"
    except Exception:
        return False, "Redis服务未启动"


def check_database():
    """检查数据库"""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(
            'postgresql+pg8000://postgres:postgres@localhost:5432/o2o_dashboard',
            pool_pre_ping=True
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "数据库连接正常"
    except Exception:
        return False, "数据库连接失败"


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(" 简易启动自检")
    print("=" * 60 + "\n")
    
    checks = [
        ("Python版本", check_python_version),
        ("Redis服务", check_redis_service),
        ("数据库连接", check_database),
    ]
    
    all_passed = True
    
    for i, (name, check_func) in enumerate(checks, 1):
        print(f"[{i}/{len(checks)}] {name}...", end=" ")
        try:
            passed, message = check_func()
            if passed:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
                all_passed = False
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print(" ✅ 所有检查通过")
    else:
        print(" ⚠️  部分检查失败")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
