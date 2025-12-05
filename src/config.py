import os
from enum import Enum


# 数据库
DB_CONFIG = dict(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PWD", "123456"),
    database=os.getenv("DB_NAME", "ecommerce"),
    charset="utf8mb4",
)

# 支付
VALID_PAY_WAYS = {"alipay", "wechat", "card", "wx_pub", "wx_app"}

# 订单状态
class OStatus(str, Enum):
    PENDING_PAY = "pending_pay"
    PENDING_SHIP = "pending_ship"
    PENDING_RECV = "pending_recv"
    COMPLETED = "completed"
    REFUND = "refund"

# 退款状态
class RStatus(str, Enum):
    APPLIED = "applied"
    SELLER_OK = "seller_ok"
    SUCCESS = "success"
    REJECTED = "rejected"