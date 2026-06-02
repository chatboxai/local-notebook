<template>
  <Teleport to="body">
    <div v-if="visible" class="workflow-config-overlay" @click.self="handleClose">
      <div class="workflow-config-modal">
        <div class="workflow-config-header">
          <h3>{{ workflowTitle }}</h3>
          <button class="workflow-config-close" @click="handleClose">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        <div class="workflow-config-content">
          
          <div class="workflow-config-files">
            <div class="files-header" @click="toggleSelectAll">
              <span class="files-title">选择文件</span>
              <div class="files-header-right">
                <span class="files-count">{{ localSelectedIds.length }}/{{ selectableFiles.length }}</span>
                <div class="select-all-checkbox" :class="{ checked: isAllSelected, indeterminate: isPartialSelected }">
                  <svg v-if="isAllSelected" viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                  <svg v-else-if="isPartialSelected" viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                    <path d="M19 13H5v-2h14v2z"/>
                  </svg>
                </div>
              </div>
            </div>
            <div class="files-list">
              <div
                v-for="file in selectableFiles"
                :key="file.id"
                class="file-item"
                :class="{ selected: localSelectedIds.includes(file.id) }"
                @click="toggleFileSelection(file.id)"
              >
                <div class="file-icon" :class="getFileIconClass(file.file_type)">
                  
                  <svg v-if="isAudioType(file.file_type)" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
                  </svg>
                  
                  <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
                  </svg>
                </div>
                <span class="file-name">{{ file.file_name }}</span>
                <div class="file-checkbox" :class="{ checked: localSelectedIds.includes(file.id) }">
                  <svg v-if="localSelectedIds.includes(file.id)" viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                </div>
              </div>
              <div v-if="selectableFiles.length === 0" class="files-empty">
                暂无可选文件
              </div>
            </div>
          </div>

          
          <div class="workflow-config-body">
            <div class="workflow-info">
              <div class="workflow-icon" :class="workflowType">
                
                <svg v-if="workflowType === 'research_brief'" viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7zm2.85 11.1l-.85.6V16h-4v-2.3l-.85-.6A4.997 4.997 0 0 1 7 9c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.63-.8 3.16-2.15 4.1z"/>
                </svg>
                
                <svg v-else-if="workflowType === 'content_plan'" viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/>
                </svg>
                
                <svg v-else-if="workflowType === 'design_brief'" viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zM7 17h7v-2H7v2zm0-4h10v-2H7v2zm0-4h10V7H7v2z"/>
                </svg>
                
                <svg v-else-if="workflowType === 'overview_brief'" viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>
                </svg>
                
                <svg v-else-if="workflowType === 'communication_plan'" viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M18 11v2h4v-2h-4zm-2 6.61c.96.71 2.21 1.65 3.2 2.39.4-.53.8-1.07 1.2-1.6-.99-.74-2.24-1.68-3.2-2.4-.4.54-.8 1.08-1.2 1.61zM20.4 5.6c-.4-.53-.8-1.07-1.2-1.6-.99.74-2.24 1.68-3.2 2.4.4.53.8 1.07 1.2 1.6.96-.72 2.21-1.65 3.2-2.4zM4 9c-1.1 0-2 .9-2 2v2c0 1.1.9 2 2 2h1v4h2v-4h1l5 3V6L8 9H4zm11.5 3c0-1.33-.58-2.53-1.5-3.35v6.69c.92-.81 1.5-2.01 1.5-3.34z"/>
                </svg>
              </div>
              <div class="workflow-desc">
                <p class="workflow-desc-title">{{ workflowDescription }}</p>
                <p class="workflow-desc-hint">{{ workflowHint }}</p>
              </div>
            </div>
            <div class="workflow-title-input">
              <p class="steps-title">方案名称<span class="required">*</span></p>
              <input
                v-model="localTitle"
                class="title-input"
                placeholder="请输入方案名称（必填，不可重复）"
                maxlength="100"
              />
            </div>
            <div class="workflow-steps">
              <p class="steps-title">生成内容</p>
              <div class="steps-list">
                <div v-for="(step, index) in workflowSteps" :key="index" class="step-item" :data-tooltip="step">
                  <span class="step-number">{{ index + 1 }}</span>
                  <span class="step-name">{{ step }}</span>
                </div>
              </div>
            </div>
            <div class="workflow-prompt">
              <p class="steps-title">自定义要求（可选）</p>
              <textarea
                v-model="localPrompt"
                class="prompt-input"
                rows="3"
                placeholder="例如：更偏向学术风格，突出核心创新点"
              ></textarea>
            </div>
          </div>
        </div>
        <div class="workflow-config-footer">
          <button class="workflow-config-btn cancel" @click="handleClose">取消</button>
          <button class="workflow-config-btn confirm" :disabled="localSelectedIds.length === 0" @click="handleConfirm">开始生成</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

