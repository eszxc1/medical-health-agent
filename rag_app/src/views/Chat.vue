<template>
  <div class="chat-app-container">
    <!-- 左侧历史记录侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-brand">
          <span class="brand-icon">💬</span>
          <span class="brand-title">AI 助手</span>
        </div>
        <button class="new-chat-btn" @click="newChat">
          <span class="btn-icon">✚</span>
          <span>新建对话</span>
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input
          type="text"
          class="search-input"
          placeholder="搜索历史对话..."
          v-model="searchKeyword"
          @keyup.enter="searchHistory"
        />
      </div>

      <div class="history-divider">
        <span>历史记录</span>
        <span class="history-count" v-if="chatHistory.length">{{ chatHistory.length }}</span>
      </div>

      <div class="history-list" ref="chatHistory">
        <div
          v-for="(history, index) in chatHistory"
          :key="index"
          class="history-item"
          :class="{ active: currentHistoryIndex === index }"
          @click="switchHistory(index)"
        >
          <div class="history-item-content">
            <div class="history-item-icon">
              <span v-if="currentHistoryIndex === index">💡</span>
              <span v-else>📄</span>
            </div>
            <div class="history-item-text">
              <span class="history-title">{{ history.title || '未命名对话' }}</span>
              <span class="history-preview">{{ history.time || '' }}</span>
            </div>
          </div>
          <!-- ★ 新增：重命名对话按钮 -->
          <button
            class="updatehistorytitle-btn"
            @click.stop="updateHistoryTitle(history)"
            title="重命名对话"
          >
            <span>✎</span>
          </button>
          <button
            class="delete-btn"
            @click.stop="deleteHistory(index)"
            title="删除对话"
          >
            <span>✕</span>
          </button>
        </div>

        <!-- 空状态 -->
        <div v-if="chatHistory.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-text">暂无历史记录</div>
          <div class="empty-hint">点击上方按钮开始新对话</div>
        </div>
      </div>

      <!-- 底部用户信息 -->
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">{{ username ? username.charAt(0).toUpperCase() : 'U' }}</div>
          <!-- yllwyw 新增：点击用户名选择账号功能 -->
          <el-dropdown class="user-dropdown" trigger="click" placement="top-start" popper-class="user-account-menu" @command="handleUserCommand">
            <div class="user-entry">
              <div class="user-meta">
                <span class="user-name">{{ username }}</span>
                <span class="user-hint">账号管理</span>
              </div>
              <i class="el-icon-more user-menu-icon"></i>
            </div>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="switchAccount" icon="el-icon-sort">切换账号</el-dropdown-item>
              <!-- ★ 新增：退出登录 -->
              <el-dropdown-item command="logout" icon="el-icon-circle-close">退出登录</el-dropdown-item>
              <el-dropdown-item command="deleteAccount" icon="el-icon-delete" divided>用户注销</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
          <!-- yllwyw 新增结束 -->
        </div>
      </div>
    </div>

    <!-- 右侧主聊天区域 -->
    <div class="chat-main">
      <div class="chat-messages" ref="chatBox">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message-row"
          :class="msg.role"
        >
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="message-bubble user-bubble">
            <div class="bubble-avatar user-avatar-small">U</div>
            <div class="bubble-content">{{ msg.content }}</div>
          </div>

          <!-- AI消息 -->
          <div v-else class="message-bubble ai-bubble">
            <div class="bubble-avatar ai-avatar-small">🤖</div>
            <div class="bubble-content">
              <div class="ai-name">AI 医疗助手</div>
              <div v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>
        </div>

        <!-- 欢迎页面：Bento 卡片式首页（场景化 + 模块化） -->
        <div v-if="messages.length === 0" class="welcome-screen">
          <!-- F 型视觉热区：核心入口居中首屏 -->
          <div class="bento-hero">
            <div class="bento-hero-icon">🌿</div>
            <h2 class="bento-title">你好，我是你的 AI 健康顾问</h2>
            <p class="bento-desc">智能问诊 · 健康档案 · 用药安全，一站式守护你的健康</p>
            <button class="bento-primary-btn" @click="quickStart('我想咨询健康问题')">
              极速问诊
              <span class="bento-btn-arrow">→</span>
            </button>
          </div>
          <!-- 核心功能卡片 -->
          <div class="bento-grid">
            <div class="bento-card" @click="quickStart('我最近身体有些不适，帮我分析一下可能的原因')">
              <svg class="bento-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="3"/>
                <path d="M3 9h18M9 21V9"/>
              </svg>
              <div class="bento-card-title">智能问诊</div>
              <div class="bento-card-desc">描述症状，分析可能原因与就医建议</div>
            </div>
            <div class="bento-card" @click="quickStart('查看我的健康档案')">
              <svg class="bento-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
                <path d="M14 3v6h6M9 13h6M9 17h4"/>
              </svg>
              <div class="bento-card-title">健康档案</div>
              <div class="bento-card-desc">过敏史、慢病、用药记录统一管理</div>
            </div>
            <div class="bento-card" @click="quickStart('我想咨询用药安全问题')">
              <svg class="bento-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 3h6v3H9z"/>
                <path d="M12 6v12M8 12h8M8 15h8M8 18h8"/>
              </svg>
              <div class="bento-card-title">用药咨询</div>
              <div class="bento-card-desc">药物安全评估与相互作用检查</div>
            </div>
            <div class="bento-card" @click="quickStart('根据我的情况制定一个健康方案')">
              <svg class="bento-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>
              </svg>
              <div class="bento-card-title">健康方案</div>
              <div class="bento-card-desc">个性化饮食、运动、用药干预计划</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部输入区域 -->
      <div class="chat-input-area">
        <div class="input-wrapper">
          <input
            ref="questionInput"
            type="text"
            placeholder="请输入你的问题..."
            v-model="question"
            class="chat-input"
            @keyup.enter="handleSend"
          >
          <button type="button" @click="handleSend" class="send-btn" :disabled="!question">
            <span class="send-icon">➤</span>
          </button>
        </div>
        <div class="input-footer">
          <div class="mode-switch">
            <span
              class="mode-tab"
              :class="{active: chatMode === 'agent'}"
              @click="chatMode = 'agent'"
            >🧠 Agent</span>
            <span
              class="mode-tab"
              :class="{active: chatMode === 'no-agent'}"
              @click="chatMode = 'no-agent'"
            >💬 普通</span>
          </div>
          <span class="input-tip">Enter 发送</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

