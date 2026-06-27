<template>
  <div class="settings-page">

    <header class="settings-header">
      <div class="settings-header-left">
        <button class="btn-back" @click="router.push('/')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
          </svg>
          返回
        </button>
        <h1 class="settings-title">设置</h1>
      </div>
      <div class="settings-header-right">
        <LanguageSwitcher />
        <button class="btn-header-icon" @click="router.push('/admin')" title="用户管理">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zM8 11c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5C15 14.17 10.33 13 8 13zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
          </svg>
        </button>
        <span class="user-badge">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
          <span>{{ displayUsername }}</span>
        </span>
        <button class="btn-header-icon" @click="logout" title="退出登录">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M10.09 15.59 11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3h-8v2h8v14h-8v2h8c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z" />
          </svg>
        </button>
      </div>
    </header>

    <div class="settings-layout">

      <nav class="settings-nav">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="nav-item"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <span class="nav-icon" v-html="tab.icon" />
          {{ tab.label }}
        </button>
      </nav>


      <main class="settings-content">
        <div v-if="loading" class="loading-state">加载中...</div>

        <template v-else>

          <section v-if="activeTab === 'overview'" class="settings-section overview-section">
            <div class="section-header">
              <h2>配置总览</h2>
              <p class="section-desc">当前各服务的配置状态一览</p>
            </div>

            <div class="overview-grid">

              <div class="overview-card" @click="activeTab = 'bailian'">
                <div class="overview-card-header">
                  <span class="overview-card-title">百炼 API Key</span>
                  <span class="overview-badge" :class="saved.bailian_api_key ? 'configured' : 'unconfigured'">
                    {{ saved.bailian_api_key ? '已配置' : '未配置' }}
                  </span>
                </div>
                <p class="overview-card-detail" v-if="saved.bailian_api_key">
                  {{ saved.bailian_api_key.slice(0, 8) }}...
                </p>
                <p class="overview-card-detail muted" v-else>点击前往配置</p>
              </div>


              <div class="overview-card" @click="activeTab = 'llm'">
                <div class="overview-card-header">
                  <span class="overview-card-title">LLM 大模型</span>
                  <span class="overview-badge" :class="overviewLlmReady ? 'configured' : 'unconfigured'">
                    {{ overviewLlmReady ? '已配置' : '未配置' }}
                  </span>
                </div>
                <p class="overview-card-detail">
                  {{ saved.llm_source === 'custom' ? '自定义' : '百炼' }}
                  · {{ saved.llm_source === 'custom' ? (saved.llm_model || '未设置模型') : (saved.llm_bailian_model || '未设置模型') }}
                  <template v-if="saved.llm_source === 'custom'">· {{ apiFormatLabel(saved.llm_api_format) }}</template>
                </p>
              </div>


              <div class="overview-card" @click="activeTab = 'llm'">
                <div class="overview-card-header">
                  <span class="overview-card-title">VLM 视觉模型</span>
                  <span class="overview-badge" :class="overviewVlmReady ? 'configured' : 'unconfigured'">
                    {{ overviewVlmReady ? '已配置' : '未配置' }}
                  </span>
                </div>
                <p class="overview-card-detail">
                  {{ saved.vlm_source === 'custom' ? '自定义' : '百炼' }}
                  · {{ saved.vlm_source === 'custom' ? (saved.vlm_model || '未设置模型') : (saved.vlm_bailian_model || '未设置模型') }}
                </p>
              </div>


              <div class="overview-card" @click="activeTab = 'embedding'">
                <div class="overview-card-header">
                  <span class="overview-card-title">Embedding 向量化</span>
                  <span class="overview-badge" :class="overviewEmbeddingReady ? 'configured' : 'unconfigured'">
                    {{ overviewEmbeddingReady ? '已配置' : '未配置' }}
                  </span>
                </div>
                <p class="overview-card-detail">
                  {{ saved.embedding_source === 'local' ? '本地服务' : '百炼' }}
                  <template v-if="saved.embedding_source === 'local'">· {{ saved.embedding_base_url || '未设置地址' }}</template>
                  <template v-else>· {{ saved.embedding_bailian_model || '未设置模型' }}</template>
                </p>
              </div>


              <div class="overview-card" @click="activeTab = 'mineru'">
                <div class="overview-card-header">
                  <span class="overview-card-title">MinerU PDF 解析</span>
                  <span class="overview-badge" :class="overviewMineruReady ? 'configured' : 'unconfigured'">
                    {{ overviewMineruReady ? '已配置' : '未配置' }}
                  </span>
                </div>
                <p class="overview-card-detail">
                  {{ saved.mineru_source === 'local' ? '本地服务' : '官方 API' }}
                  <template v-if="saved.mineru_source === 'local'">· {{ saved.mineru_base_url || '未设置地址' }}</template>
                  <template v-else>· {{ saved.mineru_api_key ? 'Key 已填写' : '未配置 Key' }}</template>
                </p>
              </div>


              <div class="overview-card disabled-card">
                <div class="overview-card-header">
                  <span class="overview-card-title">FunASR 语音转写</span>
                  <span class="overview-badge coming-soon">即将支持</span>
                </div>
                <p class="overview-card-detail muted">音频文件解析功能开发中</p>
              </div>


              <div class="overview-card" @click="activeTab = 'websearch'">
                <div class="overview-card-header">
                  <span class="overview-card-title">联网搜索</span>
                  <span class="overview-badge" :class="saved.bocha_api_key ? 'configured' : 'unconfigured'">
                    {{ saved.bocha_api_key ? '已配置' : '未配置' }}
                  </span>
                </div>
                <p class="overview-card-detail">博查 API</p>
              </div>
            </div>
          </section>


          <section v-if="activeTab === 'bailian'" class="settings-section">
            <div class="section-header">
              <h2>阿里云百炼</h2>
              <p class="section-desc">
                填写阿里云百炼 API Key 作为通用凭证。各服务选择「使用百炼模型」时将自动使用此 Key。
                <a href="https://bailian.console.aliyun.com/" target="_blank">前往百炼控制台</a>
              </p>
            </div>

            <div class="form-group">
              <label>百炼 API Key</label>
              <div class="input-row">
                <input
                  :type="showBailianKey ? 'text' : 'password'"
                  v-model="draft.bailian_api_key"
                  placeholder="sk-..."
                  class="input"
                />
                <button class="btn-icon" @click="showBailianKey = !showBailianKey" title="显示/隐藏">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path v-if="showBailianKey" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                    <path v-else d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
                  </svg>
                </button>
              </div>
              <p class="field-hint">此 Key 将作为 LLM、Embedding 等服务的默认凭证</p>
            </div>

            <div class="form-actions">
              <button class="btn-save" @click="save('bailian')" :disabled="saving">
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </section>


          <section v-if="activeTab === 'llm'" class="settings-section">

            <div class="section-header">
              <h2>LLM 模型</h2>
              <p class="section-desc">用于智能问答的大语言模型</p>
            </div>

            <div class="form-group">
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="draft.llm_source" value="bailian" />
                  <span>使用百炼模型</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="draft.llm_source" value="custom" />
                  <span>自定义（OpenAI / Anthropic / DeepSeek / Ollama / 兼容接口）</span>
                </label>
              </div>
            </div>


            <template v-if="draft.llm_source === 'bailian'">
              <div class="form-group">
                <label>模型名称</label>
                <input
                  v-model="draft.llm_bailian_model"
                  placeholder="例如：qwen-max"
                  class="input"
                />
                <p class="field-hint">填写百炼平台支持的模型名称，需先在百炼控制台开通对应模型</p>
              </div>
            </template>


            <template v-if="draft.llm_source === 'custom'">
              <div class="form-group">
                <label>API Key</label>
                <div class="input-row">
                  <input
                    :type="showLlmKey ? 'text' : 'password'"
                    v-model="draft.llm_api_key"
                    placeholder="sk-..."
                    class="input"
                  />
                  <button class="btn-icon" @click="showLlmKey = !showLlmKey" title="显示/隐藏">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path v-if="showLlmKey" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                      <path v-else d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
                    </svg>
                  </button>
                </div>
              </div>

              <div class="form-group">
                <div class="label-row">
                  <label>Base URL</label>
                  <BaseUrlHelpTooltip />
                </div>
                <input
                  v-model="draft.llm_base_url"
                  :placeholder="draft.llm_api_format === 'anthropic' ? 'https://api.anthropic.com' : 'https://api.openai.com/v1'"
                  class="input"
                />
              </div>

              <div class="form-group">
                <label>请求格式</label>
                <div class="radio-group">
                  <label class="radio-item">
                    <input type="radio" v-model="draft.llm_api_format" value="openai" />
                    <span>OpenAI Chat Completions</span>
                  </label>
                  <label class="radio-item">
                    <input type="radio" v-model="draft.llm_api_format" value="anthropic" />
                    <span>Anthropic Messages</span>
                  </label>
                </div>
              </div>

              <div class="form-group">
                <label>模型名称</label>
                <input v-model="draft.llm_model" placeholder="例如：deepseek-chat、kimi-k2.5、gpt-4o" class="input" />
              </div>
            </template>

            <div class="form-actions">
              <button class="btn-test" @click="testLlm" :disabled="testing.llm">
                {{ testing.llm ? '测试中...' : '测试连接' }}
              </button>
              <span v-if="testResult.llm" class="test-result" :class="testResult.llm.ok ? 'ok' : 'fail'">
                {{ testResult.llm.msg }}
              </span>
              <button class="btn-save" @click="save('llm')" :disabled="saving">
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>


            <div class="form-group easy-task-group">
              <label class="switch-row">
                <span class="switch-text">
                  配置 easy task model
                  <span class="switch-sub">节省计划 · 解析任务的摘要生成使用更便宜的模型，复用上方主模型的 Key 和地址，仅替换模型名</span>
                </span>
                <span class="switch" :class="{ on: easyTaskEnabled }">
                  <input
                    type="checkbox"
                    :checked="easyTaskEnabled"
                    @change="toggleEasyTask(($event.target as HTMLInputElement).checked)"
                  />
                  <span class="switch-knob"></span>
                </span>
              </label>
              <template v-if="easyTaskEnabled">
                <input
                  v-model="draft.easy_task_llm"
                  placeholder="例如：deepseek-v4-flash"
                  class="input easy-task-input"
                />
                <p class="field-hint">
                  需与上方主模型为同一 provider（复用其 Key 和地址）。例如主模型配置为 deepseek-v4-pro 时，这里可填更便宜的 deepseek-v4-flash；具体模型名以该 provider 实际支持的为准。
                </p>
              </template>
              <div v-if="easyTaskEnabled" class="form-actions easy-task-actions">
                <button class="btn-test" @click="testEasyTask" :disabled="testing.easytask || !draft.easy_task_llm">
                  {{ testing.easytask ? '测试中...' : '测试连接' }}
                </button>
                <span v-if="testResult.easytask" class="test-result" :class="testResult.easytask.ok ? 'ok' : 'fail'">
                  {{ testResult.easytask.msg }}
                </span>
                <button class="btn-save" @click="save('easytask')" :disabled="saving">
                  {{ saving ? '保存中...' : '保存' }}
                </button>
              </div>
            </div>

            <hr class="section-divider" />


            <div class="section-header">
              <h2>VLM 模型</h2>
              <p class="section-desc">用于 PDF 图片分析的视觉语言模型</p>
            </div>

            <div class="form-group">
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="draft.vlm_source" value="bailian" />
                  <span>使用百炼模型</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="draft.vlm_source" value="custom" />
                  <span>自定义（OpenAI / 兼容接口）</span>
                </label>
              </div>
            </div>


            <template v-if="draft.vlm_source === 'bailian'">
              <div class="form-group">
                <label>模型名称</label>
                <input
                  v-model="draft.vlm_bailian_model"
                  placeholder="例如：qwen-vl-plus、qwen-vl-max"
                  class="input"
                />
                <p class="field-hint">填写百炼平台支持的多模态模型名称</p>
              </div>
            </template>


            <template v-if="draft.vlm_source === 'custom'">
              <div class="form-group">
                <label>API Key</label>
                <div class="input-row">
                  <input
                    :type="showVlmKey ? 'text' : 'password'"
                    v-model="draft.vlm_api_key"
                    placeholder="sk-..."
                    class="input"
                  />
                  <button class="btn-icon" @click="showVlmKey = !showVlmKey" title="显示/隐藏">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path v-if="showVlmKey" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                      <path v-else d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
                    </svg>
                  </button>
                </div>
              </div>

              <div class="form-group">
                <label>Base URL <span class="optional">（可选）</span></label>
                <input v-model="draft.vlm_base_url" placeholder="https://api.openai.com/v1" class="input" />
              </div>

              <div class="form-group">
                <label>模型名称</label>
                <input v-model="draft.vlm_model" placeholder="gpt-4o" class="input" />
              </div>
            </template>

            <div class="form-actions">
              <button class="btn-test" @click="testVlm" :disabled="testing.vlm">
                {{ testing.vlm ? '测试中...' : '测试连接' }}
              </button>
              <span v-if="testResult.vlm" class="test-result" :class="testResult.vlm.ok ? 'ok' : 'fail'">
                {{ testResult.vlm.msg }}
              </span>
              <button class="btn-save" @click="save('vlm')" :disabled="saving">
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </section>


          <section v-if="activeTab === 'embedding'" class="settings-section">
            <div class="section-header">
              <h2>Embedding 向量化</h2>
              <p class="section-desc">将文本转为向量，用于语义检索</p>
            </div>

            <div class="warning-banner">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" class="warning-icon">
                <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
              </svg>
              <div>
                <strong>请在首次使用前确定 Embedding 服务</strong>
                <p>切换 Embedding 服务后，所有已解析文档的向量数据将无法使用，需要删除全部项目后重新上传。请谨慎选择。</p>
              </div>
            </div>

            <div class="form-group">
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="draft.embedding_source" value="bailian" />
                  <span>使用百炼模型（云服务，需确保账户有足够余额）</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="draft.embedding_source" value="local" />
                  <span>本地服务（sentence-transformers，需要 GPU）</span>
                </label>
              </div>
            </div>


            <template v-if="draft.embedding_source === 'bailian'">
              <div class="form-group">
                <label>模型名称</label>
                <input
                  v-model="draft.embedding_bailian_model"
                  placeholder="例如：text-embedding-v4、text-embedding-v2"
                  class="input"
                />
                <p class="field-hint">百炼 Embedding 模型，推荐 text-embedding-v4</p>
              </div>
            </template>


            <template v-if="draft.embedding_source === 'local'">
              <div class="form-group">
                <label>服务地址</label>
                <input
                  v-model="draft.embedding_base_url"
                  placeholder="例如：http://host.docker.internal:8001（Docker 模式）或 http://localhost:8001（本地裸跑）"
                  class="input"
                />
                <p class="field-hint">
                  本地 Embedding 服务地址，启动方式：cd services/embedding && python server.py。
                  Docker 部署时不能用 localhost（容器内 localhost 指容器自身），
                  Mac/Win 用 <code>host.docker.internal</code>，Linux 用宿主机内网 IP。
                </p>
              </div>
            </template>

            <div class="form-actions">
              <button class="btn-test" @click="testEmbedding" :disabled="testing.embedding">
                {{ testing.embedding ? '测试中...' : '测试连接' }}
              </button>
              <span v-if="testResult.embedding" class="test-result" :class="testResult.embedding.ok ? 'ok' : 'fail'">
                {{ testResult.embedding.msg }}
              </span>
              <button class="btn-save" @click="save('embedding')" :disabled="saving">
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </section>


          <section v-if="activeTab === 'mineru'" class="settings-section">
            <div class="section-header">
              <h2>MinerU PDF 解析</h2>
            </div>

            <div class="warning-banner">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" class="warning-icon">
                <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
              </svg>
              <div>
                <strong>必须配置 PDF 解析服务后才能上传 PDF 文档</strong>
                <p>本系统采用 MinerU 进行 Layout 感知解析（支持公式提取、表格结构化、页码保留）。未配置时上传 PDF 会失败，但 Word / 音频 / 文本笔记仍可正常使用。</p>
              </div>
            </div>

            <div class="form-group">
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="draft.mineru_source" value="api" />
                  <span>官方 API（<a href="https://mineru.net" target="_blank">mineru.net</a>）</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="draft.mineru_source" value="local" />
                  <span>本地服务（自部署 MinerU）</span>
                </label>
              </div>
            </div>

            <template v-if="draft.mineru_source === 'api'">
              <div class="form-group">
                <label>API Key</label>
                <div class="input-row">
                  <input
                    :type="showMineruKey ? 'text' : 'password'"
                    v-model="draft.mineru_api_key"
                    placeholder="your-mineru-api-key"
                    class="input"
                  />
                  <button class="btn-icon" @click="showMineruKey = !showMineruKey" title="显示/隐藏">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path v-if="showMineruKey" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                      <path v-else d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
                    </svg>
                  </button>
                </div>
              </div>
            </template>

            <template v-if="draft.mineru_source === 'local'">
              <div class="form-group">
                <label>服务地址</label>
                <input
                  v-model="draft.mineru_base_url"
                  placeholder="例如：http://host.docker.internal:8002（Docker 模式）或 http://localhost:8002（本地裸跑）"
                  class="input"
                />
                <p class="field-hint">
                  本地 MinerU 服务地址，启动方式：cd services/mineru && python server.py。
                  Docker 部署时不能用 localhost（容器内 localhost 指容器自身），
                  Mac/Win 用 <code>host.docker.internal</code>，Linux 用宿主机内网 IP。
                </p>
              </div>
            </template>

            <div class="form-actions">
              <button class="btn-test" @click="testMineru" :disabled="testing.mineru">
                {{ testing.mineru ? '测试中...' : '测试连接' }}
              </button>
              <span v-if="testResult.mineru" class="test-result" :class="testResult.mineru.ok ? 'ok' : 'fail'">
                {{ testResult.mineru.msg }}
              </span>
              <button class="btn-save" @click="save('mineru')" :disabled="saving">
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </section>


          <section v-if="activeTab === 'funasr'" class="settings-section">
            <div class="section-header">
              <h2>FunASR 语音转写</h2>
              <p class="section-desc">音频文件自动转文字，支持中文长音频</p>
            </div>
            <div class="coming-soon-placeholder">
              <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
              <p>该功能正在开发中，敬请期待</p>
            </div>
          </section>


          <section v-if="activeTab === 'websearch'" class="settings-section">
            <div class="section-header">
              <h2>联网搜索</h2>
              <p class="section-desc">
                配置博查 API Key 后即可启用联网搜索，让 AI 能够搜索互联网获取最新信息。
                <a href="https://open.bochaai.com/" target="_blank">前往博查控制台</a>
              </p>
            </div>

            <div class="form-group">
              <label>博查 API Key</label>
              <div class="input-row">
                <input
                  :type="showBochaKey ? 'text' : 'password'"
                  v-model="draft.bocha_api_key"
                  placeholder="sk-..."
                  class="input"
                />
                <button class="btn-icon" @click="showBochaKey = !showBochaKey" title="显示/隐藏">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path v-if="showBochaKey" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                    <path v-else d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
                  </svg>
                </button>
              </div>
              <p class="field-hint">在博查控制台获取 API Key，填写后自动启用联网搜索</p>
            </div>

            <div class="form-actions">
              <button class="btn-test" @click="testWebSearch" :disabled="testing.websearch">
                {{ testing.websearch ? '测试中...' : '测试连接' }}
              </button>
              <span v-if="testResult.websearch" class="test-result" :class="testResult.websearch.ok ? 'ok' : 'fail'">
                {{ testResult.websearch.msg }}
              </span>
              <button class="btn-save" @click="save('websearch')" :disabled="saving">
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </section>

        </template>


        <transition name="toast">
          <div v-if="toast.show" class="toast" :class="toast.type">
            {{ toast.msg }}
          </div>
        </transition>


        <transition name="modal">
          <div v-if="confirmDialog.show" class="modal-overlay" @click.self="confirmDialog.show = false">
            <div class="modal-card">
              <div class="modal-header">
                <svg viewBox="0 0 24 24" width="22" height="22" fill="#e65100">
                  <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
                </svg>
                <h3>确认切换 Embedding 服务</h3>
              </div>
              <div class="modal-body">
                <p>{{ confirmDialog.msg }}</p>
                <p class="modal-warn">请确认所有文件和结果都已保存后再进行切换。此操作不可撤销。</p>
              </div>
              <div class="modal-actions">
                <button class="btn-cancel" @click="confirmDialog.show = false">取消</button>
                <button class="btn-danger" @click="confirmForceSave">确认切换</button>
              </div>
            </div>
          </div>
        </transition>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getSettings, updateSettings, type SettingsMap } from '../services/api'