interface FileItem {
  id: string
  file_name: string
  file_type: string
  status: string
}

const props = defineProps<{
  visible: boolean
  workflowType: string
  workflowTitle: string
  files?: FileItem[]
  selectedFileIds?: string[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'close'): void
  (e: 'confirm', workflowType: string, title: string, prompt: string, fileIds: string[]): void
}>()

const localSelectedIds = ref<string[]>([])
const localPrompt = ref('')
const localTitle = ref('')


watch(() => props.visible, (newVal) => {
  if (newVal) {
    const selectableIds = new Set(selectableFiles.value.map(f => f.id))
    localSelectedIds.value = (props.selectedFileIds || []).filter(id => selectableIds.has(id))
    localPrompt.value = ''
    localTitle.value = ''
  } else {
    localSelectedIds.value = []
    localPrompt.value = ''
    localTitle.value = ''
  }
})

function handleClose() {
  emit('close')
}

function handleConfirm() {
  if (!localTitle.value.trim()) {
    
    
    return
  }
  emit('confirm', props.workflowType, localTitle.value.trim(), localPrompt.value.trim(), localSelectedIds.value)
}
const AUDIO_TYPES = ['wav', 'mp3', 'm4a', 'wma']

const IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'webp']


const workflowDescription = computed(() => {
  const descMap: Record<string, string> = {
    research_brief: '基于文档生成完整研究简报',
    content_plan: '基于文档生成内容方案',
    design_brief: '生成设计简报',
    overview_brief: '生成文档概览',
    communication_plan: '生成完整传播方案'
  }
  return descMap[props.workflowType] || '一键生成'
})


const workflowHint = computed(() => {
  const hintMap: Record<string, string> = {
    research_brief: '包括研究主题、核心问题、背景分析、创新价值、实施方案等',
    content_plan: '包括标题、简介、背景分析、实施方案、呈现要求等',
    design_brief: '包含视觉设计、排版要求、展示文案等呈现要求',
    overview_brief: '用于会议交流、成果发布等场景',
    communication_plan: '包含亮点分析、传播策略、时间规划等'
  }
  return hintMap[props.workflowType] || '选择文件后点击开始生成'
})


const workflowSteps = computed(() => {
  const stepsMap: Record<string, string[]> = {
    research_brief: [
      '研究主题', '建议标题', '研究性质/类别', '内容摘要', '负责人信息',
      '背景/领域分析', '成果与建议', '核心定位', '目标受众画像',
      '创新价值', '问题与解决', '推荐思路', '实施方案', '文档规格',
      '其他形式', '时间规划', '相关研究情况'
    ],
    content_plan: [
      '建议标题', '内容摘要', '负责人信息', '参与人员信息', '背景/领域分析',
      '成果与建议', '核心定位', '目标受众画像', '实施方案',
      '呈现要求', '时间规划', '传播文案', '亮点与传播'
    ],
    design_brief: [
      '建议标题', '内容摘要', '负责人信息', '参与人员信息', '成果与建议',
      '文档规格', '呈现要求', '其他形式', '时间规划',
      '视觉说明', '封面页'
    ],
    overview_brief: [
      '建议标题', '内容摘要', '负责人信息', '参与人员信息', '成果与建议',
      '核心定位', '目标受众画像', '文档规格', '视觉说明', '亮点与传播'
    ],
    communication_plan: [
      '项目名称', '建议标题', '内容摘要', '负责人信息', '参与人员信息',
      '背景/领域分析', '成果与建议', '核心定位', '目标受众画像',
      '推荐思路', '亮点与传播'
    ]
  }
  return stepsMap[props.workflowType] || []
})


const selectableFiles = computed(() => {
  if (!props.files) return []
  return props.files.filter(f =>
    f.status === 'ready' && !IMAGE_TYPES.includes(f.file_type?.toLowerCase() || '')
  )
})


function isAudioType(fileType: string): boolean {
  return AUDIO_TYPES.includes(fileType?.toLowerCase() || '')
}


function getFileIconClass(fileType: string): string {
  if (isAudioType(fileType)) return 'audio'
  return 'document'
}


