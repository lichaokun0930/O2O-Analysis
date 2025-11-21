"""检查Order表中cost字段的完整性"""
import pymysql
import pandas as pd

try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Lck..0930',
        database='o2o_analysis',
        charset='utf8mb4'
    )
    
    # 检查祥和路店Order表cost字段
    query = """
    SELECT 
        store_name as 门店,
        COUNT(*) as 总订单数,
        SUM(CASE WHEN cost IS NULL THEN 1 ELSE 0 END) as cost为NULL数量,
        SUM(CASE WHEN cost = 0 THEN 1 ELSE 0 END) as cost为0数量,
        SUM(CASE WHEN cost > 0 THEN 1 ELSE 0 END) as cost大于0数量,
        SUM(cost) as cost总和
    FROM orders
    WHERE store_name = '惠宜选超市（徐州祥和路店）'
    GROUP BY store_name
    """
    
    print("📊 检查Order表中祥和路店的cost字段:\n")
    df = pd.read_sql(query, conn)
    print(df.to_string(index=False))
    
    print(f"\n💰 Order表cost总和: ¥{df['cost总和'].iloc[0]:,.2f}")
    print(f"📉 NULL比例: {df['cost为NULL数量'].iloc[0] / df['总订单数'].iloc[0] * 100:.1f}%")
    print(f"📉 为0比例: {df['cost为0数量'].iloc[0] / df['总订单数'].iloc[0] * 100:.1f}%")
    
    # 对比Product表的current_cost
    query2 = """
    SELECT 
        '通过Product表JOIN' as 来源,
        COUNT(*) as 总订单数,
        SUM(CASE WHEN p.current_cost IS NULL THEN 1 ELSE 0 END) as cost为NULL数量,
        SUM(p.current_cost * o.quantity) as cost总和
    FROM orders o
    LEFT JOIN products p ON o.barcode = p.barcode
    WHERE o.store_name = '惠宜选超市（徐州祥和路店）'
    """
    
    print(f"\n📊 对比Product表current_cost JOIN结果:\n")
    df2 = pd.read_sql(query2, conn)
    print(df2.to_string(index=False))
    
    conn.close()
    print("\n✅ 检查完成")
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