import { clearTokens, getDisplayUsername, getToken } from '../services/auth'
import BaseUrlHelpTooltip from '../components/common/BaseUrlHelpTooltip.vue'
import LanguageSwitcher from '../components/common/LanguageSwitcher.vue'

const router = useRouter()
const route = useRoute()
const displayUsername = computed(() => getDisplayUsername() || 'admin')

function logout() {
  clearTokens()
  router.push('/login')
}


const tabs = [
  {
    key: 'overview',
    label: '总览',
    icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>',
  },
  {
    key: 'bailian',
    label: '百炼',
    icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg>',
  },
  {
    key: 'llm',
    label: '大模型设置',
    icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 17.93V18a1 1 0 0 0-2 0v1.93A8 8 0 0 1 4.07 13H6a1 1 0 0 0 0-2H4.07A8 8 0 0 1 11 4.07V6a1 1 0 0 0 2 0V4.07A8 8 0 0 1 19.93 11H18a1 1 0 0 0 0 2h1.93A8 8 0 0 1 13 19.93z"/></svg>',
  },
  {
    key: 'embedding',
    label: 'Embedding',
    icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M4 8h4V4H4v4zm6 12h4v-4h-4v4zm-6 0h4v-4H4v4zm0-6h4v-4H4v4zm6 0h4v-4h-4v4zm6-10v4h4V4h-4zm-6 4h4V4h-4v4zm6 6h4v-4h-4v4zm0 6h4v-4h-4v4z"/></svg>',
  },
  {
    key: 'mineru',
    label: 'PDF 解析',
    icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm4 18H6V4h7v5h5v11z"/></svg>',
  },
  {
    key: 'funasr',
    label: '语音',
    icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 15c1.66 0 2.99-1.34 2.99-3L15 6c0-1.66-1.34-3-3-3S9 4.34 9 6v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 15 6.7 12H5c0 3.42 2.72 6.23 6 6.72V22h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/></svg>',
  },
  {
    key: 'websearch',
    label: '联网搜索',
    icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>',
  },
]

