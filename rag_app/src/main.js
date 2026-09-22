// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'

// 引入 markdown-it
import MarkdownIt from 'markdown-it'

Vue.use(ElementUI)
Vue.config.productionTip = false

// 引入axios
import axios from 'axios'
axios.defaults.baseURL = 'http://localhost:8000/'
// 设置post请求数据格式
axios.defaults.headers.post['Content-Type'] = 'application/json'
// 设置put请求数据格式
axios.defaults.headers.put['Content-Type'] = 'application/json'
// 设置全局 axios 写法
Vue.prototype.$axios = axios

// ===== 配置 markdown-it =====
// 1. 创建 markdown-it 实例
const md = new MarkdownIt({
  html: false,      // 安全起见，不允许 HTML 标签
  breaks: true,     // 将换行符转换为 <br>
  linkify: true,    // 自动识别并转换 URL 为链接
  typographer: true // 启用一些语言中性的排版替换
})

// 2. 挂载到 Vue 原型上，方便全局使用
Vue.prototype.$md = md

// 3. 注册全局过滤器
Vue.filter('markdown', function(content) {
  if (!content) return ''
  try {
    return md.render(content)
  } catch (error) {
    console.error('Markdown filter error:', error)
    return content
  }
})

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>'
})
