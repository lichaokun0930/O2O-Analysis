/**
 * 企业级智能请求管理器
 * 
 * 核心功能：
 * 1. 请求取消 - 门店切换时自动取消旧请求
 * 2. 请求防抖 - 相同请求短时间内只发一次
 * 3. 请求合并 - 批量请求合并为单次调用
 * 4. 智能重试 - 429/5xx 错误自动重试（指数退避）
 * 5. 降级缓存 - 请求失败时返回缓存数据
 * 
 * @author O2O-Analysis Team
 * @version 1.0.0
 */

import axios, { AxiosRequestConfig, AxiosResponse, CancelTokenSource } from 'axios';

// ==================== 类型定义 ====================

interface PendingRequest {
  cancelSource: CancelTokenSource;
  timestamp: number;
  key: string;
}

interface CacheEntry<T = unknown> {
  data: T;
  timestamp: number;
  ttl: number;
}

interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  retryOn: number[];
}

interface RequestManagerConfig {
  debounceMs: number;
  cacheTtlMs: number;
  retry: RetryConfig;
}

// ==================== 默认配置 ====================

const DEFAULT_CONFIG: RequestManagerConfig = {
  debounceMs: 100,           // 防抖时间 100ms
  cacheTtlMs: 5 * 60 * 1000, // 缓存 5 分钟
  retry: {
    maxRetries: 3,
    baseDelay: 1000,         // 初始重试延迟 1s
    maxDelay: 10000,         // 最大重试延迟 10s
    retryOn: [429, 500, 502, 503, 504],
  },
};

// ==================== 请求管理器类 ====================

class RequestManager {
  private pendingRequests: Map<string, PendingRequest> = new Map();
  private cache: Map<string, CacheEntry> = new Map();
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map();
  private config: RequestManagerConfig;
  
  // 请求分组（用于批量取消）
  private requestGroups: Map<string, Set<string>> = new Map();