const validTabs = tabs.map(t => t.key)
const initialTab = validTabs.includes(route.query.tab as string) ? (route.query.tab as string) : 'overview'
const activeTab = ref(initialTab)


watch(activeTab, (tab) => {
  router.replace({ query: { ...route.query, tab } })
})

watch(() => route.query.tab, (tab) => {
  if (tab && validTabs.includes(tab as string) && tab !== activeTab.value) {
    activeTab.value = tab as string
  }
})


const loading = ref(true)
const saving = ref(false)
const draft = reactive<SettingsMap>({})
const saved = reactive<SettingsMap>({})

const showBailianKey = ref(false)
const showLlmKey = ref(false)
const showVlmKey = ref(false)
const showMineruKey = ref(false)
const showBochaKey = ref(false)

// 「节省计划」开关:开关状态由 easy_task_llm 是否非空驱动。
// 关闭 = 不设置 easy model(简单任务与主 LLM 共用模型),清空并立即持久化;
// 没有 easy_task_llm 时,后端 resolve 会回退到主 LLM。
const easyTaskEnabled = ref(false)
async function toggleEasyTask(on: boolean) {
  easyTaskEnabled.value = on
  if (on) return
  testResult.easytask = null
  const hadValue = !!(draft.easy_task_llm || saved.easy_task_llm)
  draft.easy_task_llm = ''
  if (hadValue) await save('easytask')  // 立即持久化「不设置」
}