export default {
  name: "Chat",
  data() {
    return {
      messages: [],
      question: null,
      chatHistory: [],
      currentHistoryIndex: -1,
      chatMode: 'agent',
      isSending: false,
      isSaving: false,
      username: '',
      email: null,
      searchKeyword: '',
    }
  },
  methods: {
    handleSend() {
      if (this.chatMode === 'agent') {
        this.chatAgent();
      } else {
        this.chatNoAgent();
      }
    },

    // ★ Bento 首页卡片：快速开始（填充引导语 + 切 Agent 模式 + 聚焦输入框）
    quickStart(prompt) {
      this.chatMode = 'agent';
      this.question = prompt;
      this.$nextTick(() => {
        this.$refs.questionInput && this.$refs.questionInput.focus();
      });
    },

    searchHistory() {
      if (!this.searchKeyword.trim()) {
        this.queryHistoryByEmail();
        return;
      }

      this.$axios.get('/history/searchHistory', {
        params: {
          email: this.email,
          keyword: this.searchKeyword
        }
      }).then(res => {
        if (res.data.code === 200) {
          this.chatHistory = res.data.data.map(item => ({
            id: item.id,
            title: item.title,
            time: item.time
          }));
        } else {
          this.$message.error(res.data.msg || '搜索失败');
        }
      }).catch(err => {
        console.error('搜索历史记录失败', err);
        this.$message.error('搜索请求出错');
      });
    },

    chatNoAgent() {
      let _this = this;
      let myQuestion = _this.question;
      _this.question = null;
      if (!myQuestion.trim()) {
        _this.$message.warning("请输入内容");
        return
      }
      if (_this.currentHistoryIndex === -1 || !_this.chatHistory[_this.currentHistoryIndex]) {
        let title = myQuestion.length > 15 ? myQuestion.substring(0, 15) + "..." : myQuestion;
        let now = new Date();
        let timeStr = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0') + ' ' + String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0') + ':' + String(now.getSeconds()).padStart(2, '0');
        _this.chatHistory.unshift({id: Date.now(), title: title, messages: [], time: timeStr});
        _this.currentHistoryIndex = 0;
      }
      _this.chatHistory[_this.currentHistoryIndex].messages = JSON.parse(JSON.stringify(_this.messages));
      _this.messages.push({role: 'user', content: myQuestion});
      _this.messages.push({role: 'assistant', content: 'AI正在努力的生成回复，请稍等~ '});
      _this.scrollToBottom();
      _this.isSending = true;
      let params = new URLSearchParams({question: myQuestion});
      let es = new EventSource('http://localhost:8000/chat/chatNoAgentStream?' + params);
      let s = "";
      let streamEnded = false;   // ← 新增：流结束标记

      es.onmessage = function (event) {
        let data;
        try {
          data = JSON.parse(event.data);
        } catch (e) {
          console.error('[SSE] JSON 解析失败，跳过本条:', e);
          return;
        }
        if (!data) return;
        let result = data.content;
        if (result === "[DONE]") {
          streamEnded = true;    // ← 标记流已结束
          es.close();
          _this.isSending = false;
          _this.chatHistory[_this.currentHistoryIndex].messages = JSON.parse(JSON.stringify(_this.messages));
          _this.$nextTick(() => _this.scrollToBottom());
          // ★ saveChatResult 已移走，不在这里调用了
          return
        }
        s += result || '';
        _this.messages[_this.messages.length - 1].content = s;
        _this.chatHistory[_this.currentHistoryIndex].messages = JSON.parse(JSON.stringify(_this.messages));
        _this.scrollToBottom();
      };
      // ★ 新增：流正常结束时保存
      es.onclose = function () {
        if (streamEnded) {
          _this.saveChatResult(myQuestion, s);
        }
      };
      // ★ 新增：连接异常时也保存（兜底，保存已收到的部分）
      es.onerror = function (event) {
        console.log(event);
        _this.$message.error("与AI的连接异常，请稍后重试");
        streamEnded = true;      // ← 标记已结束，防止 onclose 重复保存
        es.close();
        _this.isSending = false;
      };
    },

    chatAgent() {
      let _this = this;
      let myQuestion = _this.question;
      _this.question = null;
      if (!myQuestion.trim()) {
        _this.$message.warning("请输入内容");
        return
      }
      if (_this.currentHistoryIndex === -1 || !_this.chatHistory[_this.currentHistoryIndex]) {
        let title = myQuestion.length > 15 ? myQuestion.substring(0, 15) + "..." : myQuestion;
        let now = new Date();
        let timeStr = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0') + ' ' + String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0') + ':' + String(now.getSeconds()).padStart(2, '0');
        _this.chatHistory.unshift({id: Date.now(), title: title, messages: [], time: timeStr});
        _this.currentHistoryIndex = 0;
      }
      _this.chatHistory[_this.currentHistoryIndex].messages = JSON.parse(JSON.stringify(_this.messages));
      _this.messages.push({role: 'user', content: myQuestion});
      _this.messages.push({role: 'assistant', content: 'AI正在努力的生成回复，请稍等~ '});
      _this.scrollToBottom();
      _this.isSending = true;

      let params = new URLSearchParams({question: myQuestion});
      if (_this.email) {
        params.append('email', _this.email);
      }
      let currentHistory = _this.chatHistory[_this.currentHistoryIndex];
      let historyIdToSend = (currentHistory && currentHistory.historyId) || sessionStorage.getItem('currentHistoryId') || 0;
      if (historyIdToSend) {
        params.append('history_id', historyIdToSend);
      }
      // ★ 调试日志：打印即将发送给后端的会话根 ID（验证刷新后是否仍为旧 ID）
      console.log('[Chat][发送] Sending Session ID (history_id):', historyIdToSend,
        '| currentHistoryIndex:', _this.currentHistoryIndex,
        '| sessionStorage:', sessionStorage.getItem('currentHistoryId'));
      let es = new EventSource('http://localhost:8000/chat/chatAgentStream?' + params);
      let s = "";
      let streamEnded = false;   // ← 新增：流结束标记

      es.onmessage = function (event) {
        let data;
        try {
          data = JSON.parse(event.data);
        } catch (e) {
          console.error('[SSE] JSON 解析失败，跳过本条:', e);
          return;
        }
        if (!data || !data.type) return;
        if (!data.startTime) data.startTime = Date.now();
        if (data.type === 'text') {
          // 增加调试日志，确认前端到底收到了什么
          console.log('[SSE] 收到文本片段:', data.content);

          // 过滤掉纯空白或仅包含分割符的内容，避免无效渲染
          let cleanContent = data.content || '';
          if (cleanContent.trim() && cleanContent !== '<!--SPLIT-->') {
            s += cleanContent;
            _this.messages[_this.messages.length - 1].content = s;
            // 保持原有的历史同步逻辑
            _this.chatHistory[_this.currentHistoryIndex].messages = JSON.parse(JSON.stringify(_this.messages));
            _this.scrollToBottom();
          }
        }
        if (data.type === 'end') {
          streamEnded = true;      // ← 标记流已结束
          es.close();
          _this.isSending = false;
          // ★ 从后端 SSE 捕获会话根 ID，写入当前会话对象 + sessionStorage（修复刷新断连）
          if (data.history_id) {
            let idx = _this.currentHistoryIndex;
            if (idx >= 0 && _this.chatHistory[idx]) {
              _this.chatHistory[idx].historyId = data.history_id;
              // ★ 修复：同步纠正 id —— 新建对话的 id 是 Date.now() 占位符，
              //    必须替换为后端真实 history_id，否则重命名/删除会发错 ID
              _this.chatHistory[idx].id = data.history_id;
            }
            sessionStorage.setItem('currentHistoryId', String(data.history_id));
            console.log('[Chat][结束] 后端返回会话根 ID 并已持久化:', data.history_id);
          }
          _this.chatHistory[_this.currentHistoryIndex].messages = JSON.parse(JSON.stringify(_this.messages));
          _this.$nextTick(() => _this.scrollToBottom());
          // ★ saveChatResult 已移走，不在这里调用了
          return
        }
      };
      // ★ 后端已保存历史，前端不再重复保存（避免产生重复根节点）
      es.onclose = function () {
        if (streamEnded) {
          console.log('[Chat][结束] Agent 流已结束，历史由后端保存，前端跳过重复保存');
        }
      };
      // ★ 新增：连接异常时也保存（兜底）
      es.onerror = function (event) {
        console.log(event);
        _this.$message.error("与AI的连接异常，请稍后重试");
        streamEnded = true;        // ← 标记已结束，防止 onclose 重复保存
        es.close();
        _this.isSending = false;
      };
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const chatBox = this.$refs.chatBox;
        if (chatBox) {
          chatBox.scrollTop = chatBox.scrollHeight;
        }
      });
    },

    saveChatResult(question, answer) {
      let _this = this;
      if (!_this.email || _this.isSaving) return;  // ★ 新增：防重复保存
      _this.isSaving = true;                        // ★ 新增：加锁
      let parentId = 0;
      if (_this.currentHistoryIndex !== -1 && _this.chatHistory[_this.currentHistoryIndex].historyId) {
        parentId = _this.chatHistory[_this.currentHistoryIndex].historyId;
      }
      _this.$axios({
        url: '/history/saveChatResult',
        method: 'post',
        headers: {
          'Content-Type': 'application/json'
        },
        data: JSON.stringify({
          question: question,
          answer: answer,
          parentId: parentId,
          email: _this.email
        })
      }).then(res => {
        if (res.data.code === 200 && res.data.data && res.data.data.history_id) {
          if (!_this.chatHistory[_this.currentHistoryIndex].historyId) {
            _this.chatHistory[_this.currentHistoryIndex].historyId = res.data.data.history_id;
          }
          // ★ 修复：持久化当前会话根 ID 到 sessionStorage
          // 为什么？—— historyId 存在 Vue data 里，刷新页面后丢失，
          //    导致下一条消息 parent_id=0，数据库产生新会话，多轮上下文断裂。
          //    sessionStorage 跨刷新保留，保证刷新后仍能继续当前会话。
          sessionStorage.setItem('currentHistoryId', _this.chatHistory[_this.currentHistoryIndex].historyId);
        }
      }).finally(() => {                       // ★ 新增：无论成功失败都释放锁
        _this.isSaving = false;
      });
    },

    renderMarkdown(content) {
      if (!content) return '';
      // ★ 免责声明样式优化：使用唯一锚点 <!--SPLIT--> 切割免责声明
      // 为什么用 HTML 注释而非 ⚠️ 或"免责声明"文本？
      // —— ⚠️ 图标会出现在 AI 正文的"风险提示"部分，"免责声明"也可能被正文提及，
      //    只有 <!--SPLIT--> 是正文中绝对不可能出现的唯一标识，确保切割准确。
      const SPLIT_ANCHOR = '<!--SPLIT-->';
      // ★ 修复：用 split 处理，兼容可能出现的多个锚点（去重：正文取第一段、声明取最后一段）
      const segments = content.split(SPLIT_ANCHOR);
      if (segments.length === 1) {
        // 不含免责声明，正常渲染
        return this.$md.render(content);
      }
      const mainText = segments[0];
      const disclaimerText = segments[segments.length - 1];

      // ★ 修复：触发条件判断——仅当正文确属医疗/健康内容时才渲染声明框，
      //         普通闲聊（如"你好"）不再误触发该组件
      if (!this.isMedicalContent(mainText)) {
        return this.$md.render(mainText);
      }

      const mainHtml = this.$md.render(mainText);
      // 去掉 Markdown 引用符号 > 和多余空白，再渲染（**免责声明** 仍会加粗）
      const cleanDisclaimer = disclaimerText.replace(/^[\s>]+/, '').trim();
      const disclaimerHtml = this.$md.render(cleanDisclaimer);
      // 内联样式（scoped CSS 无法作用于 v-html 注入内容，故用内联样式保证生效）
      const boxStyle = 'margin-top:12px;padding:10px 14px;background:#f7f8fa;'
        + 'border:1px solid #e4e7ed;border-left:3px solid #e6a23c;border-radius:4px;'
        + 'font-size:12px;color:#909399;line-height:1.7;';
      // 单条消息最多只渲染一次免责声明（去重）
      return mainHtml + '<div style="' + boxStyle + '">' + disclaimerHtml + '</div>';
    },

    // 医疗/健康关键词判断：比后端 medical_keywords 更精准，
    // 去掉"建议/注意/方案"这类问候中也会出现的宽泛词，避免普通闲聊误触发声明框
    isMedicalContent(text) {
      const keywords = [
        '疾病', '症状', '过敏', '用药', '服药', '药物', '治疗', '诊断',
        '高血压', '糖尿病', '忌口', '宜吃', '禁忌', '副作用', '处方',
        '就医', '复诊', '饮食', '食谱', '慎用', '不宜', '调理', '检查',
      ];
      return keywords.some(kw => text.indexOf(kw) !== -1);
    },

    newChat() {
      this.messages = [];
      this.currentHistoryIndex = -1;
      // ★ 修复：新建对话时清除持久化的会话 ID，避免下次刷新又回到旧会话
      sessionStorage.removeItem('currentHistoryId');
      this.$nextTick(() => {
        this.$refs.questionInput && this.$refs.questionInput.focus();
      });
    },

    switchHistory(index) {
      let _this = this;
      if (_this.currentHistoryIndex >= 0 && _this.chatHistory[_this.currentHistoryIndex]) {
        _this.chatHistory[_this.currentHistoryIndex].messages = JSON.parse(JSON.stringify(_this.messages));
      }
      let item = this.chatHistory[index];
      if (item && item.id) {
        _this.$axios.get('/history/queryHistoryAllById', {
          params: {historyId: item.id}
        }).then(function (res) {
          if (res.data && res.data.code === 200 && res.data.data) {
            _this.messages = res.data.data;
            _this.currentHistoryIndex = index;
            _this.scrollToBottom();
          }
        }).catch(function (err) {
          console.log('加载对话记录失败', err);
        });
      }
    },

    // ★ 新增：调用后端 API 同步删除数据库记录
    deleteHistory(index) {
      let _this = this;
      let historyIdToDelete = _this.chatHistory[index] ? _this.chatHistory[index].id : null;

      // 1. 前端删除
      _this.chatHistory.splice(index, 1);

      // 2. 处理删除后的状态
      if (_this.chatHistory.length === 0) {
        _this.messages = [];
        _this.currentHistoryIndex = -1;
        sessionStorage.removeItem('currentHistoryId');  // ★ 清空失效的会话 ID
      } else {
        if (_this.currentHistoryIndex === index) {
          _this.currentHistoryIndex = 0;
          let firstItem = _this.chatHistory[0];
          if (firstItem && firstItem.id) {
            _this.$axios.get('/history/queryHistoryAllById', {
              params: { historyId: firstItem.id }
            }).then(res => {
              if (res.data && res.data.code === 200) {
                _this.messages = res.data.data;
                _this.scrollToBottom();
              }
            });
          }
        } else if (_this.currentHistoryIndex > index) {
          _this.currentHistoryIndex--;
        }
      }

      // 3. 同步删除后端数据库记录
      if (historyIdToDelete) {
        _this.$axios({
          url: '/history/deleteHistory',
          method: 'post',
          params: { history_id: historyIdToDelete }
        }).then(res => {
          if (res.data.code === 200) {
            _this.$message.success('删除成功');
          } else {
            _this.$message.error(res.data.msg || '数据库删除失败');
          }
        }).catch(err => {
          console.error('删除请求出错', err);
          _this.$message.error('删除请求出错');
        });
      }
    },

    // ★ 新增：重命名对话标题
    updateHistoryTitle(history) {
      let _this = this;
      _this.$prompt('请输入新的对话标题', '重命名', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: history.title,
        inputPattern: /^.{1,50}$/,
        inputErrorMessage: '标题长度需在1到50个字符之间'
      }).then(({ value }) => {
        _this.$axios({
          url: '/history/updateHistoryTitle',
          method: 'post',
          params: {
            history_id: history.historyId || history.id,
            new_title: value
          }
        }).then(res => {
          if (res.data.code === 200) {
            history.title = value;
            _this.$message.success('重命名成功');
          } else {
            _this.$message.error(res.data.msg || '重命名失败');
          }
        }).catch(err => {
          console.error('重命名请求出错', err);
          _this.$message.error('重命名请求出错');
        });
      }).catch(() => {
        // 用户取消输入，不做任何操作
      });
    },

    queryHistoryByEmail() {
      let _this = this;
      if (!_this.email) return;
      _this.$axios({
        url: '/history/queryHistoryByEmail',
        method: 'get',
        params: {
          email: _this.email
        }
      }).then(res => {
        if (res.data.code === 200) {
          _this.chatHistory = res.data.data;
          _this.chatHistory.forEach(function (item) {
            item.historyId = item.id;
            // ★ 新增：title 回退逻辑
            item.title = item.title || item.question || '未命名对话';
          });
          // ★ 修复：历史列表加载完成后，自动恢复上次的会话
          _this.restoreCurrentHistory();
        }
      }).catch(function (err) {
        console.log('加载历史记录失败', err);
      });
    },

    // ★ 修复：从 sessionStorage 恢复上次会话，避免刷新后当前会话丢失
    restoreCurrentHistory() {
      const lastHistoryId = sessionStorage.getItem('currentHistoryId');
      if (!lastHistoryId) return;
      // 在历史列表中查找对应的会话
      const idx = this.chatHistory.findIndex(item => String(item.id) === String(lastHistoryId));
      if (idx !== -1) {
        // 找到了，自动切换到该会话（加载其消息，currentHistoryIndex 指向它）
        this.switchHistory(idx);
      } else {
        // 会话已不存在（可能被删除），清除失效的持久化
        sessionStorage.removeItem('currentHistoryId');
      }
    },

    // yllwyw 新增：统一接收用户菜单操作
    handleUserCommand(command) {
      if (command === 'deleteAccount') this.handleDeleteAccount();
      if (command === 'switchAccount') this.handleSwitchAccount();
      // ★ 新增：退出登录
      if (command === 'logout') this.handleLogout();
    },

    // 退出登录
    handleLogout() {
      sessionStorage.removeItem('username');
      sessionStorage.removeItem('email');
      this.$router.push('/').catch(err => {
        if (err.name !== 'NavigationDuplicated') {
          console.error(err);
        }
      });
      this.$message.success('已退出登录');
    },

    // yllwyw 新增：用户注销
    handleDeleteAccount() {
      this.$confirm('注销后当前账号将被删除，确定继续吗？', '用户注销', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.$axios({
          url: '/users/deleteAccount',
          method: 'delete',
          params: {email: this.email}
        }).then(res => {
          if (res.data.code === 200) {
            sessionStorage.removeItem('username');
            sessionStorage.removeItem('email');
            this.$router.push('/').catch(err => {
              if (err.name !== 'NavigationDuplicated') {
                console.error(err);
              }
            });
            this.$message.success(res.data.msg || '账号已注销');
          } else {
            this.$message.error(res.data.msg || '账号注销失败');
          }
        }).catch(() => {
          this.$message.error('账号注销失败');
        });
      }).catch(() => {
      });
    },

    // yllwyw 新增：切换账号
    handleSwitchAccount() {
      sessionStorage.removeItem('username');
      sessionStorage.removeItem('email');
      this.$router.push('/').catch(err => {
        if (err.name !== 'NavigationDuplicated') {
          console.error(err);
        }
      });
      this.$message.success('请登录其他账号');
    }
    // yllwyw 新增结束
  },
  created() {
    this.username = sessionStorage.getItem('username') || '用户';
    this.email = sessionStorage.getItem('email');
  },
  mounted() {
    this.$nextTick(() => {
      this.$refs.questionInput && this.$refs.questionInput.focus();
    });
    this.queryHistoryByEmail();
  },
}
</script>

