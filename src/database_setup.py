import pymysql
from pymysql import Error
from typing import List, Dict, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
import threading
import time
from src.config import DB_CONFIG



# ---------- 连接 ----------
def get_conn(**kw):
    cfg = {**DB_CONFIG, **kw}
    return pymysql.connect(**cfg, cursorclass=pymysql.cursors.DictCursor)

# ---------- 建库建表 ----------
def create_database():
    with get_conn(database=None) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()

def create_tables():
    ddl = """
CREATE TABLE IF NOT EXISTS Merchants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  login_user VARCHAR(50) UNIQUE NOT NULL,
  login_pwd VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Merchant_Balance (
  merchant_id INT PRIMARY KEY,
  balance DECIMAL(10,2) NOT NULL DEFAULT 0,
  bank_name VARCHAR(100) DEFAULT '',
  bank_account VARCHAR(50) DEFAULT '',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (merchant_id) REFERENCES Merchants(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  phone VARCHAR(20),
  points INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  sku VARCHAR(50) UNIQUE NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  stock INT DEFAULT 0,
  category VARCHAR(100),
  image_url VARCHAR(500),
  description TEXT,
  is_vip TINYINT(1) DEFAULT 0 COMMENT '1=会员商品',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Cart (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT DEFAULT 1,
  selected TINYINT DEFAULT 1,
  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE,
  UNIQUE KEY uk_user_product (user_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  order_number VARCHAR(50) UNIQUE NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  status ENUM('pending_pay','pending_ship','pending_recv','refund','completed') DEFAULT 'pending_pay',
  consignee_name VARCHAR(100) NOT NULL,
  consignee_phone VARCHAR(20) NOT NULL,
  province VARCHAR(20) NOT NULL DEFAULT '',
  city VARCHAR(20) NOT NULL DEFAULT '',
  district VARCHAR(20) NOT NULL DEFAULT '',
  shipping_address TEXT NOT NULL,
  pay_way ENUM('alipay','wechat','card','wx_pub','wx_app') DEFAULT 'alipay',
  is_vip_item TINYINT(1) DEFAULT 0 COMMENT '1=含会员商品',
  refund_reason TEXT,
  auto_recv_time DATETIME NULL COMMENT '7 天后自动收货',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Order_Items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  total_price DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES Orders(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Refunds (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_number VARCHAR(50) NOT NULL,
  refund_type ENUM('return','refund_only') NOT NULL COMMENT 'return=退货退款，refund_only=仅退款',
  reason TEXT NOT NULL,
  status ENUM('applied','seller_ok','success','rejected') DEFAULT 'applied',
  reject_reason TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (order_number) REFERENCES Orders(order_number) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS User_Addresses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  label VARCHAR(20) NOT NULL COMMENT '家/公司/朋友',
  consignee_name VARCHAR(100) NOT NULL,
  consignee_phone VARCHAR(20) NOT NULL,
  province VARCHAR(20) NOT NULL DEFAULT '',
  city VARCHAR(20) NOT NULL DEFAULT '',
  district VARCHAR(20) NOT NULL DEFAULT '',
  detail TEXT NOT NULL,
  lng DECIMAL(10,6) NULL,
  lat DECIMAL(10,6) NULL,
  is_default TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
  INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS order_split (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_number VARCHAR(50) NOT NULL,
  item_type ENUM('merchant','pool') NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  pool_type VARCHAR(20) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS merchant_statement (
  merchant_id INT NOT NULL,
  date DATE NOT NULL,
  opening_balance DECIMAL(10,2) NOT NULL,
  income DECIMAL(10,2) NOT NULL,
  withdraw DECIMAL(10,2) NOT NULL,
  closing_balance DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (merchant_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS alert_order (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_number VARCHAR(50) NOT NULL,
  alert_type VARCHAR(50) NOT NULL,
  detail TEXT NOT NULL,
  is_handled TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            for stmt in ddl.split(";"):
                stmt = stmt.strip()
                if stmt:
                    cur.execute(stmt)
        conn.commit()

# ---------- 样例数据 ----------
def insert_sample():
    with get_conn() as conn:
        with conn.cursor() as cur:
            # users
            users = [(1, "张三", "zhangsan@example.com", "13800138001"),
                     (2, "李四", "lisi@example.com", "13800138002"),
                     (3, "王五", "wangwu@example.com", "13800138003")]
            for u in users:
                cur.execute("REPLACE INTO Users(id,name,email,phone) VALUES(%s,%s,%s,%s)", u)
            # products
            products = [
                (1, "iPhone 15 Pro", "IP15P-001", 7999.00, 100, "手机", "", "最新款iPhone", 1),
                (2, "MacBook Pro", "MBP-2023", 12999.00, 50, "电脑", "", "苹果笔记本", 0),
                (3, "AirPods Pro", "APP-002", 1899.00, 200, "耳机", "", "无线蓝牙", 1),
                (4, "iPad Air", "IPA-003", 4599.00, 80, "平板", "", "轻薄便携", 0),
                (5, "Apple Watch", "AW-004", 2999.00, 150, "手表", "", "智能手表", 1),
            ]
            for p in products:
                cur.execute("REPLACE INTO Products(id,name,sku,price,stock,category,image_url,description,is_vip) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)", p)
            # cart
            carts = [(1, 1, 2, 1, 1), (1, 2, 1, 1, 1), (2, 3, 3, 0, 1), (2, 4, 1, 1, 1)]
            for c in carts:
                cur.execute("REPLACE INTO Cart(user_id,product_id,quantity,selected) VALUES(%s,%s,%s,%s)", c[0:4])
            # merchant
            cur.execute("REPLACE INTO Merchants(id,name,login_user,login_pwd) VALUES(1,'官方旗舰店','admin','123456')")
            cur.execute("REPLACE INTO Merchant_Balance(merchant_id,balance) VALUES(1,0)")
        conn.commit()

# ---------- 一键初始化 ----------
def init_db():
    create_database()
    create_tables()
    insert_sample()
    print("[database_setup] 初始化完成！")

# ---------- 自动收货 & 结算 守护 ----------
def auto_receive_task(db_cfg: dict):
    def run():
        while True:
            try:
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        now = datetime.now()
                        cur.execute("SELECT id,order_number,total_amount FROM Orders WHERE status='pending_recv' AND auto_recv_time<=%s", now)
                        for row in cur.fetchall():
                            cur.execute("UPDATE Orders SET status='completed' WHERE id=%s", row["id"])
                            from src.finance_logic import settle_to_merchant
                            settle_to_merchant(row["total_amount"])
                            conn.commit()
                            print(f"[auto_receive] 订单 {row['order_number']} 已自动完成并结算。")
            except Exception as e:
                print("[auto_receive] 异常:", e)
            time.sleep(3600)  # 每小时扫一次
    t = threading.Thread(target=run, daemon=True)
    t.start()