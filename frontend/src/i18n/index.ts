import { computed, ref, watch } from 'vue'

export const localeConfig = {
  zh: {
    htmlLang: 'zh-CN',
    modelOutputLanguage: 'Chinese',
    relativeNow: '刚刚',
    matchesBrowserLanguage: (language: string) => language.startsWith('zh'),
  },
  en: {
    htmlLang: 'en',
    modelOutputLanguage: 'English',
    relativeNow: 'Just now',
    matchesBrowserLanguage: () => true,
  },
} as const

export type Locale = keyof typeof localeConfig

const supportedLocales = Object.keys(localeConfig) as Locale[]

const STORAGE_KEY = 'local-notebook-locale'

const messages = {
  zh: {
    language: '语言',
    chinese: '中文',
    english: 'English',
  },
  en: {
    language: 'Language',
    chinese: '中文',
    english: 'English',
  },
} as const

const zhToEn: Record<string, string> = {
  '返回': 'Back',
  '返回首页': 'Back to home',
  '返回列表': 'Back to list',
  '设置': 'Settings',
  '语言': 'Language',
  '加载中...': 'Loading...',
  '还没有项目': 'No projects yet',
  '创建第一个项目': 'Create your first project',
  '新建项目': 'New project',
  '输入项目名称': 'Enter project name',
  '重命名项目': 'Rename project',
  '输入新的项目名称': 'Enter a new project name',
  '取消': 'Cancel',
  '创建': 'Create',
  '创建中...': 'Creating...',
  '保存': 'Save',
  '保存中...': 'Saving...',
  '删除': 'Delete',
  '重命名': 'Rename',
  '更多操作': 'More actions',
  '基础配置未完成': 'Basic configuration is incomplete',
  '创建项目前，请先完成以下配置：': 'Complete the following configuration before creating a project:',
  '稍后再说': 'Later',
  '前往设置': 'Go to settings',
  '刚刚': 'Just now',
  '今天': 'Today',
  '昨天': 'Yesterday',
  '前天': 'Two days ago',
  '三天内': 'Last 3 days',
  '七天内': 'Last 7 days',
  '最近7天': 'Last 7 days',
  '最近30天': 'Last 30 days',
  '一个月内': 'Last month',
  '更早': 'Older',
  '个来源': 'sources',
  '来源': 'Sources',
  '来源指南': 'Source guide',
  '添加来源': 'Add source',
  '上传来源': 'Upload sources',
  '上传来源即可开始使用': 'Upload sources to get started',
  '添加来源即可开始使用': 'Add sources to get started',
  '选择所有来源': 'Select all sources',
  '已保存的来源将显示在此处': 'Saved sources will appear here',
  '点击上方的"添加来源"即可添加 PDF、文本文件。': 'Click "Add source" above to add PDF or text files.',
  '展开来源面板': 'Expand sources panel',
  '展开工具箱面板': 'Expand toolbox panel',
  '收起面板': 'Collapse panel',
  '原文': 'Original',
  '原文视图': 'Original view',
  '解析': 'Parsed',
  '解析视图': 'Parsed view',
  '图片描述': 'Image description',
  '说话人': 'Speaker',
  '页码': 'Page',
  '跳转': 'Go',
  '新对话': 'New chat',
  '新建对话': 'New chat',
  '历史对话': 'Chat history',
  '暂无历史对话': 'No chat history',
  '删除对话': 'Delete chat',
  '确认删除': 'Confirm delete',
  '加载历史消息...': 'Loading earlier messages...',
  '向上滚动加载更多': 'Scroll up to load more',
  '更早的对话已压缩': 'Earlier chat has been compacted',
  '思考中...': 'Thinking...',
  '思考过程': 'Thought process',
  '正在列出文件...': 'Listing files...',
  '正在获取文件信息...': 'Getting file details...',
  '正在检索知识库...': 'Searching knowledge base...',
  '正在读取原文...': 'Reading source text...',
  '正在分析图片...': 'Analyzing images...',
  '正在执行': 'Running',
  '正在压缩对话历史...': 'Compacting chat history...',
  '小洛在此，您请讲': 'Xiaoluo is here. Go ahead.',
  '今天想聊点什么呀？': 'What would you like to talk about today?',
  '嗨，你来啦': 'Hi, you are here.',
  '有什么想问的？': 'What would you like to ask?',
  '发送': 'Send',
  '暂停': 'Stop',
  '滚动到底部': 'Scroll to bottom',
  '编辑': 'Edit',
  '复制': 'Copy',
  '复制纯文本': 'Copy plain text',
  '复制 Markdown': 'Copy Markdown',
  '复制成功': 'Copied',
  '复制失败': 'Copy failed',
  '已复制': 'Copied',
  '已复制为纯文本': 'Copied as plain text',
  '已复制为 Markdown': 'Copied as Markdown',
  '保存并重新生成': 'Save and regenerate',
  '重新生成': 'Regenerate',
  '重新生成（上次出错）': 'Regenerate (last attempt failed)',
  '仅最后一条消息可重新生成': 'Only the last message can be regenerated',
  '已压缩的消息不可编辑': 'Compacted messages cannot be edited',
  '已压缩的消息不可重新生成': 'Compacted messages cannot be regenerated',
  '下载对话': 'Download chat',
  '导出为 Word': 'Export as Word',
  '导出中...': 'Exporting...',
  '全选': 'Select all',
  '取消全选': 'Deselect all',
  '分析助手': 'Analysis assistant',
  '小洛': 'Xiaoluo',
  '小洛提供的内容未必准确，因此请仔细核查回答内容。': 'Xiaoluo may make mistakes, so please verify important answers.',
  '点击编辑项目名称': 'Click to edit project name',
  '点击编辑会话标题': 'Click to edit chat title',
  '配置总览': 'Configuration overview',
  '当前各服务的配置状态一览': 'Current configuration status for each service',
  '已配置': 'Configured',
  '未配置': 'Not configured',
  '点击前往配置': 'Click to configure',
  '自定义': 'Custom',
  '百炼': 'Bailian',
  '百炼 API Key': 'Bailian API Key',
  '未设置模型': 'Model not set',
  '未设置地址': 'URL not set',
  'Key 已填写': 'Key entered',
  '未配置 Key': 'Key not configured',
  'LLM 大模型': 'LLM',
  'VLM 视觉模型': 'VLM',
  'Embedding 向量化': 'Embedding',
  'MinerU PDF 解析': 'MinerU PDF parsing',
  'FunASR 语音转写': 'FunASR transcription',
  '联网搜索': 'Web search',
  '阿里云百炼': 'Alibaba Cloud Bailian',
  '前往百炼控制台': 'Open Bailian console',
  '前往博查控制台': 'Open Bocha console',
  '显示/隐藏': 'Show/hide',
  '填写阿里云百炼 API Key 作为通用凭证。各服务选择「使用百炼模型」时将自动使用此 Key。': 'Enter your Alibaba Cloud Bailian API Key as a shared credential. Services set to "Use Bailian model" will use this key automatically.',
  '此 Key 将作为 LLM、Embedding 等服务的默认凭证': 'This key is used as the default credential for LLM, Embedding, and related services.',
  '大模型设置': 'Model settings',
  'LLM 模型': 'LLM model',
  '用于智能问答的大语言模型': 'Large language model for Q&A',
  'VLM 模型': 'VLM model',
  '用于 PDF 图片分析的视觉语言模型': 'Vision-language model for PDF image analysis',
  '使用百炼模型': 'Use Bailian model',
  '自定义（OpenAI / Anthropic / DeepSeek / Ollama / 兼容接口）': 'Custom (OpenAI / Anthropic / DeepSeek / Ollama / compatible API)',
  '自定义（OpenAI / 兼容接口）': 'Custom (OpenAI / compatible API)',
  '模型名称': 'Model name',
  '例如：': 'e.g. ',
  'Docker 模式': 'Docker mode',
  '本地裸跑': 'local mode',
  '填写百炼平台支持的模型名称，需先在百炼控制台开通对应模型': 'Enter a model name supported by Bailian. Make sure the model is enabled in the Bailian console first.',
  '填写百炼平台支持的多模态模型名称': 'Enter a multimodal model name supported by Bailian.',
  '（可选）': '(optional)',
  '请求格式': 'Request format',
  'Base URL 填写提示': 'Base URL help',
  '填写规则': 'Rules',
  '只填服务根地址，不填最终 endpoint。': 'Enter the service base URL, not the final endpoint.',
  'OpenAI Chat 会请求 /chat/completions。': 'OpenAI Chat requests /chat/completions.',
  'Anthropic Messages 会请求 /v1/messages。': 'Anthropic Messages requests /v1/messages.',
  'FunASR 会请求 /health 和 /transcribe。': 'FunASR requests /health and /transcribe.',
  '常见例子': 'Examples',
  'DeepSeek OpenAI: https://api.deepseek.com': 'DeepSeek OpenAI: https://api.deepseek.com',
  'DeepSeek Anthropic: https://api.deepseek.com/anthropic': 'DeepSeek Anthropic: https://api.deepseek.com/anthropic',
  'Claude 官方: https://api.anthropic.com': 'Official Claude: https://api.anthropic.com',
  'NeoRouter Claude: https://api.neorouter.ai': 'NeoRouter Claude: https://api.neorouter.ai',
  '自定义 LLM 需要填写 Base URL': 'Custom LLM requires a Base URL',
  '请填写 Base URL': 'Enter a Base URL',
  '测试连接': 'Test connection',
  '测试中...': 'Testing...',
  '连接成功': 'Connected',
  '连接失败': 'Connection failed',
  '配置 easy task model': 'Configure easy task model',
  '节省计划 · 解析任务的摘要生成使用更便宜的模型，复用上方主模型的 Key 和地址，仅替换模型名': 'Economy mode · summaries during parsing use a cheaper model, reusing the main model API key and URL above; only the model name changes',
  '例如：deepseek-v4-flash': 'e.g. deepseek-v4-flash',
  '需与上方主模型为同一 provider（复用其 Key 和地址）。例如主模型配置为 deepseek-v4-pro 时，这里可填更便宜的 deepseek-v4-flash；具体模型名以该 provider 实际支持的为准。': 'Must use the same provider as the main model above (its API key and URL are reused). For example, when the main model is deepseek-v4-pro, you can use the cheaper deepseek-v4-flash here; use a model name your provider actually supports.',
  '无法连接': 'Cannot connect',
  '服务地址': 'Service URL',
  '本地服务': 'Local service',
  '官方 API': 'Official API',
  '博查 API': 'Bocha API',
  '博查 API Key': 'Bocha API Key',
  '在博查控制台获取 API Key，填写后自动启用联网搜索': 'Get an API Key from the Bocha console. Web search is enabled automatically after you enter it.',
  '总览': 'Overview',
  'PDF 解析': 'PDF parsing',
  '语音': 'Audio',
  '语音转写': 'Transcription',
  '密码': 'Password',
  '用户名': 'Username',
  '登录': 'Log in',
  '登录中...': 'Logging in...',
  '登录以继续': 'Log in to continue',
  '请输入用户名': 'Enter username',
  '请输入密码': 'Enter password',
  '登录失败': 'Login failed',
  '登录失败，请检查网络连接': 'Login failed. Check your network connection.',
  '处理中': 'Processing',
  '等待处理': 'Pending',
  '等待中': 'Pending',
  '就绪': 'Ready',
  '完成': 'Done',
  '失败': 'Failed',
  '上传失败': 'Upload failed',
  '正在上传...': 'Uploading...',
  '文件数量已达上限': 'File limit reached',
  '点击上传或将文件拖至此处': 'Click to upload or drag files here',
  '支持 pdf、docx、doc、epub、jpg、jpeg、png、wav、mp3、m4a': 'Supports pdf, docx, doc, epub, jpg, jpeg, png, wav, mp3, m4a',
  '粘贴文字': 'Paste text',
  '粘贴复制的文字': 'Paste copied text',
  '在下方粘贴复制的文字，即可将其作为来源上传。': 'Paste copied text below to upload it as a source.',
  '在此粘贴文字内容...': 'Paste text here...',
  '插入': 'Insert',
  '重命名文件': 'Rename file',
  '输入新的文件名': 'Enter a new file name',
  '确认切换 Embedding 服务': 'Confirm Embedding service switch',
  '确认切换': 'Confirm switch',
  '请确认所有文件和结果都已保存后再进行切换。此操作不可撤销。': 'Make sure all files and results are saved before switching. This action cannot be undone.',
  '将文本转为向量，用于语义检索': 'Convert text into vectors for semantic search',
  '使用百炼模型（云服务，需确保账户有足够余额）': 'Use Bailian model (cloud service; make sure your account has sufficient balance)',
  '本地服务（sentence-transformers，需要 GPU）': 'Local service (sentence-transformers, GPU required)',
  '百炼 Embedding 模型，推荐 text-embedding-v4': 'Bailian Embedding model. text-embedding-v4 is recommended.',
  '本地 Embedding 服务地址，启动方式：': 'Local Embedding service URL. Start it with: ',
  'Docker 部署时不能用 localhost（容器内 localhost 指容器自身），': 'Do not use localhost in Docker deployments (inside a container, localhost means the container itself). ',
  'Mac/Win 用': 'Use ',
  '，Linux 用宿主机内网 IP。': '; on Linux, use the host LAN IP.',
  'Linux 用宿主机内网 IP。': 'Use the host LAN IP on Linux.',
  '请在首次使用前确定 Embedding 服务': 'Choose the Embedding service before first use',
  '切换 Embedding 服务后，所有已解析文档的向量数据将无法使用，需要删除全部项目后重新上传。请谨慎选择。': 'After switching Embedding service, vectors for parsed documents become unusable. You must delete projects and upload files again.',
  '必须配置 PDF 解析服务后才能上传 PDF 文档': 'Configure a PDF parsing service before uploading PDFs',
  '本系统采用 MinerU 进行 Layout 感知解析（支持公式提取、表格结构化、页码保留）。未配置时上传 PDF 会失败，但 Word / 音频 / 文本笔记仍可正常使用。': 'This system uses MinerU for layout-aware parsing, including formula extraction, table structuring, and page preservation. PDF uploads fail when it is not configured, while Word, audio, and text notes still work normally.',
  '本地服务（自部署 MinerU）': 'Local service (self-hosted MinerU)',
  '本地 MinerU 服务地址，启动方式：': 'Local MinerU service URL. Start it with: ',
  '音频文件自动转文字，支持中文长音频': 'Automatically transcribe audio files, with support for long Chinese audio',
  '本地 FunASR 服务地址，启动方式：': 'Local FunASR service URL. Start it with: ',
  '配置博查 API Key 后即可启用联网搜索，让 AI 能够搜索互联网获取最新信息。': 'Configure a Bocha API key to enable web search for up-to-date information.',
  '此操作无法撤销。': 'This action cannot be undone.',
  '选择文件': 'Select files',
  '暂无可选文件': 'No selectable files',
  '方案名称': 'Plan name',
  '请输入方案名称（必填，不可重复）': 'Enter a plan name (required and unique)',
  '生成内容': 'Generated content',
  '内置 prompt': 'Built-in prompt',
  '补充要求（可选）': 'Additional requirements (optional)',
  '可补充输出风格、关注重点、长度要求等': 'Optionally add output style, focus areas, length requirements, and more',
  '自定义要求（可选）': 'Custom requirements (optional)',
  '开始生成': 'Generate',
  '生成结果': 'Generated result',
  '暂无生成结果': 'No generated results',
  '暂无内容': 'No content yet',
  '工作流': 'Workflow',
  '自定义工作流': 'Custom workflow',
  '正在生成标题': 'Generating title',
  '正在生成标题...': 'Generating title...',
  '标题生成后可重命名': 'You can rename it after the title is generated',
  '内容速读': 'Quick read',
  '核心详解': 'Core deep dive',
  '智能报告': 'Smart report',
  '研究简报': 'Research brief',
  '内容方案': 'Content plan',
  '设计简报': 'Design brief',
  '文档概览': 'Document overview',
  '传播方案': 'Communication plan',
  '一键生成': 'Generate',
  '一键生成研究简报': 'Generate research brief',
  '一键生成内容方案': 'Generate content plan',
  '一键生成设计简报': 'Generate design brief',
  '一键生成文档概览': 'Generate document overview',
  '一键生成传播方案': 'Generate communication plan',
  '生成研究简报': 'Generate research brief',
  '生成内容方案': 'Generate content plan',
  '根据文档与你的描述自动规划栏目并生成': 'Plan sections from your documents and description, then generate the report',
  '快速掌握材料主线与重点': 'Quickly grasp the main thread and key points',
  '系统拆解材料中的关键逻辑': 'Systematically unpack the key logic in the material',
  '适合先快速了解资料讲了什么、重点在哪里、后续该追问什么。': 'Best for quickly understanding what the sources say, where the key points are, and what to ask next.',
  '适合深入理解资料里的问题、论据、关系、分歧和可执行结论。': 'Best for deeply understanding the problems, arguments, relationships, disagreements, and actionable conclusions in the sources.',
  '可补充希望重点关注的人物、主题、章节或输出长度。': 'Optionally add people, themes, sections, or length requirements to focus on.',
  '可补充希望加深分析的方向、读者背景、输出风格或篇幅。': 'Optionally add analysis directions, audience background, output style, or length requirements.',
  '完全按你的要求规划和生成': 'Plan and generate fully from your instructions',
  '请先上传并处理文件': 'Upload and process files first',
  '点击上方按钮生成报告': 'Use the buttons above to generate a report',
  '上传来源后即可生成报告': 'Upload sources to generate a report',
  'AI 将根据所选文档与你的描述，自动规划本报告的栏目结构。': 'AI will plan the report sections from the selected documents and your description.',
  'AI 会把你的要求拆成多个环节，每个环节作为 workflow 中的一个 feature 生成。': 'AI will split your instructions into multiple stages, with each stage generated as one feature in the workflow.',
  '工作流名称（可选）': 'Workflow name (optional)',
  '不填写则由 AI 根据要求命名': 'Leave blank and AI will name it from your instructions',
  '工作流要求': 'Workflow instructions',
  '例如：请基于这些资料生成一份面向投资人的尽调报告，重点分析商业模式、增长证据、竞争格局和风险。': 'Example: Based on these materials, generate an investor-facing due diligence report focused on business model, growth evidence, competitive landscape, and risks.',
  '基于文档生成完整研究简报': 'Generate a complete research brief from documents',
  '基于文档生成内容方案': 'Generate a content plan from documents',
  '生成设计简报': 'Generate a design brief',
  '生成文档概览': 'Generate a document overview',
  '生成完整传播方案': 'Generate a complete communication plan',
  '包括研究主题、核心问题、背景分析、创新价值、实施方案等': 'Includes research topic, core questions, background analysis, innovation value, implementation plan, and more',
  '包括标题、简介、背景分析、实施方案、呈现要求等': 'Includes title, intro, background analysis, implementation plan, presentation requirements, and more',
  '包含视觉设计、排版要求、展示文案等呈现要求': 'Includes visual design, layout requirements, display copy, and related presentation requirements',
  '用于会议交流、成果发布等场景': 'For meeting discussions, result releases, and similar scenarios',
  '包含亮点分析、传播策略、时间规划等': 'Includes highlight analysis, communication strategy, schedule planning, and more',
  '选择文件后点击开始生成': 'Select files, then click Generate',
  '例如：更偏向学术风格，突出核心创新点': 'Example: use a more academic style and highlight the core innovations',
  '例如：强调受众画像，减少背景介绍': 'Example: emphasize audience profiles and reduce background context',
  '正在生成，请稍候': 'Generating, please wait',
  '正在重新生成，请稍候': 'Regenerating, please wait',
  '生成失败，请点击“重新生成”按钮重试': 'Generation failed. Click "Regenerate" to try again.',
  '规划中': 'Planning',
  '生成中': 'Generating',
  '取消中': 'Cancelling',
  '已完成': 'Completed',
  '已取消': 'Cancelled',
  '部分完成': 'Partially completed',
  '停止生成': 'Stop generation',
  '停止': 'Stop',
  '正在停止生成': 'Stopping generation',
  '已停止生成': 'Generation stopped',
  '停止生成失败，请稍后重试': 'Failed to stop generation. Try again later.',
  '目录': 'Contents',
  '目录导航': 'Contents navigation',
  '点击重命名': 'Click to rename',
  '导出为 Word 文档': 'Export as Word document',
  '导出成功': 'Exported successfully',
  '操作过于频繁，请稍后再试': 'Too many requests. Try again later.',
  '当前状态不支持导出': 'Export is not supported in the current state.',
  '导出失败，请稍后重试': 'Export failed. Try again later.',
  '抱歉，暂时无法定位该引用来源': 'Sorry, this citation source cannot be located.',
  '确定要重新生成该步骤吗？': 'Regenerate this step?',
  '该步骤': 'this step',
  '创建任务失败，请稍后重试': 'Failed to create the task. Try again later.',
  '状态获取失败，请刷新页面': 'Failed to get status. Refresh the page.',
  '生成完成': 'Generation completed',
  '部分内容生成完成': 'Some content was generated',
  '生成失败，请重试': 'Generation failed. Try again.',
  '网络连接不稳定，请刷新页面重试': 'The network connection is unstable. Refresh the page and try again.',
  '获取详情失败': 'Failed to load details',
  '该步骤不存在，无法重新生成': 'This step does not exist and cannot be regenerated.',
  '获取步骤配置失败，请稍后重试': 'Failed to load step configuration. Try again later.',
  '重新生成失败，请稍后重试': 'Regeneration failed. Try again later.',
  '确定要删除这个生成记录吗？': 'Delete this generated record?',
  '已删除': 'Deleted',
  '删除失败': 'Delete failed',
  '确认定稿': 'Confirm finalization',
  '确认将此工作流标记为“定稿”吗？\n\n定稿后内容将不可修改，且会作为后续生成的重要参考。': 'Mark this workflow as final?\n\nAfter finalization, the content cannot be edited and will be used as an important reference for later generation.',
  '已成功定稿': 'Finalized successfully',
  '定稿失败': 'Finalization failed',
  '工具箱': 'Toolbox',
  '快捷工具': 'Quick tools',
  '智能分析': 'Smart analysis',
  '功能开发中': 'Feature under development',
  '深度解析': 'Deep analysis',
  '数据洞察': 'Data insights',
  '智能提取': 'Smart extraction',
  '内容分析': 'Content analysis',
  '综合报告': 'Comprehensive report',
  '知识图谱': 'Knowledge graph',
  '音频概览': 'Audio overview',
  '视频概览': 'Video overview',
  '思维导图': 'Mind map',
  '报告': 'Report',
  '闪卡': 'Flashcards',
  '测验': 'Quiz',
  '时间线': 'Timeline',
  '摘要': 'Summary',
  '要点': 'Key points',
  '笔记': 'Notes',
  '开发中': 'under development',
  '喜欢（即将推出）': 'Like (coming soon)',
  '不喜欢（即将推出）': 'Dislike (coming soon)',
  '文生图': 'Text to image',
  '图生图': 'Image to image',
  '文生视频': 'Text to video',
  '图生视频': 'Image to video',
  '首尾帧视频': 'Start/end frame video',
  '参考生视频': 'Reference to video',
  '视频生成': 'Video generation',
  '图片生成通常需要 30-90 秒，请耐心等待': 'Image generation usually takes 30-90 seconds.',
  '视频生成通常需要 1-5 分钟，请耐心等待': 'Video generation usually takes 1-5 minutes.',
  '选择图片': 'Select images',
  '暂无可用的图片文件': 'No image files available',
  '请先上传 jpg、png 格式的图片': 'Upload jpg or png images first',
  '请先上传 jpg、png 或 webp 格式的图片': 'Upload jpg, png, or webp images first',
  '添加背景音乐': 'Add background music',
  '视频时长': 'Duration',
  '画面比例': 'Aspect ratio',
  '分辨率': 'Resolution',
  '输出比例': 'Aspect ratio',
  '修改要求': 'Edit instructions',
  '显示修改对比': 'Show diff',
  '下载图片': 'Download image',
  '关闭': 'Close',
  '确定': 'OK',
}

