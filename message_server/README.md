# FileTidy 消息服务端模块 - 综合使用文档

## 📋 模块概述

消息服务端模块是 FileTidy 的独立消息管理服务，基于 Flask 构建，提供消息推送、管理、统计等功能。支持 HTTP API 远程调用，可被任意语言/框架的客户端集成。

## 🚀 快速开始

### 运行服务器

```bash
# 安装依赖
cd message_server
pip install -r message_server_requirements.txt

# 源码版本启动
python message_server.py

# 编译版本启动
python run_compiled.py
```

### 访问管理界面

打开浏览器访问: `http://120.79.249.9:1002/message_admin.html`

## 🎯 核心功能

- **消息管理**: 创建、更新、删除、查询消息
- **消息推送**: 实时推送、批量推送、定时推送
- **安全功能**: 请求频率限制、来源验证、日志记录
- **统计功能**: 消息统计、访问统计、性能监控

## 📁 模块文件结构

| 文件 | 作用 |
|------|------|
| `message_server.py` | 核心服务源码（Flask app，全部 API 路由） |
| `message_admin.html` | 管理后台前端页面 |
| `messages.json` | 消息持久化存储文件 |
| `message_server_requirements.txt` | Python 依赖清单 |
| `01_compile_message_server_pyd.py` | Cython 编译脚本（.py → .pyd） |
| `run_compiled.py` | 编译版启动器 |
| `build/compiled/message_server.pyd` | 编译后的二进制模块 |

## 📝 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/api/messages` | GET | 获取消息列表 |
| `/api/messages/<id>` | GET | 获取单个消息 |
| `/api/messages` | POST | 创建消息 |
| `/api/messages/<id>` | PUT | 更新消息 |
| `/api/messages/<id>` | DELETE | 删除消息 |
| `/api/messages/batch` | POST | 批量创建 |
| `/api/messages/clear` | DELETE | 清空消息 |
| `/api/messages/stats` | GET | 获取统计 |

---

## 🔗 集成方案

其他项目集成本模块，推荐采用 **HTTP API 远程调用** 方式（最松耦合），将消息服务端作为独立微服务部署，客户端通过 RESTful API 交互。

### 集成架构

```
┌─────────────────────┐       HTTP API        ┌──────────────────────┐
│   客户端项目         │ ──────────────────────→ │  message_server      │
│   (Python/任意语言)  │ ←────────────────────── │  Flask :1002         │
│                     │       JSON Response     │                      │
└─────────────────────┘                         │  ┌─ message_admin   │
                                                │  │  .html (管理UI)  │
                                                │  └─────────────────│
                                                │  ┌─ messages.json   │
                                                │  │  (数据存储)      │
                                                │  └─────────────────│
                                                └──────────────────────┘
```

### 基础配置

| 项目 | 值 |
|------|-----|
| 服务地址 | `http://120.79.249.9:1002`（按实际部署修改） |
| 协议 | HTTP |
| 数据格式 | JSON（`Content-Type: application/json`） |
| 字符编码 | UTF-8 |

---

## 📖 Python 客户端获取消息开发文档

### 1. 前置准备

```bash
pip install requests
```

### 2. 消息数据结构

客户端获取到的消息对象包含以下字段：

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `id` | str | 是 | 消息唯一标识 |
| `title` | str | 是 | 消息标题 |
| `content` | str | 是 | 消息正文 |
| `type` | str | 是 | 消息类型，枚举值见下表 |
| `priority` | int | 是 | 优先级，正整数，越小越紧急 |
| `created_at` | str | 是 | 创建时间，ISO 8601 格式 |
| `read` | bool | 否 | 是否已读，字段可能不存在 |

**消息类型枚举**：

| 类型值 | 含义 | 典型场景 |
|--------|------|----------|
| `info` | 一般通知 | 功能介绍、使用提示 |
| `warning` | 警告 | 配置异常、资源不足 |
| `error` | 错误 | 服务故障、操作失败 |
| `success` | 成功 | 操作完成、任务成功 |
| `promotion` | 推广 | 活动通知、功能推荐 |
| `update` | 更新 | 版本升级、功能变更 |
| `maintenance` | 维护 | 计划停机、服务降级 |