const DEFAULT_SETTINGS: SettingsMap = {

  bailian_api_key: '',

  llm_source: '',
  llm_bailian_model: '',
  llm_api_key: '',
  llm_base_url: '',
  llm_model: '',
  llm_api_format: 'openai',
  easy_task_llm: '',

  vlm_source: '',
  vlm_bailian_model: '',
  vlm_api_key: '',
  vlm_base_url: '',
  vlm_model: '',

  embedding_source: 'bailian',
  embedding_bailian_model: '',
  embedding_model: '',
  embedding_api_key: '',
  embedding_base_url: '',

  mineru_source: 'api',
  mineru_base_url: '',
  mineru_api_key: '',

  funasr_base_url: '',

  bocha_api_key: '',
}


const overviewLlmReady = computed(() => {
  if (saved.llm_source === 'custom') return !!(saved.llm_api_key && saved.llm_model)
  return !!(saved.bailian_api_key && saved.llm_bailian_model)
})
const overviewVlmReady = computed(() => {
  if (saved.vlm_source === 'custom') return !!(saved.vlm_api_key && saved.vlm_model)
  return !!(saved.bailian_api_key && saved.vlm_bailian_model)
})
const overviewEmbeddingReady = computed(() => {
  if (saved.embedding_source === 'local') return !!saved.embedding_base_url
  return !!(saved.bailian_api_key && saved.embedding_bailian_model)
})
const overviewMineruReady = computed(() => {
  if (saved.mineru_source === 'local') return !!saved.mineru_base_url
  return !!saved.mineru_api_key
})