const reverseEnToZh = Object.fromEntries(
  Object.entries(zhToEn).map(([zh, en]) => [en, zh]),
) as Record<string, string>

interface LocalizedValueRecord {
  source: string
  localized: string
}

const textNodeValues = new WeakMap<Node, LocalizedValueRecord>()
const attributeValues = new WeakMap<Element, Map<string, LocalizedValueRecord>>()

function isSupportedLocale(value: string | null): value is Locale {
  return Boolean(value && supportedLocales.includes(value as Locale))
}

function detectBrowserLocale(browserLanguage: string): Locale {
  const normalized = browserLanguage.toLowerCase()
  return supportedLocales.find((item) => localeConfig[item].matchesBrowserLanguage(normalized)) || 'en'
}

function getInitialLocale(): Locale {
  if (typeof window === 'undefined') return 'zh'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (isSupportedLocale(stored)) return stored
  return detectBrowserLocale(window.navigator.language)
}

export const locale = ref<Locale>(getInitialLocale())

export const isEnglish = computed(() => locale.value === 'en')

export function setLocale(nextLocale: Locale) {
  locale.value = nextLocale
}

export function getModelOutputLanguage(targetLocale: Locale = locale.value): string {
  return localeConfig[targetLocale].modelOutputLanguage
}

export function t(key: keyof typeof messages.zh): string {
  return messages[locale.value][key]
}

