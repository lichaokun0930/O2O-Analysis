"""直接查询数据库,检查祥和路门店的成本数据"""
import pymysql
import pandas as pd

try:
    # 连接数据库
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Lck.115911',
        database='o2o_analysis',
        charset='utf8mb4'
    )
    
    # 查询祥和路门店数据
    query = """
    SELECT 
        COUNT(*) as 总行数,
        SUM(cost) as 成本总和,
        COUNT(CASE WHEN cost IS NULL THEN 1 END) as 成本NULL数量,
        COUNT(CASE WHEN cost = 0 THEN 1 END) as 成本为0数量,
        COUNT(CASE WHEN cost > 0 THEN 1 END) as 成本大于0数量
    FROM orders
    WHERE store_name = '惠宜选超市（徐州祥和路店）'
    """
    
    print("🔍 查询祥和路门店成本数据...")
    print(f"SQL: {query}\n")
    
    df = pd.read_sql(query, conn)
    print("📊 数据库查询结果:")
    print(df.to_string(index=False))
    print(f"\n💰 成本总和: ¥{df['成本总和'].iloc[0]:,.2f}")
    
    # 详细查看前10条数据
    detail_query = """
    SELECT 
        order_id as 订单ID,
        product_name as 商品名称,
        cost as 成本,
        selling_price as 售价,
        sales_volume as 销量
    FROM orders
    WHERE store_name = '惠宜选超市（徐州祥和路店）'
    LIMIT 10
    """
    
    print(f"\n📋 前10条数据样本:")
    df_sample = pd.read_sql(detail_query, conn)
    print(df_sample.to_string(index=False))
    
    conn.close()
    print("\n✅ 查询完成")
    
except Exception as e:
    print(f"❌ 查询失败: {e}")
    import traceback
    traceback.print_exc()