const testing = reactive({ llm: false, easytask: false, vlm: false, embedding: false, mineru: false, websearch: false })
const testResult = reactive<{
  llm: { ok: boolean; msg: string } | null
  easytask: { ok: boolean; msg: string } | null
  vlm: { ok: boolean; msg: string } | null
  embedding: { ok: boolean; msg: string } | null
  mineru: { ok: boolean; msg: string } | null
  websearch: { ok: boolean; msg: string } | null
}>({ llm: null, easytask: null, vlm: null, embedding: null, mineru: null, websearch: null })

const toast = reactive({ show: false, msg: '', type: 'success' as 'success' | 'error' })


const savedEmbeddingSource = ref('')
const confirmDialog = reactive({ show: false, msg: '' })


onMounted(async () => {
  try {
    const remote = await getSettings()
    savedEmbeddingSource.value = remote.embedding_source || ''
    Object.assign(saved, DEFAULT_SETTINGS, remote)
    Object.assign(draft, DEFAULT_SETTINGS, remote)
    easyTaskEnabled.value = !!(remote.easy_task_llm && remote.easy_task_llm.trim())
  } finally {
    loading.value = false
  }
})


const SECTION_KEYS: Record<string, (keyof SettingsMap)[]> = {
  bailian: ['bailian_api_key'],
  llm: ['llm_source', 'llm_bailian_model', 'llm_api_key', 'llm_base_url', 'llm_model', 'llm_api_format'],
  easytask: ['easy_task_llm'],
  vlm: ['vlm_source', 'vlm_bailian_model', 'vlm_api_key', 'vlm_base_url', 'vlm_model'],
  embedding: ['embedding_source', 'embedding_bailian_model', 'embedding_model', 'embedding_api_key', 'embedding_base_url'],
  mineru: ['mineru_source', 'mineru_base_url', 'mineru_api_key'],
  funasr: ['funasr_base_url'],
  websearch: ['bocha_api_key'],
}

