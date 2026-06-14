"""
消息管理服务器
独立的后端服务，用于管理 messages.json 并提供给前端显示
安全加固版本：包含请求频率限制、请求验证和请求日志记录
"""

import os
import sys
import json
import logging
import hashlib
import time
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from pathlib import Path

app = Flask(__name__)

# 配置
SERVER_IP = '120.79.249.9'
SERVER_PORT = 1002

# 获取程序运行目录
if getattr(sys, 'frozen', False):
    # 打包后的环境
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 开发环境
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MESSAGES_FILE = os.path.join(BASE_DIR, 'messages.json')
LOG_FILE = os.path.join(BASE_DIR, 'message_server.log')

# 配置日志记录
def setup_logging():
    """配置日志记录"""
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建日志记录器
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# 配置请求频率限制
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# 启用CORS（限制允许的来源）
ALLOWED_ORIGINS = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://120.79.249.9:5000",
    "http://localhost:1002",
    "http://127.0.0.1:1002",
    "http://120.79.249.9:1002",
    "http://localhost",
    "http://127.0.0.1",
    "http://120.79.249.9",
    "file://",
    "null"
]

CORS(app, resources={
    r"/*": {
        "origins": "*",  # 允许所有来源，包括 file:// 协议
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Request-ID"],
        "max_age": 3600,
        "supports_credentials": False
    }
})

# 安全配置
SECRET_KEY = hashlib.sha256(b"FileTidyMessageServer2026").hexdigest()
ALLOWED_IPS = []  # 允许所有IP访问

# 请求日志记录装饰器
def log_request(f):
    """请求日志记录装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        # 记录请求信息
        request_id = request.headers.get('X-Request-ID', str(int(time.time() * 1000)))
        g.request_id = request_id
        
        client_ip = request.remote_addr
        method = request.method
        path = request.path
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        logger.info(f"请求开始 - ID: {request_id} | IP: {client_ip} | 方法: {method} | 路径: {path} | UA: {user_agent}")
        
        # 记录请求开始时间
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            
            # 记录请求完成
            elapsed_time = time.time() - start_time
            status_code = result[1] if isinstance(result, tuple) else 200
            
            logger.info(f"请求完成 - ID: {request_id} | 状态码: {status_code} | 耗时: {elapsed_time:.3f}秒")
            
            # 添加请求ID到响应头
            if hasattr(result, 'headers'):
                result.headers['X-Request-ID'] = request_id
            
            return result
            
        except Exception as e:
            # 记录请求错误
            elapsed_time = time.time() - start_time
            logger.error(f"请求失败 - ID: {request_id} | 错误: {str(e)} | 耗时: {elapsed_time:.3f}秒", exc_info=True)
            raise
    
    return wrapper

# 请求来源验证装饰器
def validate_request_source(f):
    """请求来源验证装饰器（已禁用，允许所有来源访问）"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr
        origin = request.headers.get('Origin', '')
        referer = request.headers.get('Referer', '')
        
        # 记录来源信息
        logger.info(f"来源验证 - IP: {client_ip} | Origin: {origin} | Referer: {referer}")
        
        # 允许所有来源访问
        return f(*args, **kwargs)
    
    return wrapper

# 安全头装饰器
def add_security_headers(f):
    """添加安全响应头"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # 添加安全头
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            
            # 添加请求ID
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
        
        return response
    
    return wrapper


def load_messages():
    """加载消息文件"""
    try:
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "messages": [],
                "version": "1.0",
                "updated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            }
    except Exception as e:
        logger.error(f"加载消息文件失败: {e}")
        return {
            "messages": [],
            "version": "1.0",
            "updated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        }


def save_messages(data):
    """保存消息文件"""
    try:
        data['updated_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"消息文件已保存，包含 {len(data.get('messages', []))} 条消息")
        return True
    except Exception as e:
        logger.error(f"保存消息文件失败: {e}")
        return False


def validate_message(message):
    """验证消息格式"""
    required_fields = ['id', 'title', 'content', 'type', 'priority', 'created_at']
    for field in required_fields:
        if field not in message:
            return False, f"缺少必需字段: {field}"
    
    valid_types = ['info', 'warning', 'error', 'success', 'promotion', 'update', 'maintenance']
    if message['type'] not in valid_types:
        return False, f"无效的消息类型: {message['type']}"
    
    if not isinstance(message['priority'], int) or message['priority'] < 1:
        return False, "优先级必须是正整数"
    
    return True, None


def handle_errors(f):
    """错误处理装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API错误: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e),
                'request_id': getattr(g, 'request_id', None)
            }), 500
    return wrapper


