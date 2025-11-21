"""检查数据库中订单ID的实际值"""
from database.connection import engine
from sqlalchemy import text

with engine.connect() as conn:
    results = conn.execute(text('SELECT order_id, product_name, price FROM orders LIMIT 10')).fetchall()
    
    print('='*80)
    print('📊 数据库订单ID检查 (前10条记录):')
    print('='*80)
    
    for i, (order_id, product_name, price) in enumerate(results, 1):
        print(f'{i}. order_id="{order_id}" (type={type(order_id).__name__}, len={len(str(order_id)) if order_id else 0})')
        print(f'   product="{product_name}" price={price}')
    
    print('='*80)
    
    # 统计空订单ID
    empty_count = conn.execute(text("SELECT COUNT(*) FROM orders WHERE order_id IS NULL OR order_id = ''")).scalar()
    total_count = conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
    
    print(f'\n📈 统计:')
    print(f'   总订单数: {total_count}')
    print(f'   空订单ID数: {empty_count}')
    print(f'   有效订单ID数: {total_count - empty_count}')