### 3. API 端点详解

#### 3.1 健康检查

```
GET /health
```

| 项目 | 值 |
|------|-----|
| 频率限制 | 无 |
| 超时建议 | 5 秒 |
| 用途 | 启动时检测服务可用性、定时探活 |

**响应**：

```json
{
  "status": "healthy",
  "timestamp": "2026-06-12T10:30:00"
}
```

#### 3.2 获取消息列表

```
GET /api/messages
```

| 项目 | 值 |
|------|-----|
| 频率限制 | 60 次/分钟 |
| 超时建议 | 10 秒 |

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | str | 否 | — | 按类型筛选，值为 7 种类型枚举之一 |
| `sort` | str | 否 | `priority` | `priority`：按优先级升序（紧急在前）；`date`：按时间降序（最新在前） |

**请求示例**：

```python
import requests

SERVER_URL = "http://120.79.249.9:1002"

# 获取全部消息（默认按优先级排序）
requests.get(f"{SERVER_URL}/api/messages")

# 只获取 warning 类型
requests.get(f"{SERVER_URL}/api/messages", params={"type": "warning"})

# 按时间倒序获取全部消息
requests.get(f"{SERVER_URL}/api/messages", params={"sort": "date"})

# 获取 update 类型 + 按时间倒序
requests.get(f"{SERVER_URL}/api/messages", params={"type": "update", "sort": "date"})
```

**成功响应**（`200`）：

```json
{
  "success": true,
  "messages": [
    {
      "id": "msg-001",
      "title": "系统维护通知",
      "content": "系统将于今晚22:00进行维护",
      "type": "maintenance",
      "priority": 1,
      "created_at": "2026-06-12T08:00:00",
      "read": false
    }
  ],
  "count": 1,
  "version": "1.0",
  "updated_at": "2026-06-12T08:00:00"
}
```

**响应字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 请求是否成功 |
| `messages` | array | 消息对象数组 |
| `count` | int | 当前返回的消息数量 |
| `version` | str | 数据版本号 |
| `updated_at` | str | 数据最后更新时间 |

#### 3.3 获取单条消息

```
GET /api/messages/<message_id>
```

| 项目 | 值 |
|------|-----|
| 频率限制 | 100 次/分钟 |
| 超时建议 | 10 秒 |

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `message_id` | str | 消息的唯一 ID |

**成功响应**（`200`）：

```json
{
  "success": true,
  "message": {
    "id": "msg-001",
    "title": "系统维护通知",
    "content": "系统将于今晚22:00进行维护",
    "type": "maintenance",
    "priority": 1,
    "created_at": "2026-06-12T08:00:00"
  }
}
```

**消息不存在**（`404`）：

```json
{
  "success": false,
  "error": "消息不存在"
}
```

#### 3.4 获取消息统计

```
GET /api/messages/stats
```

| 项目 | 值 |
|------|-----|
| 频率限制 | 30 次/分钟 |
| 超时建议 | 10 秒 |

**成功响应**（`200`）：

```json
{
  "success": true,
  "stats": {
    "total": 15,
    "by_type": {
      "info": 5,
      "warning": 3,
      "error": 1,
      "maintenance": 2,
      "update": 4
    },
    "by_priority": {
      "1": 3,
      "2": 5,
      "3": 7
    },
    "unread": 8
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `stats.total` | int | 消息总数 |
| `stats.by_type` | dict[str, int] | 按类型分组计数 |
| `stats.by_priority` | dict[str, int] | 按优先级分组计数 |
| `stats.unread` | int | 未读消息数 |

### 4. 错误处理

**统一错误格式**：

```json
{
  "success": false,
  "error": "错误简要描述"
}
```

**HTTP 状态码与处理建议**：

| 状态码 | 含义 | 客户端处理建议 |
|--------|------|----------------|
| `200` | 成功 | 正常解析数据 |
| `404` | 资源不存在 | 消息 ID 无效时返回 `None`，路径错误时检查 URL |
| `429` | 频率超限 | 等待后重试，响应体含 `message` 字段说明限制值 |
| `500` | 服务器错误 | 记录日志，降级处理，稍后重试 |

**429 响应示例**：

```json
{
  "success": false,
  "error": "请求频率过高，请稍后再试",
  "message": "60 per 1 minute"
}
```

### 5. 完整客户端封装

以下是一个可直接集成到项目中的客户端类：

```python
import requests
from typing import Optional