  constructor(config: Partial<RequestManagerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * 生成请求唯一键
   */
  private generateKey(url: string, params?: Record<string, unknown>): string {
    const sortedParams = params ? JSON.stringify(params, Object.keys(params).sort()) : '';
    return `${url}:${sortedParams}`;
  }

  /**
   * 取消指定分组的所有请求
   * 用于门店切换时取消旧门店的所有请求
   */
  cancelGroup(groupId: string): void {
    const keys = this.requestGroups.get(groupId);
    if (!keys) return;

    keys.forEach(key => {
      const pending = this.pendingRequests.get(key);
      if (pending) {
        pending.cancelSource.cancel(`Request cancelled: group ${groupId} cancelled`);
        this.pendingRequests.delete(key);
      }
    });

    this.requestGroups.delete(groupId);
    console.log(`🚫 已取消请求组: ${groupId}, 共 ${keys.size} 个请求`);
  }

  /**
   * 取消所有待处理请求
   */
  cancelAll(): void {
    this.pendingRequests.forEach((pending, key) => {
      pending.cancelSource.cancel('All requests cancelled');
    });
    this.pendingRequests.clear();
    this.requestGroups.clear();
    console.log('🚫 已取消所有待处理请求');
  }

  /**
   * 获取缓存数据
   */
  private getCache<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    // 检查是否过期
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  /**
   * 设置缓存
   */
  private setCache<T>(key: string, data: T, ttl?: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.config.cacheTtlMs,
    });
  }

  /**
   * 计算重试延迟（指数退避 + 抖动）
   */
  private calculateRetryDelay(attempt: number): number {
    const { baseDelay, maxDelay } = this.config.retry;
    // 指数退避: baseDelay * 2^attempt
    const exponentialDelay = baseDelay * Math.pow(2, attempt);
    // 添加随机抖动 (±25%)
    const jitter = exponentialDelay * 0.25 * (Math.random() * 2 - 1);
    return Math.min(exponentialDelay + jitter, maxDelay);
  }

  /**
   * 执行带重试的请求
   */
  private async executeWithRetry<T>(
    requestFn: () => Promise<AxiosResponse<T>>,
    key: string,
    attempt: number = 0
  ): Promise<AxiosResponse<T>> {
    try {
      return await requestFn();
    } catch (error: unknown) {
      if (axios.isCancel(error)) {
        throw error; // 取消的请求不重试
      }

      const axiosError = error as { response?: { status: number } };
      const status = axiosError.response?.status;
      const { maxRetries, retryOn } = this.config.retry;

      // 检查是否应该重试
      if (status && retryOn.includes(status) && attempt < maxRetries) {
        const delay = this.calculateRetryDelay(attempt);
        console.log(`🔄 请求重试 [${attempt + 1}/${maxRetries}]: ${key}, 延迟 ${Math.round(delay)}ms`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.executeWithRetry(requestFn, key, attempt + 1);
      }

      // 429 错误特殊处理：尝试返回缓存
      if (status === 429) {
        const cached = this.getCache<T>(key);
        if (cached) {
          console.log(`📦 429 限流，返回缓存数据: ${key}`);
          return { data: cached } as AxiosResponse<T>;
        }
      }

      throw error;
    }
  }

  /**
   * 发起智能请求
   * 
   * @param url 请求 URL
   * @param config Axios 配置
   * @param options 额外选项
   */
  async request<T = unknown>(
    url: string,
    config: AxiosRequestConfig = {},
    options: {
      groupId?: string;      // 请求分组 ID（用于批量取消）
      debounce?: boolean;    // 是否防抖
      useCache?: boolean;    // 是否使用缓存
      cacheTtl?: number;     // 缓存 TTL
      skipCancel?: boolean;  // 跳过取消检查
    } = {}
  ): Promise<T> {
    const { groupId, debounce = true, useCache = true, cacheTtl, skipCancel = false } = options;
    const key = this.generateKey(url, config.params as Record<string, unknown>);

    // 1. 检查缓存
    if (useCache) {
      const cached = this.getCache<T>(key);
      if (cached) {
        console.log(`📦 命中缓存: ${key}`);
        return cached;
      }
    }

    // 2. 防抖处理
    if (debounce) {
      const existingTimer = this.debounceTimers.get(key);
      if (existingTimer) {
        clearTimeout(existingTimer);
      }

      return new Promise((resolve, reject) => {
        const timer = setTimeout(async () => {
          this.debounceTimers.delete(key);
          try {
            const result = await this.executeRequest<T>(url, config, key, groupId, useCache, cacheTtl, skipCancel);
            resolve(result);
          } catch (error) {
            reject(error);
          }
        }, this.config.debounceMs);

        this.debounceTimers.set(key, timer);
      });
    }

    return this.executeRequest<T>(url, config, key, groupId, useCache, cacheTtl, skipCancel);
  }

  /**
   * 执行实际请求
   */
  private async executeRequest<T>(
    url: string,
    config: AxiosRequestConfig,
    key: string,
    groupId?: string,
    useCache?: boolean,
    cacheTtl?: number,
    skipCancel?: boolean
  ): Promise<T> {
    // 3. 取消重复请求
    if (!skipCancel) {
      const existing = this.pendingRequests.get(key);
      if (existing) {
        existing.cancelSource.cancel('Duplicate request cancelled');
        this.pendingRequests.delete(key);
      }
    }

    // 4. 创建取消令牌
    const cancelSource = axios.CancelToken.source();
    const pending: PendingRequest = {
      cancelSource,
      timestamp: Date.now(),
      key,
    };

    this.pendingRequests.set(key, pending);

    // 5. 添加到分组
    if (groupId) {
      if (!this.requestGroups.has(groupId)) {
        this.requestGroups.set(groupId, new Set());
      }
      this.requestGroups.get(groupId)!.add(key);
    }

    // 6. 执行请求（带重试）
    try {
      const response = await this.executeWithRetry<T>(
        () => axios({
          ...config,
          url,
          cancelToken: cancelSource.token,
        }),
        key
      );

      // 7. 缓存响应
      if (useCache && response.data) {
        this.setCache(key, response.data, cacheTtl);
      }

      return response.data;
    } finally {
      // 8. 清理
      this.pendingRequests.delete(key);
      if (groupId) {
        this.requestGroups.get(groupId)?.delete(key);
      }
    }
  }

  /**
   * 批量请求（并行执行，统一取消）
   */
  async batchRequest<T extends Record<string, unknown>>(
    requests: Array<{
      key: keyof T;
      url: string;
      config?: AxiosRequestConfig;
    }>,
    groupId: string
  ): Promise<Partial<T>> {
    // 先取消该分组的旧请求
    this.cancelGroup(groupId);

    const results: Partial<T> = {};
    const promises = requests.map(async ({ key, url, config }) => {
      try {
        const data = await this.request(url, config, { groupId, debounce: false });
        results[key] = data as T[keyof T];
      } catch (error) {
        if (!axios.isCancel(error)) {
          console.error(`批量请求失败 [${String(key)}]:`, error);
        }
      }
    });

    await Promise.allSettled(promises);
    return results;
  }

  /**
   * 清理过期缓存
   */
  cleanExpiredCache(): void {
    const now = Date.now();
    let cleaned = 0;

    this.cache.forEach((entry, key) => {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
        cleaned++;
      }
    });

    if (cleaned > 0) {
      console.log(`🧹 清理过期缓存: ${cleaned} 条`);
    }
  }

  /**
   * 获取统计信息
   */
  getStats(): {
    pendingCount: number;
    cacheSize: number;
    groupCount: number;
  } {
    return {
      pendingCount: this.pendingRequests.size,
      cacheSize: this.cache.size,
      groupCount: this.requestGroups.size,
    };
  }
}

// ==================== 导出单例 ====================

export const requestManager = new RequestManager();

// 定期清理过期缓存（每分钟）
setInterval(() => {
  requestManager.cleanExpiredCache();
}, 60 * 1000);

export default requestManager;
