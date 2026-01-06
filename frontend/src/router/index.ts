import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/today-must-do'
  },
  {
    path: '/today-must-do',
    name: 'TodayMustDo',
    component: () => import('@/views/TodayMustDo/index.vue'),
    meta: { title: '今日必做', icon: 'Notification' }
  },
  {
    path: '/order-overview',
    name: 'OrderOverview',
    component: () => import('@/views/OrderOverview.vue'),
    meta: { title: '订单数据概览', icon: 'DataLine' }
  },
  {
    path: '/product-analysis',
    name: 'ProductAnalysis',
    component: () => import('@/views/ProductAnalysis.vue'),
    meta: { title: '商品分析', icon: 'Goods' }
  },
  {
    path: '/scene-analysis',
    name: 'SceneAnalysis',
    component: () => import('@/views/SceneAnalysis.vue'),
    meta: { title: '时段场景分析', icon: 'Timer' }
  },
  {
    path: '/data-management',
    name: 'DataManagement',
    component: () => import('@/views/DataManagement.vue'),
    meta: { title: '数据管理', icon: 'FolderOpened' }
  },
  {
    path: '/system-monitor',
    name: 'SystemMonitor',
    component: () => import('@/views/SystemMonitor.vue'),
    meta: { title: '系统监控', icon: 'Monitor' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, _from, next) => {
  const title = to.meta.title as string
  document.title = title ? `${title} - 订单数据看板` : '订单数据看板'
  next()
})

export default router

