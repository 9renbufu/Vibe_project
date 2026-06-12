"""
Voice Designer Agent 启动脚本
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main_v4:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