async function save(section: string, force = false) {

  if (section === 'llm' && draft.llm_source === 'custom' && !draft.llm_base_url) {
    showToast('自定义 LLM 需要填写 Base URL', 'error')
    return
  }

  if (section === 'embedding' && !force) {
    const oldSource = savedEmbeddingSource.value
    const newSource = draft.embedding_source
    if (oldSource && newSource && oldSource !== newSource) {
      confirmDialog.msg = `你正在将 Embedding 服务从「${sourceLabel(oldSource)}」切换为「${sourceLabel(newSource)}」。切换后所有已解析文档的向量数据将全部失效，需要删除项目并重新上传文件。`
      confirmDialog.show = true
      return
    }
  }

  saving.value = true
  try {
    const keys = SECTION_KEYS[section] ?? []
    const payload: Partial<SettingsMap> = {}
    for (const k of keys) {
      payload[k] = draft[k]
    }
    const updated = await updateSettings(payload, force)
    Object.assign(saved, DEFAULT_SETTINGS, updated)
    Object.assign(draft, updated)
    savedEmbeddingSource.value = saved.embedding_source || ''
    showToast('已保存', 'success')
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (detail) {
      showToast(detail, 'error')
    } else {
      showToast('保存失败，请检查网络', 'error')
    }
  } finally {
    saving.value = false
  }
}

function sourceLabel(source: string): string {
  return { bailian: '百炼模型', local: '本地服务', custom: '自定义' }[source] || source
}

function apiFormatLabel(format?: string): string {
  return format === 'anthropic' ? 'Anthropic Messages' : 'OpenAI Chat'
}

function confirmForceSave() {
  confirmDialog.show = false
  save('embedding', true)
}


function authHeader() {
  return { Authorization: `Bearer ${getToken() ?? ''}` }
}

async function testLlm() {
  testing.llm = true
  testResult.llm = null
  try {

    let body: Record<string, string | undefined>
    if (draft.llm_source === 'custom') {
      if (!draft.llm_base_url) {
        testResult.llm = { ok: false, msg: '请填写 Base URL' }
        return
      }
      body = {
        source: 'custom',
        api_key: draft.llm_api_key,
        base_url: draft.llm_base_url,
        model: draft.llm_model,
        api_format: draft.llm_api_format || 'openai',
      }
    } else {
      // 传 source=bailian 让后端走百炼分支,不依赖 DB 里旧的 llm_source。
      // api_key 也一起带上 draft.bailian_api_key,覆盖可能还没保存的状态。
      body = {
        source: 'bailian',
        api_key: draft.bailian_api_key || undefined,
        model: draft.llm_bailian_model || undefined,
      }
    }
    const res = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/settings/test/llm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    testResult.llm = { ok: !!data.ok, msg: data.msg || (data.ok ? '连接成功' : '连接失败') }
  } catch {
    testResult.llm = { ok: false, msg: '无法连接' }
  } finally {
    testing.llm = false
  }
}

async function testEasyTask() {
  // 节省计划复用主 LLM 的 provider(key/url),只把模型名换成 easy_task_llm 来测试。
  testing.easytask = true
  testResult.easytask = null
  try {
    let body: Record<string, string | undefined>
    if (draft.llm_source === 'custom') {
      if (!draft.llm_base_url) {
        testResult.easytask = { ok: false, msg: '请填写 Base URL' }
        return
      }
      body = {
        source: 'custom',
        api_key: draft.llm_api_key,
        base_url: draft.llm_base_url,
        model: draft.easy_task_llm,
        api_format: draft.llm_api_format || 'openai',
      }
    } else {
      body = {
        source: 'bailian',
        api_key: draft.bailian_api_key || undefined,
        model: draft.easy_task_llm || undefined,
      }
    }
    const res = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/settings/test/easy-task-llm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    testResult.easytask = { ok: !!data.ok, msg: data.msg || (data.ok ? '连接成功' : '连接失败') }
  } catch {
    testResult.easytask = { ok: false, msg: '无法连接' }
  } finally {
    testing.easytask = false
  }
}

