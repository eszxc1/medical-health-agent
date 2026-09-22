<template>
  <div class="login-container">
    <!-- yllwyw 新增：参考主页面风格的登录布局 -->
    <section class="login-shell">
      <aside class="login-brand-panel">
        <div class="brand-mark"><span class="brand-icon">💬</span><span class="brand-name">AI 助手</span></div>
        <div class="brand-content">
          <span class="brand-label">智能医疗问答</span>
          <h1>欢迎回来</h1>
          <p>登录后继续查看历史对话，并使用 AI 助手获取帮助。</p>
        </div>
        <div class="brand-status"><span class="status-dot"></span><span>服务正常运行</span></div>
      </aside>

      <main class="login-main">
        <div class="mobile-brand"><span class="brand-icon">💬</span><span class="brand-name">AI 助手</span></div>
        <div class="login-form-wrap">
          <div class="login-heading">
            <span class="heading-icon"><i class="el-icon-user"></i></span>
            <div><h2 class="login-title">账号登录</h2><p>使用邮箱验证码安全登录</p></div>
          </div>

          <form @submit.prevent>
            <label class="form-label" for="login-username">用户名</label>
            <div class="form-group input-with-icon">
              <i class="el-icon-user input-icon"></i>
              <input id="login-username" type="text" placeholder="请输入用户名" v-model="username" :disabled="isSend" class="form-input" autocomplete="username">
            </div>

            <template v-if="isSend">
              <div class="code-label-row">
                <label class="form-label" for="login-code">验证码</label>
                <span class="countdown-text">{{ countdown > 0 ? `${countdown}s 后可重新发送` : '' }}</span>
              </div>
              <div class="form-group input-with-icon">
                <i class="el-icon-key input-icon"></i>
                <input id="login-code" type="text" placeholder="请输入邮箱验证码" v-model="code" class="form-input" autocomplete="one-time-code" @keyup.enter="verifyCode">
              </div>
            </template>

            <button type="button" v-if="!isSend" @click="sendEmail" class="form-btn primary-btn" :disabled="!username.trim()">
              <span>发送验证码</span><i class="el-icon-right"></i>
            </button>
            <button type="button" v-else @click="verifyCode" class="form-btn primary-btn" :disabled="!code.trim()">
              <span>验证并登录</span><i class="el-icon-right"></i>
            </button>

            <div class="register-link">
              <span class="register-text">还没有账号？</span>
              <button type="button" @click="goToRegister" class="register-btn">立即注册</button>
            </div>
          </form>
        </div>
      </main>
    </section>
    <!-- yllwyw 新增结束 -->
  </div>
</template>

<script>
export default {
  name: "Login",
  data() {
    return {
      username: '',
      receiver: '',
      code: '',
      isSend: false,
      countdown: 0,
      timer: null
    }
  },
  methods: {
    sendEmail() { // 发送验证码
      this.$message.closeAll();
      this.isSend = true;
      this.startCountdown();
      this.$axios({
        url: 'users/sendEmail',
        method: 'get',
        params: {
          username: this.username,
        }
      }).then(res => {
        let code = res.data.code;
        let data = res.data.data;
        if (code == 200) {
          this.$message.success('发送成功！');
          this.receiver = data;
        } else {
          // ★ 修复：显示后端返回的具体错误原因，而非硬编码的"发送失败"
          let errMsg = res.data.msg || '发送失败！';
          this.$message.error(errMsg);
          clearInterval(this.timer);
          this.timer = null;
          this.isSend = false;
          this.countdown = 0;
        }
      });
    },
    verifyCode() { // 验证验证码
      this.$axios({
        url: 'users/verifyCode',
        method: 'get',
        params: {
          receiver: this.receiver,
          code: this.code
        }
      }).then(res => {
        if (res.data.code == 200) {
          this.$message.success('登录成功！');
          sessionStorage.setItem('username', this.username);
          sessionStorage.setItem('email', this.receiver);
          setTimeout(() => {
            this.$router.push('/chat').catch(err => {
              if (err.name !== 'NavigationDuplicated') {
                console.error(err);
              }
            });
          }, 1500);
        } else {
          this.$message.error(res.data.msg || '登录失败！');
        }
      })
    },
    startCountdown() {
      this.countdown = 60;
      this.timer = setInterval(() => {
        this.countdown -= 1;
        if (this.countdown <= 0) {
          clearInterval(this.timer);
          this.timer = null;
          this.isSend = false;
        }
      }, 1000);
    },
    goToRegister(){
      this.$router.push('/register').catch(err => {
        if (err.name !== 'NavigationDuplicated') {
          console.error(err);
        }
      });
    }
  },
  beforeDestroy() {
    if (this.timer) clearInterval(this.timer);
  }
}
</script>



<style scoped>
/* 整体居中背景 */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #84A98C 0%, #6B8F73 100%);
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

/* 登录卡片 */
.login-card {
  background: #ffffff;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 400px;
  box-sizing: border-box;
}

.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.verify-btn.is-disabled {
  background-color: #e0e0e0;
  color: #999;
  cursor: not-allowed;
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

/* 表单组 */
.form-group {
  margin-bottom: 20px;
}

.form-input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
  box-sizing: border-box; /* 防止输入框撑破卡片 */
}

.form-input:focus {
  border-color: #84A98C;
  box-shadow: 0 0 0 3px rgba(132, 169, 140, 0.2);
}

.form-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

/* 按钮样式 */
.form-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.1s;
}

.primary-btn {
  background-color: #84A98C;
  color: #fff;
}

.primary-btn:hover {
  background-color: #6B8F73;
}

.primary-btn:active {
  transform: scale(0.98);
}