function replaceWithDictionary(text: string, dictionary: Record<string, string>) {
  let output = text
  const entries = Object.entries(dictionary).sort((a, b) => b[0].length - a[0].length)
  for (const [source, target] of entries) {
    output = output.split(source).join(target)
  }
  return output
}

export function translateText(text: string, targetLocale: Locale = locale.value): string {
  if (!text.trim()) return text

  if (targetLocale === 'zh') {
    return replaceWithDictionary(text, reverseEnToZh)
  }

  let output = text
  output = output.replace(/第\s*(\d+)\s*\/\s*(\d+)\s*页/g, 'Page $1 / $2')
  output = output.replace(/第\s*(\d+)\s*页/g, 'Page $1')
  output = output.replace(/已选择\s*(\d+)\/(\d+)\s*张/g, 'Selected $1/$2 images')
  output = output.replace(/已选中\s*(\d+)\s*项/g, '$1 selected')
  output = output.replace(/1\s*个文件/g, '1 file')
  output = output.replace(/1\s*个来源文件/g, '1 source file')
  output = output.replace(/1\s*个来源/g, '1 source')
  output = output.replace(/(\d+)\s*个文件/g, '$1 files')
  output = output.replace(/(\d+)\s*个来源文件/g, '$1 source files')
  output = output.replace(/(\d+)\s*个来源/g, '$1 sources')
  output = output.replace(/(\d+)\s*秒/g, '$1s')
  output = output.replace(/(\d+)\s*分钟前/g, '$1 minutes ago')
  output = output.replace(/(\d+)\s*小时前/g, '$1 hours ago')
  output = output.replace(/(\d+)\s*天前/g, '$1 days ago')
  output = output.replace(/(\d+)\s*个月前/g, '$1 months ago')
  output = output.replace(/(\d+)年(\d+)月(\d+)日/g, '$1-$2-$3')
  output = replaceWithDictionary(output, zhToEn)
  return output
}