class MessageServerClient:
    """消息服务端客户端"""

    VALID_TYPES = {"info", "warning", "error", "success", "promotion", "update", "maintenance"}
    VALID_SORTS = {"priority", "date"}

    def __init__(self, server_url: str = "http://120.79.249.9:1002", timeout: int = 10):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.server_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        return requests.request(method, url, **kwargs)

    def check_health(self) -> dict:
        """健康检查，返回 {'status': 'healthy', 'timestamp': '...'}"""
        resp = self._request("GET", "/health", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def is_healthy(self) -> bool:
        """健康检查，返回布尔值"""
        try:
            data = self.check_health()
            return data.get("status") == "healthy"
        except requests.RequestException:
            return False

    def get_messages(
        self,
        msg_type: Optional[str] = None,
        sort: str = "priority"
    ) -> list[dict]:
        """
        获取消息列表

        参数:
            msg_type: 按类型筛选，None 表示全部，可选值见 VALID_TYPES
            sort: 排序方式，'priority' 按优先级升序，'date' 按时间降序

        返回:
            消息字典列表，失败时抛出 requests.HTTPError
        """
        if msg_type is not None and msg_type not in self.VALID_TYPES:
            raise ValueError(f"无效的消息类型: {msg_type}，可选值: {self.VALID_TYPES}")
        if sort not in self.VALID_SORTS:
            raise ValueError(f"无效的排序方式: {sort}，可选值: {self.VALID_SORTS}")

        params = {"sort": sort}
        if msg_type is not None:
            params["type"] = msg_type

        resp = self._request("GET", "/api/messages", params=params)
        resp.raise_for_status()
        return resp.json()["messages"]

    def get_message(self, message_id: str) -> Optional[dict]:
        """
        获取单条消息

        参数:
            message_id: 消息唯一 ID

        返回:
            消息字典，不存在时返回 None
        """
        resp = self._request("GET", f"/api/messages/{message_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()["message"]

    def get_stats(self) -> dict:
        """
        获取消息统计

        返回:
            {'total': int, 'by_type': dict, 'by_priority': dict, 'unread': int}
        """
        resp = self._request("GET", "/api/messages/stats")
        resp.raise_for_status()
        return resp.json()["stats"]

    def get_unread_count(self) -> int:
        """获取未读消息数量（快捷方法）"""
        stats = self.get_stats()
        return stats.get("unread", 0)

    def get_messages_by_type(self, msg_type: str, sort: str = "priority") -> list[dict]:
        """按类型获取消息（快捷方法）"""
        return self.get_messages(msg_type=msg_type, sort=sort)

    def get_latest_messages(self, msg_type: Optional[str] = None) -> list[dict]:
        """获取最新消息（按时间倒序，快捷方法）"""
        return self.get_messages(msg_type=msg_type, sort="date")

    def get_urgent_messages(self, msg_type: Optional[str] = None) -> list[dict]:
        """获取紧急消息（按优先级升序，快捷方法）"""
        return self.get_messages(msg_type=msg_type, sort="priority")
```

### 6. 使用示例

#### 6.1 基础用法

```python
client = MessageServerClient(server_url="http://120.79.249.9:1002")

# 健康检查
if client.is_healthy():
    print("消息服务正常")

# 获取全部消息（按优先级）
messages = client.get_messages()
for msg in messages:
    print(f"[{msg['type']}] {msg['title']}: {msg['content']}")

# 获取单条消息
msg = client.get_message("msg-001")
if msg:
    print(f"标题: {msg['title']}, 内容: {msg['content']}")
else:
    print("消息不存在")

# 获取统计
stats = client.get_stats()
print(f"总数: {stats['total']}, 未读: {stats['unread']}")
```

#### 6.2 按类型筛选

```python
# 只获取警告消息
warnings = client.get_messages_by_type("warning")

# 只获取维护通知
maintenance = client.get_messages_by_type("maintenance")

# 获取所有类型枚举
for t in MessageServerClient.VALID_TYPES:
    msgs = client.get_messages_by_type(t)
    print(f"{t}: {len(msgs)} 条")
```

#### 6.3 排序控制

```python
# 按优先级（紧急在前，默认行为）
urgent = client.get_urgent_messages()

# 按时间（最新在前）
latest = client.get_latest_messages()

# 指定类型 + 排序
latest_warnings = client.get_latest_messages(msg_type="warning")
```

#### 6.4 统计与未读

```python
# 快捷获取未读数
unread_count = client.get_unread_count()
print(f"您有 {unread_count} 条未读消息")

# 完整统计
stats = client.get_stats()
print(f"总消息: {stats['total']}")
print(f"各类型: {stats['by_type']}")
print(f"各优先级: {stats['by_priority']}")
```

#### 6.5 带错误处理的完整示例

```python
import requests
import logging
import time

logger = logging.getLogger(__name__)
client = MessageServerClient(server_url="http://120.79.249.9:1002", timeout=10)


def fetch_messages_with_retry(max_retries: int = 3, retry_delay: float = 2.0) -> list[dict]:
    """带重试的消息获取"""
    for attempt in range(1, max_retries + 1):
        try:
            messages = client.get_messages()
            logger.info(f"成功获取 {len(messages)} 条消息")
            return messages
        except requests.exceptions.ConnectionError:
            logger.warning(f"连接失败，第 {attempt}/{max_retries} 次重试...")
        except requests.exceptions.Timeout:
            logger.warning(f"请求超时，第 {attempt}/{max_retries} 次重试...")
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", retry_delay))
                logger.warning(f"频率超限，等待 {retry_after} 秒后重试...")
                time.sleep(retry_after)
                continue
            logger.error(f"HTTP 错误: {e}")
            raise
        if attempt < max_retries:
            time.sleep(retry_delay)
    logger.error(f"获取消息失败，已重试 {max_retries} 次")
    return []


def poll_messages(interval: float = 30.0):
    """定时轮询消息（示例）"""
    while True:
        try:
            if not client.is_healthy():
                logger.warning("消息服务不可用，跳过本次轮询")
                continue

            unread = client.get_unread_count()
            if unread > 0:
                messages = client.get_latest_messages()
                for msg in messages[:5]:
                    print(f"  [{msg['type'].upper()}] {msg['title']}")
        except requests.RequestException as e:
            logger.error(f"轮询异常: {e}")

        time.sleep(interval)
```

### 7. 注意事项

| 项目 | 建议 |
|------|------|
| **超时设置** | 健康检查 5 秒，数据请求 10 秒 |
| **轮询间隔** | ≥ 30 秒，避免触发 429 频率限制 |
| **本地缓存** | 获取到的消息建议本地缓存，避免重复请求相同数据 |
| **降级处理** | 服务不可用时应有兜底逻辑（如显示缓存数据或跳过消息展示） |
| **429 重试** | 遇到 429 时检查 `Retry-After` 响应头，按指定秒数等待后重试 |
| **类型校验** | 传入 `type` 参数前可用 `MessageServerClient.VALID_TYPES` 校验，避免无效请求 |
| **线程安全** | `requests.Session` 非线程安全；若多线程调用，每个线程应创建独立客户端实例 |

---

## 📦 打包部署

### 统一打包（推荐）

```bash
# 打包所有模块
python 打包/03_package_all_modules.py --all

# 打包所有模块（先编译为pyd）
python 打包/03_package_all_modules.py --all --compile

# 只打包消息服务端模块
python 打包/03_package_all_modules.py --module message

# 只打包消息服务端模块（先编译为pyd）
python 打包/03_package_all_modules.py --module message --compile
```

### 使用批处理脚本

```bash
# Windows 批处理脚本
打包\package_all_modules.bat
```

### 一键打包

```bash
cd message_server
build_message_server_complete.bat
```

## 🔗 相关模块

- [主功能模块](../主功能模块/) - 主功能模块
- [授权管理模块](../授权管理模块/) - 授权管理模块
- [测试代码](../测试代码/) - 测试代码目录

---

**版本**: 1.0.0  
**更新日期**: 2026-06-12  
**维护者**: FileTidy 项目组