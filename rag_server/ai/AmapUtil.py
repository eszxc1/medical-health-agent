import os
import requests as req

# ★ 新增：高德地图 API 工具函数（与 LoadLLM.py 风格一致）

AMAP_API_KEY = os.getenv("AMAP_API_KEY")

def get(url, params):
    """调用高德地图 API 的通用 GET 请求"""
    params["key"] = AMAP_API_KEY
    params["output"] = "JSON"
    return req.get(url, params=params, timeout=5).json()