async function testVlm() {
  testing.vlm = true
  testResult.vlm = null
  try {

    let body: Record<string, string | undefined>
    if (draft.vlm_source === 'custom') {
      body = {
        source: 'custom',
        api_key: draft.vlm_api_key,
        base_url: draft.vlm_base_url,
        model: draft.vlm_model,
      }
    } else {
      body = {
        source: 'bailian',
        api_key: draft.bailian_api_key || undefined,
        model: draft.vlm_bailian_model || undefined,
      }
    }
    const res = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/settings/test/vlm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    testResult.vlm = { ok: !!data.ok, msg: data.msg || (data.ok ? '连接成功' : '连接失败') }
  } catch {
    testResult.vlm = { ok: false, msg: '无法连接' }
  } finally {
    testing.vlm = false
  }
}

async function testEmbedding() {
  testing.embedding = true
  testResult.embedding = null
  try {

    const body: Record<string, string | undefined> = {
      source: draft.embedding_source || undefined,
    }
    if (draft.embedding_source === 'bailian') {
      body.api_key = draft.bailian_api_key || undefined
      body.model = draft.embedding_bailian_model || undefined
    } else if (draft.embedding_source === 'local') {
      body.base_url = draft.embedding_base_url || undefined
      body.model = draft.embedding_model || undefined
    }
    const res = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/settings/test/embedding`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    testResult.embedding = { ok: !!data.ok, msg: data.msg || (data.ok ? '连接成功' : '连接失败') }
  } catch {
    testResult.embedding = { ok: false, msg: '无法连接' }
  } finally {
    testing.embedding = false
  }
}

async function testMineru() {
  testing.mineru = true
  testResult.mineru = null
  try {
    const payload: Record<string, string> = { source: draft.mineru_source || 'api' }
    if (draft.mineru_source === 'local') {
      payload.base_url = draft.mineru_base_url || ''
    } else {
      payload.api_key = draft.mineru_api_key || ''
    }

    const res = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/settings/test/mineru`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    testResult.mineru = { ok: !!data.ok, msg: data.msg || (data.ok ? '连接成功' : '连接失败') }
  } catch {
    testResult.mineru = { ok: false, msg: '无法连接' }
  } finally {
    testing.mineru = false
  }
}

async function testWebSearch() {
  testing.websearch = true
  testResult.websearch = null
  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/settings/test/web-search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify({ api_key: draft.bocha_api_key }),
    })
    const data = await res.json()
    testResult.websearch = { ok: !!data.ok, msg: data.msg || (data.ok ? '连接成功' : '连接失败') }
  } catch {
    testResult.websearch = { ok: false, msg: '无法连接' }
  } finally {
    testing.websearch = false
  }
}


function showToast(msg: string, type: 'success' | 'error') {
  toast.msg = msg
  toast.type = type
  toast.show = true
  setTimeout(() => { toast.show = false }, type === 'error' ? 5000 : 2500)
}
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f9f9f7;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}


.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 24px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e8e8e4;
  flex-shrink: 0;
}

.settings-header-left,
.settings-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.settings-header-left {
  min-width: 0;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #e0e0da;
  border-radius: 6px;
  background: transparent;
  color: #555;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-back:hover { background: #f0f0ec; }

.btn-header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid #e0e0da;
  border-radius: 6px;
  background: transparent;
  color: #555;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-header-icon:hover { background: #f0f0ec; }

.settings-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.user-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 13px;
  color: #666;
  cursor: default;
}

@media (max-width: 640px) {
  .settings-header {
    padding: 0 12px;
  }

  .settings-title {
    display: none;
  }

  .user-badge {
    padding: 6px 8px;
  }
}


.settings-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}


.settings-nav {
  width: 180px;
  flex-shrink: 0;
  padding: 16px 8px;
  background: #fff;
  border-right: 1px solid #e8e8e4;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #555;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.nav-item:hover { background: #f0f0ec; color: #1a1a1a; }
.nav-item.active { background: #1a1a1a; color: #fff; }

.nav-icon { display: flex; align-items: center; flex-shrink: 0; }


.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px 48px;
  position: relative;
}

.loading-state {
  color: #888;
  font-size: 14px;
}


.settings-section {
  max-width: 560px;
}

.section-header {
  margin-bottom: 28px;
}
.section-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 6px;
}
.section-desc {
  font-size: 13px;
  color: #888;
  margin: 0;
  line-height: 1.5;
}
.section-desc a {
  color: #1a73e8;
  text-decoration: none;
}
.section-desc a:hover {
  text-decoration: underline;
}


.section-divider {
  border: none;
  border-top: 1px solid #e8e8e4;
  margin: 32px 0;
}


