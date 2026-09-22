import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

export default new Router({
  // 把history改成hash，本地刷新不会404
  mode: 'hash',
  routes: [
    {
      path: '/',
      component: () => import('@/views/Login.vue')
    },
    {
      path: '/chat',
      component: () => import('@/views/Chat.vue')
    },
    // ★ 新增注册路由
    {
      path: '/register',
      component: () => import('@/views/Register.vue')
    }
  ]
})
