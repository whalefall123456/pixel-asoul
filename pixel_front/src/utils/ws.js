// WebSocket连接管理工具
class WSClient {
  constructor() {
    this.ws = null;
    this.listeners = {};
    this.reconnectInterval = 5000; // 5秒重连间隔
    this.maxReconnectAttempts = 5;
    this.reconnectAttempts = 0;
  }

  /**
   * 连接到WebSocket服务器
   * @param {string} url - WebSocket服务器地址
   */
  connect(url) {
    // 如果处于模拟模式，不实际连接
    this.ws = new WebSocket(url);
    
    this.ws.onopen = (event) => {
      console.log('WebSocket连接已建立');
      this.reconnectAttempts = 0; // 重置重连次数
      this.emit('open', event);
    };
    
    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        // 根据后端API调整消息类型映射
        if (message.type === "initial_canvas") {
          this.emit('initial_canvas', message.data);
        } else if (message.type === "pixel_update") {
          this.emit('pixel_update', message.data);
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error);
      }
    };
    
    this.ws.onclose = (event) => {
      console.log('WebSocket连接已关闭', event);
      this.emit('close', event);
      
      // 尝试重连
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        setTimeout(() => this.connect(url), this.reconnectInterval);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
      this.emit('error', error);
    };
  }

  /**
   * 发送消息到服务器
   * @param {string} type - 消息类型
   * @param {Object} data - 消息数据
   */
  send(type, data) {
    if (this.isMockMode) {
      // 在模拟模式下，直接处理消息
      switch (type) {
        case 'pixel_place':
          // 模拟服务器确认像素放置
          this.emit('pixel_update', data);
          break;
      }
      return;
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      let message = null;
      // 根据后端API调整发送消息格式
      if (type === 'pixel_place') {
        message = {
          type: "pixel_update",
          data: {
            x: data.x,
            y: data.y,
            color: data.color
          }
        };
      } else {
        message = { type, data };
      }
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket未连接，无法发送消息');
    }
  }

  /**
   * 添加事件监听器
   * @param {string} event - 事件类型
   * @param {Function} callback - 回调函数
   */
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  /**
   * 移除事件监听器
   * @param {string} event - 事件类型
   * @param {Function} callback - 回调函数
   */
  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  /**
   * 触发事件监听器
   * @param {string} event - 事件类型
   * @param {any} data - 数据
   */
  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  /**
   * 关闭WebSocket连接
   */
  close() {
    this.stopMockDrawing();
    
    if (this.isMockMode) {
      return;
    }
    
    if (this.ws) {
      this.ws.close();
    }
  }
}

// 导出单例实例
export default new WSClient();