from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src.routes import register_all
from src.fasteners import auto_receive_task

app = FastAPI(title="电商全功能-模块化版", version="1.0")

@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html><head><meta charset="utf-8"><title>电商接口</title></head>
<body><h2>电商全功能接口文档</h2><a href="/docs">进入 Swagger</a></body></html>"""

# 注册所有路由
register_all(app)

# 启动守护线程
auto_receive_task()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)