function toggleFileSelection(fileId: string) {
  const index = localSelectedIds.value.indexOf(fileId)
  if (index === -1) {
    localSelectedIds.value.push(fileId)
  } else {
    localSelectedIds.value.splice(index, 1)
  }
}


const isAllSelected = computed(() => {
  return selectableFiles.value.length > 0 && localSelectedIds.value.length === selectableFiles.value.length
})


const isPartialSelected = computed(() => {
  return localSelectedIds.value.length > 0 && localSelectedIds.value.length < selectableFiles.value.length
})


function toggleSelectAll() {
  if (isAllSelected.value) {
    localSelectedIds.value = []
  } else {
    localSelectedIds.value = selectableFiles.value.map(f => f.id)
  }
}


</script>

<style scoped>
.workflow-config-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.workflow-config-modal {
  width: 960px;
  max-width: 95vw;
  height: 720px;
  max-height: 95vh;
  background: var(--bg-white);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.25s ease;
  display: flex;
  flex-direction: column;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.workflow-config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}

.workflow-config-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.workflow-config-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
}

.workflow-config-close:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.workflow-config-content {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}


.workflow-config-files {
  width: 280px;
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.files-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
}

.files-header:hover .select-all-checkbox {
  border-color: var(--primary-color);
}

.files-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.select-all-checkbox {
  width: 16px;
  height: 16px;
  border: 1.5px solid var(--border-color);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}

.select-all-checkbox.checked {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.select-all-checkbox.indeterminate {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.files-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.files-count {
  font-size: 12px;
  color: var(--text-tertiary);
}

.files-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.file-item:hover {
  background: var(--bg-hover);
}

.file-checkbox {
  width: 16px;
  height: 16px;
  border: 1.5px solid var(--border-color);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}

.file-checkbox.checked {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.file-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.file-icon.audio {
  color: #9333ea;
}

.file-icon.document {
  color: #1a73e8;
}

.file-name {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.files-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
}


.workflow-config-body {
  flex: 1;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.workflow-info {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.workflow-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  flex-shrink: 0;
}

.workflow-icon.research_brief {
  background: linear-gradient(135deg, rgba(192, 132, 252, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%);
  color: #7c3aed;
}

.workflow-icon.content_plan {
  background: linear-gradient(135deg, rgba(147, 197, 253, 0.3) 0%, rgba(96, 165, 250, 0.3) 100%);
  color: #1d4ed8;
}

.workflow-icon.design_brief {
  background: linear-gradient(135deg, rgba(94, 234, 212, 0.3) 0%, rgba(45, 212, 191, 0.3) 100%);
  color: #0d9488;
}

.workflow-icon.overview_brief {
  background: linear-gradient(135deg, rgba(134, 239, 172, 0.3) 0%, rgba(74, 222, 128, 0.3) 100%);
  color: #16a34a;
}

.workflow-icon.communication_plan {
  background: linear-gradient(135deg, rgba(255, 186, 125, 0.3) 0%, rgba(255, 154, 77, 0.3) 100%);
  color: #c2410c;
}

.workflow-desc {
  flex: 1;
}

.workflow-desc-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 6px 0;
}

.workflow-desc-hint {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
}

.steps-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
  flex-shrink: 0;
}

.workflow-steps {
  
  display: flex;
  flex-direction: column;
}

.steps-list {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-primary);
  position: relative;
  min-width: 0;
}


.step-item[data-tooltip]:hover::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 100;
  margin-bottom: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.step-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}


.workflow-prompt {
  margin-top: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.prompt-input {
  width: 100%;
  resize: none;
  flex: 1;
  min-height: 120px;
  padding: 10px 12px;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-primary);
  background: var(--bg-white);
}
.prompt-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.step-number {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-name {
  font-size: 13px;
  color: var(--text-primary);
}

.workflow-config-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-light);
  flex-shrink: 0;
}

.workflow-config-btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: none;
}

.workflow-config-btn.cancel {
  background: var(--bg-main);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.workflow-config-btn.cancel:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.workflow-config-btn.confirm {
  background: var(--primary-color);
  color: white;
}

.workflow-config-btn.confirm:hover:not(:disabled) {
  background: var(--primary-hover);
}

.workflow-config-btn.confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.workflow-title-input {
  margin-bottom: 4px;
  flex-shrink: 0;
}

.title-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  font-size: 14px;
  height: 42px;
  color: var(--text-primary);
  background: var(--bg-white);
  transition: all 0.2s;
}

.title-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.required {
  color: #ef4444;
  margin-left: 4px;
  font-weight: bold;
}
</style>