/* 验证按钮与倒计时布局 */
.verify-action {
  display: flex;
  align-items: center;
  gap: 10px;
}

.verify-btn {
  flex: 1;
}

.countdown-text {
  font-size: 12px;
  color: #888;
  white-space: nowrap;
  min-width: 90px;
}

/* ==========================================
   方案一：注册区域美化样式 (现代简约风)
   ========================================== */
.register-link {
  display: flex;
  justify-content: space-between; /* 两端对齐 */
  align-items: center;
  margin-top: 25px;
  padding-top: 20px;
  border-top: 1px dashed #eee; /* 增加虚线分割线提升层次感 */
}

.register-text {
  font-size: 14px;
  color: #666;
}

.register-btn {
  background: none;
  border: none;
  color: #84A98C; /* 使用与主色调一致的颜色 */
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  transition: all 0.3s ease;
}

.register-btn:hover {
  color: #6B8F73;
  text-decoration: underline; /* 鼠标悬停时显示下划线 */
}

/* yllwyw 新增：登录页视觉样式 */
.login-container {
  padding: 32px;
  box-sizing: border-box;
  background: #f6f7fb;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.login-shell {
  width: min(940px, 100%);
  min-height: 580px;
  display: grid;
  grid-template-columns: 38% 62%;
  overflow: hidden;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 20px 60px rgba(37, 48, 82, 0.12);
}

.login-brand-panel {
  display: flex;
  flex-direction: column;
  padding: 38px 34px;
  color: #3D4A3E;
  background: linear-gradient(180deg, #F1F6F1 0%, #E3EDE4 100%);
  border-right: 1px solid rgba(132, 169, 140, 0.12);
}

.brand-mark, .mobile-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #fff;
  font-size: 22px;
  background: linear-gradient(135deg, #A8C3A8, #84A98C);
  box-shadow: 0 8px 20px rgba(132, 169, 140, 0.22);
}

.brand-name {
  color: #84A98C;
  font-size: 22px;
  font-weight: 700;
}

.brand-content { margin: auto 0; }
.brand-label {
  display: inline-block;
  margin-bottom: 16px;
  padding: 6px 10px;
  border: 1px solid rgba(132, 169, 140, 0.18);
  border-radius: 6px;
  color: #6B8F73;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.62);
}

.brand-content h1 { margin: 0 0 14px; color: #3D4A3E; font-size: 34px; line-height: 1.2; }
.brand-content p { margin: 0; color: rgba(90, 61, 74, 0.65); font-size: 14px; line-height: 1.8; }
.brand-status { display: flex; align-items: center; gap: 8px; color: rgba(90, 61, 74, 0.55); font-size: 12px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #41b883; box-shadow: 0 0 0 4px rgba(65, 184, 131, 0.12); }

.login-main {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 56px 72px;
  box-sizing: border-box;
  background: #fff;
}

.mobile-brand { display: none; }
.login-form-wrap { width: 100%; max-width: 390px; }
.login-heading { display: flex; align-items: center; gap: 14px; margin-bottom: 34px; }
.heading-icon { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 8px; color: #84A98C; font-size: 20px; background: #f0f2ff; }
.login-title { margin: 0 0 5px; text-align: left; color: #20253a; font-size: 24px; font-weight: 700; }
.login-heading p { margin: 0; color: #9aa0b2; font-size: 13px; }
.form-label { display: block; margin-bottom: 8px; color: #4b5168; font-size: 13px; font-weight: 600; }
.form-group { margin-bottom: 22px; }
.input-with-icon { position: relative; }
.input-icon { position: absolute; left: 14px; top: 50%; z-index: 1; transform: translateY(-50%); color: #a7adbd; font-size: 16px; }
.form-input { height: 46px; padding: 0 14px 0 42px; border-color: #dfe3ec; color: #292e42; background: #fafbfc; transition: border-color 0.2s, box-shadow 0.2s, background 0.2s; }
.form-input:focus { background: #fff; box-shadow: 0 0 0 3px rgba(132, 169, 140, 0.1); }
.code-label-row { display: flex; align-items: center; justify-content: space-between; }
.countdown-text { min-width: 0; color: #84A98C; }
.form-btn { height: 46px; display: flex; align-items: center; justify-content: center; gap: 10px; padding: 0; font-size: 14px; font-weight: 600; transition: transform 0.2s, box-shadow 0.2s, opacity 0.2s; }
.primary-btn { background: linear-gradient(135deg, #84A98C, #6B8F73); box-shadow: 0 8px 20px rgba(132, 169, 140, 0.22); }
.primary-btn:hover:not(:disabled) { transform: translateY(-1px); background: linear-gradient(135deg, #84A98C, #6B8F73); box-shadow: 0 10px 24px rgba(132, 169, 140, 0.3); }
.form-btn:disabled { opacity: 0.45; cursor: not-allowed; box-shadow: none; }
.register-link { justify-content: center; gap: 5px; margin-top: 28px; padding-top: 22px; border-top: 1px solid #eef0f5; }
.register-text, .register-btn { font-size: 13px; }
.register-text { color: #8b91a3; }
.register-btn:hover { color: #84A98C; text-decoration: none; }

@media (max-width: 760px) {
  .login-container { padding: 18px; }
  .login-shell { min-height: auto; display: block; }
  .login-brand-panel { display: none; }
  .login-main { display: block; padding: 26px 24px 34px; }
  .mobile-brand { display: flex; margin-bottom: 42px; }
  .brand-icon { width: 38px; height: 38px; font-size: 18px; }
  .brand-name { font-size: 19px; }
  .login-heading { margin-bottom: 28px; }
}
/* yllwyw 新增结束 */
</style>
