<template>
  <div class="register-container">
    <section class="register-shell">
      <aside class="register-brand-panel">
        <div class="brand-mark"><span class="brand-icon">💬</span><span class="brand-name">AI 助手</span></div>
        <div class="brand-content">
          <span class="brand-label">智能医疗问答</span>
          <h1>创建账号</h1>
          <p>注册后即可使用 AI 医疗助手，随时随地获取专业的医疗知识问答服务。</p>
        </div>
        <div class="brand-status"><span class="status-dot"></span><span>服务正常运行</span></div>
      </aside>

      <main class="register-main">
        <div class="mobile-brand"><span class="brand-icon">💬</span><span class="brand-name">AI 助手</span></div>
        <div class="register-form-wrap">
          <div class="register-heading">
            <span class="heading-icon"><i class="el-icon-edit-outline"></i></span>
            <div><h2 class="register-title">用户注册</h2><p>填写信息创建新账号</p></div>
          </div>

          <form @submit.prevent>
            <label class="form-label" for="reg-username">用户名</label>
            <div class="form-group input-with-icon">
              <i class="el-icon-user input-icon"></i>
              <input id="reg-username" type="text" placeholder="请输入用户名" v-model="username" class="form-input" autocomplete="username">
            </div>

            <label class="form-label" for="reg-email">邮箱</label>
            <div class="form-group input-with-icon">
              <i class="el-icon-message input-icon"></i>
              <input id="reg-email" type="email" placeholder="请输入邮箱" v-model="email" class="form-input" autocomplete="email">
            </div>

            <button type="button" @click="handleRegister" class="form-btn primary-btn" :disabled="!username.trim() || !email.trim()">
              <span>注册</span><i class="el-icon-right"></i>
            </button>

            <div class="register-link">
              <span class="register-text">已有账号？</span>
              <button type="button" @click="goToLogin" class="register-btn">去登录</button>
            </div>
          </form>
        </div>
      </main>
    </section>
  </div>
</template>

<script>
export default {
  name: "Register",
  data() {
    return {
      username: '',
      email: ''
    }
  },
  methods: {
    handleRegister() {
      if (!this.username.trim()) {
        this.$message.warning('请输入用户名')
        return
      }
      if (!this.email.trim()) {
        this.$message.warning('请输入邮箱')
        return
      }

      this.$axios({
        url: 'users/register',
        method: 'post',
        params: {
          username: this.username,
          email: this.email
        }
      }).then(res => {
        if (res.data.code === 200) {
          this.$message.success('注册成功！')
          setTimeout(() => {
            this.$router.push('/').catch(err => {
              if (err.name !== 'NavigationDuplicated') {
                console.error(err);
              }
            });
          }, 1500)
        } else {
          this.$message.error(res.data.msg || '注册失败')
        }
      }).catch(() => {
        this.$message.error('注册失败，请稍后重试')
      })
    },
    goToLogin() {
      this.$router.push('/').catch(err => {
        if (err.name !== 'NavigationDuplicated') {
          console.error(err);
        }
      });
    }
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #84A98C 0%, #6B8F73 100%);
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  padding: 32px;
  box-sizing: border-box;
  background: #f6f7fb;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.register-shell {
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

.register-brand-panel {
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

.register-main {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 56px 72px;
  box-sizing: border-box;
  background: #fff;
}

.mobile-brand { display: none; }
.register-form-wrap { width: 100%; max-width: 390px; }
.register-heading { display: flex; align-items: center; gap: 14px; margin-bottom: 34px; }
.heading-icon { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 8px; color: #84A98C; font-size: 20px; background: #f0f2ff; }
.register-title { margin: 0 0 5px; text-align: left; color: #20253a; font-size: 24px; font-weight: 700; }
.register-heading p { margin: 0; color: #9aa0b2; font-size: 13px; }
.form-label { display: block; margin-bottom: 8px; color: #4b5168; font-size: 13px; font-weight: 600; }
.form-group { margin-bottom: 22px; }
.input-with-icon { position: relative; }
.input-icon { position: absolute; left: 14px; top: 50%; z-index: 1; transform: translateY(-50%); color: #a7adbd; font-size: 16px; }
.form-input {
  width: 100%;
  height: 46px;
  padding: 0 14px 0 42px;
  border: 1px solid #dfe3ec;
  border-radius: 8px;
  color: #292e42;
  font-size: 14px;
  outline: none;
  background: #fafbfc;
  transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: #84A98C;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(132, 169, 140, 0.1);
}

.form-btn {
  width: 100%;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, opacity 0.2s;
}

.primary-btn {
  background: linear-gradient(135deg, #84A98C, #6B8F73);
  color: #fff;
  box-shadow: 0 8px 20px rgba(132, 169, 140, 0.22);
}

.primary-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #84A98C, #6B8F73);
  box-shadow: 0 10px 24px rgba(132, 169, 140, 0.3);
}

.form-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

.register-link {
  display: flex;
  justify-content: center;
  gap: 5px;
  margin-top: 28px;
  padding-top: 22px;
  border-top: 1px solid #eef0f5;
}

.register-text, .register-btn {
  font-size: 13px;
}

.register-text { color: #8b91a3; }
.register-btn {
  background: none;
  border: none;
  color: #84A98C;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  transition: all 0.3s ease;
}

.register-btn:hover {
  color: #84A98C;
  text-decoration: none;
}

@media (max-width: 760px) {
  .register-container { padding: 18px; }
  .register-shell { min-height: auto; display: block; }
  .register-brand-panel { display: none; }
  .register-main { display: block; padding: 26px 24px 34px; }
  .mobile-brand { display: flex; margin-bottom: 42px; }
  .brand-icon { width: 38px; height: 38px; font-size: 18px; }
  .brand-name { font-size: 19px; }
  .register-heading { margin-bottom: 28px; }
}
</style>
