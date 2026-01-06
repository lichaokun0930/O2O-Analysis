/**
 * API 请求封装
 * 统一处理请求拦截、响应拦截、错误处理
 */
import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // 增加超时时间到60秒
  headers: {
    'Content-Type': 'application/json'
  }
})

// 错误消息节流 - 防止重复弹出
let lastErrorTime = 0
const ERROR_THROTTLE_MS = 3000 // 3秒内不重复显示同类错误

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 添加认证 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    let message = '请求失败'
    
    if (error.response) {
      switch (error.response.status) {
        case 400:
          message = error.response.data?.detail || '请求参数错误'
          break
        case 401:
          message = '未授权，请重新登录'
          // 可以在这里处理登出逻辑
          break
        case 403:
          message = '拒绝访问'
          break
        case 404:
          message = '请求地址不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = error.response.data?.detail || '请求失败'
      }
    } else if (error.message.includes('timeout')) {
      message = '请求超时，请稍后重试'
    } else if (error.message.includes('Network Error')) {
      message = '网络错误，请检查网络连接'
    }
    
    // 节流显示错误消息
    const now = Date.now()
    if (now - lastErrorTime > ERROR_THROTTLE_MS) {
      lastErrorTime = now
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

// 通用请求方法
export const request = {
  get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, config)
  },
  
  post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config)
  },
  
  put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return service.put(url, data, config)
  },
  
  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.delete(url, config)
  }
}

export default service