<style scoped>
/* ===== 整体布局 ===== */
.chat-app-container {
  display: flex;
  height: 100vh;
  font-family: var(--font-family);
  background: var(--color-bg);
}

/* ===== 左侧侧边栏 ===== */
.sidebar {
  width: 280px;
  background: linear-gradient(180deg, #F1F6F1 0%, #E3EDE4 100%);
  color: #3D4A3E;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(132, 169, 140, 0.12);
  position: relative;
  overflow: hidden;
}

.sidebar-header {
  padding: 20px 16px 12px;
  border-bottom: 1px solid rgba(132, 169, 140, 0.1);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.brand-icon {
  font-size: 24px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #A8C3A8, #6B8F73);
  border-radius: 10px;
}

.brand-title {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #84A98C, #6B8F73);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.new-chat-btn {
  width: 100%;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #6B8F73 0%, #84A98C 100%);
  border: none;
  border-radius: 10px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(132, 169, 140, 0.3);
}

.new-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(132, 169, 140, 0.45);
}

.new-chat-btn:active {
  transform: translateY(0);
}

.btn-icon {
  font-size: 16px;
  font-weight: 300;
}

.search-box {
  padding: 12px 16px;
  position: relative;
}

.search-icon {
  position: absolute;
  left: 26px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  opacity: 0.5;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 8px 12px 8px 32px;
  background: rgba(132, 169, 140, 0.08);
  border: 1px solid rgba(132, 169, 140, 0.12);
  border-radius: 8px;
  color: #3D4A3E;
  font-size: 13px;
  outline: none;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.search-input:focus {
  border-color: rgba(132, 169, 140, 0.4);
  background: rgba(255, 255, 255, 0.6);
}

.search-input::placeholder {
  color: rgba(90, 61, 74, 0.3);
}

.history-divider {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(90, 61, 74, 0.4);
}

.history-count {
  background: rgba(132, 169, 140, 0.12);
  padding: 0 6px;
  border-radius: 4px;
  font-size: 10px;
  line-height: 18px;
  color: #7C9A82;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px 8px;
}

.history-list::-webkit-scrollbar {
  width: 4px;
}

.history-list::-webkit-scrollbar-track {
  background: transparent;
}

.history-list::-webkit-scrollbar-thumb {
  background: rgba(132, 169, 140, 0.15);
  border-radius: 4px;
}

.history-list::-webkit-scrollbar-thumb:hover {
  background: rgba(132, 169, 140, 0.25);
}

.history-item {
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 10px;
  transition: all 0.2s ease;
  margin-bottom: 2px;
  position: relative;
}

.history-item:hover {
  background: rgba(132, 169, 140, 0.08);
}

.history-item.active {
  background: rgba(132, 169, 140, 0.12);
  border: 1px solid rgba(132, 169, 140, 0.2);
}

.history-item-content {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.history-item-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  background: rgba(132, 169, 140, 0.08);
  border-radius: 8px;
  margin-top: 1px;
}

.history-item.active .history-item-icon {
  background: rgba(132, 169, 140, 0.15);
}

.history-item-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.history-title {
  font-size: 13px;
  font-weight: 500;
  color: #3D4A3E;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.history-item.active .history-title {
  color: #6B8F73;
  font-weight: 600;
}

.history-preview {
  font-size: 11px;
  color: rgba(90, 61, 74, 0.4);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
}

/* ★ 新增：重命名对话按钮样式 */
.updatehistorytitle-btn {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: rgba(132, 169, 140, 0.3);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  opacity: 0;
  transition: all 0.2s ease;
  margin-left: 4px;
}

.history-item:hover .updatehistorytitle-btn {
  opacity: 1;
}

.updatehistorytitle-btn:hover {
  background: rgba(132, 169, 140, 0.12);
  color: #84A98C;
}

.delete-btn {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: rgba(132, 169, 140, 0.3);
  border-radius: 6px;
  cursor: pointer;
  font-size: 10px;
  opacity: 0;
  transition: all 0.2s ease;
  margin-left: 4px;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: rgba(132, 169, 140, 0.15);
  color: #84A98C;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
  color: rgba(90, 61, 74, 0.45);
  margin-bottom: 4px;
}

.empty-hint {
  font-size: 12px;
  color: rgba(90, 61, 74, 0.3);
}

/* ===== 侧边栏底部 - 含退出按钮 ===== */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(132, 169, 140, 0.1);
  background: rgba(255, 255, 255, 0.48); /* yllwyw 新增 */
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px; /* yllwyw 新增 */
  border: 1px solid rgba(132, 169, 140, 0.12); /* yllwyw 新增 */
  border-radius: 8px; /* yllwyw 新增 */
  background: rgba(255, 255, 255, 0.7); /* yllwyw 新增 */
  box-shadow: 0 4px 14px rgba(132, 169, 140, 0.06); /* yllwyw 新增 */
}

.user-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #A8C3A8, #6B8F73);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: rgba(90, 61, 74, 0.7);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* yllwyw 新增：美化用户入口 */
.user-dropdown {
  flex: 1;
  min-width: 0;
}

.user-entry {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 2px 4px;
  border-radius: 6px;
  cursor: pointer;
  outline: none;
  transition: background 0.2s ease;
}

.user-entry:hover {
  background: rgba(132, 169, 140, 0.08);
}

.user-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.user-hint {
  color: rgba(90, 61, 74, 0.42);
  font-size: 11px;
}

.user-menu-icon {
  flex-shrink: 0;
  color: #7C9A82;
  font-size: 16px;
}
/* yllwyw 新增结束 */

/* ===== 右侧聊天区 ===== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 16px 0 0 16px;
  overflow: hidden;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.05);
}

.chat-messages {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
  background: #f8f9fc;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

.message-row {
  display: flex;
  margin-bottom: 20px;
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  display: flex;
  gap: 10px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.bubble-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 2px;
}

.user-avatar-small {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  order: 1;
}

.ai-avatar-small {
  background: #f0f0f0;
  font-size: 16px;
}

.bubble-content {
  padding: 12px 16px;
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.user-bubble .bubble-content {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: #fff;
  border-bottom-right-radius: 4px;
}

.ai-bubble .bubble-content {
  background: #fff;
  color: #333;
  border-bottom-left-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.ai-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary-dark);
  margin-bottom: 4px;
}

.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 32px;
  text-align: center;
  overflow-y: auto;
}

/* F 型视觉热区：核心入口居中首屏 */
.bento-hero {
  max-width: 560px;
  margin-bottom: 40px;
}

.bento-hero-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  font-size: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #E4F0E6, #D8E4EE);
  border-radius: 20px;
  box-shadow: var(--shadow-soft);
}