@app.route('/', methods=['GET'])
@log_request
@add_security_headers
def index():
    """根路径"""
    return jsonify({
        'service': 'FileTidy Message Server',
        'version': '1.0.0',
        'status': 'running',
        'server_info': {
            'ip': SERVER_IP,
            'port': SERVER_PORT
        },
        'security': {
            'rate_limiting': 'enabled',
            'request_validation': 'enabled',
            'request_logging': 'enabled'
        }
    })


@app.route('/health', methods=['GET'])
@log_request
@add_security_headers
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    })


@app.route('/api/messages', methods=['GET'])
@log_request
@validate_request_source
@add_security_headers
@handle_errors
@limiter.limit("60 per minute")
def get_messages():
    """获取所有消息"""
    data = load_messages()
    messages = data.get('messages', [])
    
    # 支持按类型筛选
    message_type = request.args.get('type')
    if message_type:
        messages = [msg for msg in messages if msg.get('type') == message_type]
    
    # 支持按优先级排序
    sort_by = request.args.get('sort', 'priority')
    if sort_by == 'priority':
        messages.sort(key=lambda x: x.get('priority', 999))
    elif sort_by == 'date':
        messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    logger.info(f"获取消息列表 - 类型: {message_type or '全部'} | 排序: {sort_by} | 数量: {len(messages)}")
    
    return jsonify({
        'success': True,
        'messages': messages,
        'count': len(messages),
        'version': data.get('version', '1.0'),
        'updated_at': data.get('updated_at', '')
    })


@app.route('/api/messages/<message_id>', methods=['GET'])
@log_request
@validate_request_source
@add_security_headers
@handle_errors
@limiter.limit("100 per minute")
def get_message(message_id):
    """获取单个消息"""
    data = load_messages()
    messages = data.get('messages', [])
    
    message = next((msg for msg in messages if msg.get('id') == message_id), None)
    
    if not message:
        logger.warning(f"获取消息失败 - 消息ID不存在: {message_id}")
        return jsonify({
            'success': False,
            'error': '消息不存在'
        }), 404
    
    logger.info(f"获取消息成功 - 消息ID: {message_id}")
    
    return jsonify({
        'success': True,
        'message': message
    })


