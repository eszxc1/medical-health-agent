<template>
  <div id="app">

    <router-view/>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
/* ===== 全局设计系统：治愈 + 专业（医疗产品） ===== */
:root {
  --color-primary: #84A98C;       /* 鼠尾草绿 */
  --color-primary-dark: #6B8F73;
  --color-primary-light: #A8C3A8;
  --color-secondary: #AEC4EB;     /* 雾霾蓝 */
  --color-bg: #F9F9F7;            /* 暖白背景 */
  --color-text: #3D4A3E;
  --color-text-secondary: #8A948B;
  --color-border: #E8ECE8;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-soft: 0 4px 20px rgba(132, 169, 140, 0.12);
  --shadow-hover: 0 8px 30px rgba(132, 169, 140, 0.18);
  --font-family: "HarmonyOS Sans", "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

html, body {
  font-family: var(--font-family);
  font-size: 16px;
  line-height: 1.6;
  color: var(--color-text);
  background: var(--color-bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 圆角与弥散阴影：按钮 / 输入框 / 卡片统一 */
.el-button {
  border-radius: var(--radius-md);
}
.el-input__inner {
  border-radius: var(--radius-sm);
}
.el-card {
  border: none;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
}

/* Element UI 主色覆盖为鼠尾草绿 */
.el-button--primary {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-soft);
}
.el-button--primary:hover,
.el-button--primary:focus {
  background-color: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}
</style>