.bento-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 10px;
}

.bento-desc {
  font-size: 16px;
  color: var(--color-text-secondary);
  margin: 0 0 24px;
}

.bento-primary-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  box-shadow: var(--shadow-hover);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.bento-primary-btn:hover {
  transform: translateY(-2px);
}

.bento-btn-arrow {
  transition: transform 0.2s ease;
}

.bento-primary-btn:hover .bento-btn-arrow {
  transform: translateX(4px);
}

/* 核心功能卡片网格 */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  max-width: 900px;
  width: 100%;
}

.bento-card {
  padding: 24px 20px;
  background: #fff;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: left;
  box-shadow: var(--shadow-soft);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.bento-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
}

.bento-card-icon {
  width: 36px;
  height: 36px;
  color: var(--color-primary);
  margin-bottom: 14px;
}

.bento-card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 6px;
}

.bento-card-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.chat-input-area {
  padding: 16px 24px 20px;
  border-top: 1px solid #eee;
  background: #fff;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f0f2f5;
  border: 2px solid transparent;
  border-radius: 12px;
  padding: 4px;
  transition: all 0.3s ease;
}

.input-wrapper:focus-within {
  border-color: var(--color-primary);
  background: #fff;
  box-shadow: 0 0 0 3px rgba(132, 169, 140, 0.12);
}