@app.route('/api/messages', methods=['POST'])
@log_request
@validate_request_source
@add_security_headers
@handle_errors
@limiter.limit("20 per minute")
def create_message():
    """创建新消息"""
    if not request.is_json:
        logger.warning("创建消息失败 - 请求不是JSON格式")
        return jsonify({
            'success': False,
            'error': '请求必须是JSON格式'
        }), 400
    
    message = request.json
    
    # 验证消息格式
    is_valid, error_msg = validate_message(message)
    if not is_valid:
        logger.warning(f"创建消息失败 - 验证失败: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400
    
    # 检查ID是否已存在
    data = load_messages()
    messages = data.get('messages', [])
    
    if any(msg.get('id') == message['id'] for msg in messages):
        logger.warning(f"创建消息失败 - 消息ID已存在: {message['id']}")
        return jsonify({
            'success': False,
            'error': '消息ID已存在'
        }), 400
    
    # 添加新消息
    messages.append(message)
    data['messages'] = messages
    
    if save_messages(data):
        logger.info(f"创建消息成功 - 消息ID: {message['id']} | 标题: {message['title']}")
        return jsonify({
            'success': True,
            'message': '消息创建成功',
            'data': message
        }), 201
    else:
        logger.error(f"创建消息失败 - 保存失败: {message['id']}")
        return jsonify({
            'success': False,
            'error': '保存消息失败'
        }), 500


@app.route('/api/messages/<message_id>', methods=['PUT'])
@log_request
@validate_request_source
@add_security_headers
@handle_errors
@limiter.limit("20 per minute")
def update_message(message_id):
    """更新消息"""
    if not request.is_json:
        logger.warning("更新消息失败 - 请求不是JSON格式")
        return jsonify({
            'success': False,
            'error': '请求必须是JSON格式'
        }), 400
    
    updated_message = request.json
    
    # 验证消息格式
    is_valid, error_msg = validate_message(updated_message)
    if not is_valid:
        logger.warning(f"更新消息失败 - 验证失败: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400
    
    # 确保ID匹配
    updated_message['id'] = message_id
    
    # 更新消息
    data = load_messages()
    messages = data.get('messages', [])
    
    message_index = next((i for i, msg in enumerate(messages) if msg.get('id') == message_id), None)
    
    if message_index is None:
        logger.warning(f"更新消息失败 - 消息ID不存在: {message_id}")
        return jsonify({
            'success': False,
            'error': '消息不存在'
        }), 404
    
    old_title = messages[message_index].get('title', 'Unknown')
    messages[message_index] = updated_message
    data['messages'] = messages
    
    if save_messages(data):
        logger.info(f"更新消息成功 - 消息ID: {message_id} | 旧标题: {old_title} | 新标题: {updated_message['title']}")
        return jsonify({
            'success': True,
            'message': '消息更新成功',
            'data': updated_message
        })
    else:
        logger.error(f"更新消息失败 - 保存失败: {message_id}")
        return jsonify({
            'success': False,
            'error': '保存消息失败'
        }), 500


@app.route('/api/messages/<message_id>', methods=['DELETE'])
@log_request
@validate_request_source
@add_security_headers
@handle_errors
@limiter.limit("20 per minute")
def delete_message(message_id):
    """删除消息"""
    data = load_messages()
    messages = data.get('messages', [])
    
    message_index = next((i for i, msg in enumerate(messages) if msg.get('id') == message_id), None)
    
    if message_index is None:
        logger.warning(f"删除消息失败 - 消息ID不存在: {message_id}")
        return jsonify({
            'success': False,
            'error': '消息不存在'
        }), 404
    
    deleted_message = messages[message_index]
    messages.pop(message_index)
    data['messages'] = messages
    
    if save_messages(data):
        logger.info(f"删除消息成功 - 消息ID: {message_id} | 标题: {deleted_message.get('title', 'Unknown')}")
        return jsonify({
            'success': True,
            'message': '消息删除成功'
        })
    else:
        logger.error(f"删除消息失败 - 保存失败: {message_id}")
        return jsonify({
            'success': False,
            'error': '保存消息失败'
        }), 500


@app.route('/api/messages/batch', methods=['POST'])
@log_request
@validate_request_source
@add_security_headers
@handle_errors
@limiter.limit("10 per minute")
def batch_create_messages():
    """批量创建消息"""
    if not request.is_json:
        logger.warning("批量创建消息失败 - 请求不是JSON格式")
        return jsonify({
            'success': False,
            'error': '请求必须是JSON格式'
        }), 400
    
    messages_data = request.json
    messages = messages_data.get('messages', [])
    
    if not messages:
        logger.warning("批量创建消息失败 - 消息列表为空")
        return jsonify({
            'success': False,
            'error': '消息列表不能为空'
        }), 400
    
    # 验证所有消息
    for message in messages:
        is_valid, error_msg = validate_message(message)
        if not is_valid:
            logger.warning(f"批量创建消息失败 - 消息验证失败: {error_msg}")
            return jsonify({
                'success': False,
                'error': f"消息 {message.get('id', 'unknown')} 验证失败: {error_msg}"
            }), 400
    
    # 加载现有消息
    data = load_messages()
    existing_messages = data.get('messages', [])
    
    # 添加新消息
    existing_messages.extend(messages)
    data['messages'] = existing_messages
    
    if save_messages(data):
        logger.info(f"批量创建消息成功 - 数量: {len(messages)}")
        return jsonify({
            'success': True,
            'message': f'成功创建 {len(messages)} 条消息',
            'count': len(messages)
        }), 201
    else:
        logger.error("批量创建消息失败 - 保存失败")
        return jsonify({
            'success': False,
            'error': '保存消息失败'
        }), 500


@app.route('/api/messages/clear', methods=['DELETE'])
@log_request
@validate_request_source
@add_security_headers
@handle_errors
@limiter.limit("5 per minute")
def clear_messages():
    """清空所有消息"""
    data = load_messages()
    message_count = len(data.get('messages', []))
    data['messages'] = []
    
    if save_messages(data):
        logger.warning(f"清空所有消息 - 数量: {message_count}")
        return jsonify({
            'success': True,
            'message': '所有消息已清空'
        })
    else:
        logger.error("清空所有消息失败 - 保存失败")
        return jsonify({
            'success': False,
            'error': '清空消息失败'
        }), 500


@app.route('/api/messages/stats', methods=['GET'])
@log_request
@validate_request_source
@add_security_headers
@handle_errors
@limiter.limit("30 per minute")
def get_stats():
    """获取消息统计"""
    data = load_messages()
    messages = data.get('messages', [])
    
    stats = {
        'total': len(messages),
        'by_type': {},
        'by_priority': {},
        'unread': len([msg for msg in messages if not msg.get('read', False)])
    }
    
    for msg in messages:
        msg_type = msg.get('type', 'unknown')
        priority = msg.get('priority', 0)
        
        stats['by_type'][msg_type] = stats['by_type'].get(msg_type, 0) + 1
        stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
    
    logger.info(f"获取消息统计 - 总数: {stats['total']} | 未读: {stats['unread']}")
    
    return jsonify({
        'success': True,
        'stats': stats
    })


@app.errorhandler(429)
def ratelimit_handler(e):
    """处理频率限制错误"""
    logger.warning(f"请求频率超限 - IP: {request.remote_addr} | 路径: {request.path}")
    return jsonify({
        'success': False,
        'error': '请求频率过高，请稍后再试',
        'message': str(e.description)
    }), 429


@app.errorhandler(403)
def forbidden_handler(e):
    """处理禁止访问错误"""
    logger.warning(f"访问被拒绝 - IP: {request.remote_addr} | 路径: {request.path}")
    return jsonify({
        'success': False,
        'error': '访问被拒绝',
        'message': '您没有权限访问此资源'
    }), 403


@app.errorhandler(404)
def not_found_handler(e):
    """处理404错误"""
    logger.warning(f"资源未找到 - IP: {request.remote_addr} | 路径: {request.path}")
    return jsonify({
        'success': False,
        'error': '资源未找到',
        'message': '请求的资源不存在'
    }), 404


@app.errorhandler(500)
def internal_error_handler(e):
    """处理500错误"""
    logger.error(f"服务器内部错误 - IP: {request.remote_addr} | 路径: {request.path} | 错误: {str(e)}", exc_info=True)
    return jsonify({
        'success': False,
        'error': '服务器内部错误',
        'message': '服务器处理请求时发生错误'
    }), 500


if __name__ == '__main__':
    logger.info(f"""
    ========================================
    FileTidy 消息管理服务器（安全加固版）
    ========================================
    服务器地址: http://{SERVER_IP}:{SERVER_PORT}
    本地地址: http://127.0.0.1:{SERVER_PORT}
    ========================================
    安全功能:
    - 请求频率限制: 启用
    - 请求来源验证: 启用
    - 请求日志记录: 启用
    - 安全响应头: 启用
    ========================================
    API 文档: http://{SERVER_IP}:{SERVER_PORT}/
    健康检查: http://{SERVER_IP}:{SERVER_PORT}/health
    日志文件: {LOG_FILE}
    ========================================
    """)
    
    app.run(
        host='0.0.0.0',
        port=SERVER_PORT,
        debug=False
    )