.warning-banner {
  display: flex;
  gap: 10px;
  padding: 12px 14px;
  margin-bottom: 20px;
  background: #fff8e1;
  border: 1px solid #ffe082;
  border-radius: 8px;
  font-size: 13px;
  color: #5d4037;
  line-height: 1.5;
}
.warning-banner strong {
  display: block;
  margin-bottom: 2px;
  color: #e65100;
  font-size: 13px;
}
.warning-banner p {
  margin: 0;
  font-size: 12px;
  color: #795548;
}
.warning-icon {
  flex-shrink: 0;
  color: #f57c00;
  margin-top: 1px;
}

.radio-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  vertical-align: middle;
}
.radio-tag.recommend {
  background: #e8f5e9;
  color: #2e7d32;
}


.form-group {
  margin-bottom: 20px;
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 6px;
}
.label-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.label-row label {
  margin-bottom: 0;
}
.optional {
  font-weight: 400;
  color: #999;
}

.input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d8d8d2;
  border-radius: 6px;
  font-size: 13px;
  color: #1a1a1a;
  background: #fff;
  box-sizing: border-box;
  transition: border-color 0.15s;
  outline: none;
}
.input:focus { border-color: #1a1a1a; }
.input-sm { width: 100%; }

.input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.input-row .input { flex: 1; }

.btn-icon {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d8d8d2;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  color: #666;
  transition: background 0.15s;
}
.btn-icon:hover { background: #f0f0ec; }

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.radio-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #333;
  cursor: pointer;
}
.radio-item input { cursor: pointer; }
.radio-item a {
  color: #1a73e8;
  text-decoration: none;
}
.radio-item a:hover {
  text-decoration: underline;
}

.field-hint {
  font-size: 12px;
  color: #999;
  margin: 4px 0 0;
}


.easy-task-group {
  margin-top: 8px;
  padding: 14px 16px;
  background: #fafaf8;
  border: 1px solid #e8e8e4;
  border-radius: 8px;
}
.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 0;
  cursor: pointer;
}
.switch-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}
.switch-sub {
  font-size: 12px;
  font-weight: 400;
  color: #999;
  line-height: 1.5;
}
.switch {
  position: relative;
  flex-shrink: 0;
  width: 40px;
  height: 22px;
  border-radius: 999px;
  background: #d0d0cc;
  transition: background 0.15s;
}
.switch.on { background: #1a1a1a; }
.switch input {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}
.switch-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.15s;
}
.switch.on .switch-knob { transform: translateX(18px); }
.easy-task-input { margin-top: 12px; }
.easy-task-actions { margin-top: 16px; padding-top: 16px; }


.form-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid #e8e8e4;
}

.btn-save {
  margin-left: auto;  /* 始终固定在 .form-actions 最右侧 */
  padding: 8px 20px;
  background: #1a1a1a;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-save:hover:not(:disabled) { opacity: 0.85; }
.btn-save:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-test {
  padding: 8px 16px;
  background: transparent;
  color: #555;
  border: 1px solid #d8d8d2;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-test:hover:not(:disabled) { background: #f0f0ec; }
.btn-test:disabled { opacity: 0.5; cursor: not-allowed; }

.test-result {
  font-size: 13px;
  margin-right: auto;
}
.test-result.ok { color: #2e7d32; }
.test-result.fail { color: #c62828; }


.toast {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  z-index: 9999;
  pointer-events: none;
}
.toast.success { background: #1a1a1a; color: #fff; }
.toast.error   { background: #c62828; color: #fff; }

.toast-enter-active, .toast-leave-active { transition: opacity 0.25s, transform 0.25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }


.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}
.modal-card {
  background: #fff;
  border-radius: 12px;
  width: 440px;
  max-width: 90vw;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}
.modal-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 24px 0;
}
.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}
.modal-body {
  padding: 16px 24px 20px;
}
.modal-body p {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
  margin: 0 0 10px;
}
.modal-warn {
  font-weight: 500;
  color: #c62828 !important;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 0 24px 20px;
}
.btn-cancel {
  padding: 8px 18px;
  border: 1px solid #d8d8d2;
  border-radius: 6px;
  background: #fff;
  color: #555;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-cancel:hover { background: #f0f0ec; }
.btn-danger {
  padding: 8px 18px;
  border: none;
  border-radius: 6px;
  background: #c62828;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-danger:hover { opacity: 0.85; }

.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }


.overview-section {
  max-width: 680px;
}
.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.overview-card {
  padding: 16px;
  background: #fff;
  border: 1px solid #e8e8e4;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.overview-card:hover {
  border-color: #ccc;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.overview-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.overview-card-title {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a1a;
}
.overview-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 10px;
}
.overview-badge.configured {
  background: #e8f5e9;
  color: #2e7d32;
}
.overview-badge.unconfigured {
  background: #fff3e0;
  color: #e65100;
}
.overview-card-detail {
  font-size: 12px;
  color: #666;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.overview-card-detail.muted {
  color: #aaa;
}
.overview-card.disabled-card {
  opacity: 0.6;
  cursor: default;
}
.overview-card.disabled-card:hover {
  border-color: #e8e8e4;
  box-shadow: none;
}
.overview-badge.coming-soon {
  background: #f3f4f6;
  color: #9ca3af;
}


.coming-soon-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 24px;
  color: #ccc;
  text-align: center;
}
.coming-soon-placeholder p {
  font-size: 14px;
  color: #999;
  margin: 0;
}
</style>
