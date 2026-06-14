"""启动语音绘图工具后端"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main_drawing:app", host="0.0.0.0", port=8000, reload=True)