function shouldSkipNode(node: Node) {
  const parent = node.parentElement
  if (!parent) return true
  const tagName = parent.tagName.toLowerCase()
  if (['script', 'style', 'code', 'pre', 'textarea'].includes(tagName)) return true

  return Boolean(parent.closest([
    '.assistant-content',
    '.user-message-content',
    '.preview-content',
    '.preview-file-name',
    '.image-description-content',
    '.card-title',
    '.card-summary',
    '.tooltip-content',
    '.project-title',
    '.source-name',
    '.source-status-reason',
    '.upload-file-name',
    '.table-caption',
    '.table-content',
    '.table-footnote',
    '.test-result',
    '.markdown-body',
    '.workflow-detail-panel .panel-title',
    '.workflow-item-name',
    '.feature-config-title',
    '.feature-section-title',
    '.toc-item',
    '.feature-text',
    '.feature-table',
    '.feature-image figcaption',
    '.feature-video figcaption',
    '.feature-image-group figcaption',
  ].join(',')))
}

function resolveSourceValue(
  record: LocalizedValueRecord | undefined,
  currentValue: string,
) {
  if (!record) return currentValue
  return currentValue === record.localized ? record.source : currentValue
}

function getAttributeRecords(element: Element) {
  let records = attributeValues.get(element)
  if (!records) {
    records = new Map()
    attributeValues.set(element, records)
  }
  return records
}

