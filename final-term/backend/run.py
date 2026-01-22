from app import create_app
import os
import logging

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # 配置日志：减少访问日志输出（只输出错误）
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # 只显示ERROR级别以上的日志
    
    app.run(host='0.0.0.0', port=port, debug=True)

