/**
 * API 基础配置
 */
import axios from 'axios';

// 根据环境选择API地址
// - 开发模式 (npm run dev)：使用相对路径，Vite 代理处理
// - 生产模式 (npm run preview)：直接连接后端
const isDev = import.meta.env.DEV;
const API_BASE_URL = isDev ? '/api/v1' : 'http://localhost:8080/api/v1';

console.log('API Base URL:', API_BASE_URL);

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,  // ✅ 增加到120秒，处理并发请求时需要更长时间
  headers: {
    'Content-Type': 'application/json',
  },
});

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.message, error.config?.url);
    return Promise.reject(error);
  }
);

// 兼容旧的 request 导出
export const request = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,  // ✅ 增加到120秒
  headers: {
    'Content-Type': 'application/json',
  },
});

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error.message, error.config?.url);
    return Promise.reject(error);
  }
);

export default request;

// 导出各模块 API
export { inventoryRiskApi } from './inventoryRisk';
export { categoryMatrixApi } from './categoryMatrix';