function localizeNode(node: Node) {
  if (node.nodeType === Node.TEXT_NODE) {
    if (shouldSkipNode(node)) return
    const currentValue = node.textContent || ''
    const sourceValue = resolveSourceValue(textNodeValues.get(node), currentValue)
    const translated = translateText(sourceValue)

    textNodeValues.set(node, { source: sourceValue, localized: translated })
    if (translated !== currentValue) node.textContent = translated
    return
  }

  if (node.nodeType !== Node.ELEMENT_NODE) return
  const element = node as HTMLElement
  if (['SCRIPT', 'STYLE', 'CODE', 'PRE'].includes(element.tagName)) return
  if (element.matches([
    '.assistant-content',
    '.user-message-content',
    '.preview-content',
    '.preview-file-name',
    '.image-description-content',
    '.card-title',
    '.card-summary',
    '.tooltip-content',
    '.project-title',
    '.source-name',
    '.source-status-reason',
    '.upload-file-name',
    '.table-caption',
    '.table-content',
    '.table-footnote',
    '.test-result',
    '.markdown-body',
    '.workflow-detail-panel .panel-title',
    '.workflow-item-name',
    '.feature-config-title',
    '.feature-section-title',
    '.toc-item',
    '.feature-text',
    '.feature-table',
    '.feature-image figcaption',
    '.feature-video figcaption',
    '.feature-image-group figcaption',
  ].join(','))) return

  for (const attribute of ['title', 'placeholder', 'aria-label', 'data-tooltip']) {
    const value = element.getAttribute(attribute)
    if (!value) continue

    const records = getAttributeRecords(element)
    const sourceValue = resolveSourceValue(records.get(attribute), value)
    const translated = translateText(sourceValue)

    records.set(attribute, { source: sourceValue, localized: translated })
    if (translated !== value) element.setAttribute(attribute, translated)
  }

  for (const child of Array.from(element.childNodes)) {
    localizeNode(child)
  }
}

