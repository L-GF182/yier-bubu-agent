# database.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "waimai.db")

def get_db():
    """获取数据库连接，启用外键约束"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # 让查询结果支持按列名访问
    return conn

def init_db():
    """初始化数据库：创建表 + 插入默认菜单"""
    conn = get_db()
    cursor = conn.cursor()

    # 菜单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            item_id   TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            price     REAL NOT NULL,
            category  TEXT DEFAULT '主食',
            stock     INTEGER DEFAULT 100,
            available INTEGER DEFAULT 1
        )
    """)

    # 订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id    TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL DEFAULT 'user_001',
            status      TEXT NOT NULL DEFAULT '待接单',
            total_price REAL NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 订单明细表（解决订单-菜单多对多关系）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id     TEXT NOT NULL,
            item_id      TEXT NOT NULL,
            quantity     INTEGER NOT NULL,
            unit_price   REAL NOT NULL,     -- 下单时的快照价格
            subtotal     REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (item_id)  REFERENCES menu(item_id)
        )
    """)

    # 初始化菜单数据（仅在表为空时插入）
    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        menu_data = [
            ("M001", "宫保鸡丁+米饭", 25.0, "主食", 50),
            ("M002", "鱼香肉丝+米饭", 22.0, "主食", 40),
            ("M003", "麻婆豆腐+米饭", 18.0, "主食", 30),
            ("M004", "牛肉面", 28.0, "面食", 35),
            ("M005", "麻辣烫", 42.0, "特色", 20),
            ("M006", "可乐", 6.0, "饮品", 100),
        ]
        cursor.executemany(
            "INSERT INTO menu (item_id, name, price, category, stock) VALUES (?,?,?,?,?)",
            menu_data
        )

    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成：{DB_PATH}")


if __name__ == "__main__":
    init_db()