.chat-input {
  flex: 1;
  padding: 10px 12px;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: #333;
}

.chat-input::placeholder {
  color: #bbb;
}

.send-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  border: none;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(132, 169, 140, 0.3);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-icon {
  transform: rotate(0deg);
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  padding: 0 4px;
}

.mode-switch {
  display: flex;
  gap: 4px;
}

.mode-tab {
  padding: 4px 10px;
  font-size: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #999;
  background: transparent;
}

.mode-tab:hover {
  color: #666;
  background: #f0f2f5;
}

.mode-tab.active {
  color: var(--color-primary-dark);
  background: rgba(132, 169, 140, 0.1);
  font-weight: 600;
}

.input-tip {
  font-size: 11px;
  color: #bbb;
}

/* ===== Markdown 样式 ===== */
.ai-bubble p {
  margin: 0 0 8px 0;
}

.ai-bubble p:last-child {
  margin-bottom: 0;
}

.ai-bubble pre {
  background: #1a1a2e;
  color: #e0e0e0;
  padding: 12px 14px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
  font-size: 13px;
}

.ai-bubble code {
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 13px;
}

.ai-bubble :not(pre) > code {
  background: rgba(132, 169, 140, 0.1);
  color: var(--color-primary-dark);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.ai-bubble ul, .ai-bubble ol {
  margin: 4px 0;
  padding-left: 20px;
}

.ai-bubble li {
  margin: 2px 0;
}

.ai-bubble blockquote {
  border-left: 3px solid var(--color-primary);
  margin: 8px 0;
  padding: 4px 12px;
  color: #666;
  background: rgba(132, 169, 140, 0.06);
  border-radius: 0 4px 4px 0;
}
</style>