export interface DomI18nController {
  refresh: () => void
  stop: () => void
}

export function installDomI18n(root: ParentNode = document.body): DomI18nController {
  let isLocalizing = false
  let pendingApplyTimer: number | null = null
  let releaseTimer: number | null = null

  const releaseLocalizingSoon = () => {
    if (releaseTimer !== null) {
      window.clearTimeout(releaseTimer)
    }

    releaseTimer = window.setTimeout(() => {
      releaseTimer = null
      isLocalizing = false
    }, 0)
  }

  const apply = () => {
    if (pendingApplyTimer !== null) {
      window.clearTimeout(pendingApplyTimer)
      pendingApplyTimer = null
    }

    isLocalizing = true
    document.documentElement.lang = localeConfig[locale.value].htmlLang
    localizeNode(root as Node)
    releaseLocalizingSoon()
  }

  const scheduleApply = (delay = 0) => {
    if (pendingApplyTimer !== null) {
      window.clearTimeout(pendingApplyTimer)
    }

    pendingApplyTimer = window.setTimeout(() => {
      pendingApplyTimer = null
      apply()
    }, delay)
  }

  const observer = new MutationObserver(() => {
    if (isLocalizing) return
    scheduleApply()
  })

  const handleVisibilityChange = () => {
    if (!document.hidden) {
      scheduleApply()
    }
  }

  const handlePageShow = () => scheduleApply()
  const handleFocus = () => scheduleApply()

  observer.observe(root, {
    subtree: true,
    childList: true,
    characterData: true,
    attributes: true,
    attributeFilter: ['title', 'placeholder', 'aria-label', 'data-tooltip'],
  })

  document.addEventListener('visibilitychange', handleVisibilityChange)
  window.addEventListener('pageshow', handlePageShow)
  window.addEventListener('focus', handleFocus)

  const stop = watch(locale, () => {
    window.localStorage.setItem(STORAGE_KEY, locale.value)
    apply()
  }, { immediate: true })

  return {
    refresh: apply,
    stop: () => {
      stop()
      if (pendingApplyTimer !== null) {
        window.clearTimeout(pendingApplyTimer)
      }
      if (releaseTimer !== null) {
        window.clearTimeout(releaseTimer)
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('pageshow', handlePageShow)
      window.removeEventListener('focus', handleFocus)
      observer.disconnect()
    },
  }
}
