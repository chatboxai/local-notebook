<template>
  <Teleport to="body">
    <div v-if="visible" class="workflow-config-overlay" @click.self="handleClose">
      <div class="workflow-config-modal">
        <div class="workflow-config-header">
          <h3>{{ modalHeading }}</h3>
          <button class="workflow-config-close" @click="handleClose" :aria-label="t('ui.close')">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        <div class="workflow-config-content">
          
          <div class="workflow-config-files">
            <div class="files-header" @click="toggleSelectAll">
              <span class="files-title">{{ t('ui.selectFiles') }}</span>
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
                {{ t('ui.noSelectableFiles') }}
              </div>
            </div>
          </div>

          
          <div class="workflow-config-body">
            <div class="workflow-info">
              <div class="workflow-icon" :class="workflowIconClass">
                <svg v-if="presetKey === 'quick_read'" viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M4 4h16v2H4V4zm0 4h10v2H4V8zm0 4h16v2H4v-2zm0 4h10v2H4v-2z"/>
                </svg>
                <svg v-else-if="presetKey === 'deep_dive'" viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M9 3h6l1 2h4a1 1 0 0 1 1 1v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a1 1 0 0 1 1-1h4l1-2zm1.24 2-.5 1H5v13h14V7h-4.74l-.5-1h-3.52zM7 10h10v2H7v-2zm0 4h7v2H7v-2z"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 21v-7"/>
                  <path d="M4 10V3"/>
                  <path d="M12 21v-9"/>
                  <path d="M12 8V3"/>
                  <path d="M20 21v-5"/>
                  <path d="M20 12V3"/>
                  <path d="M2 14h4"/>
                  <path d="M10 8h4"/>
                  <path d="M18 16h4"/>
                </svg>
              </div>
              <div class="workflow-desc">
                <p class="workflow-desc-title">{{ workflowDescription }}</p>
                <p class="workflow-desc-hint">{{ workflowHint }}</p>
              </div>
            </div>
            <div class="workflow-title-input">
              <p class="steps-title">{{ t('ui.workflowNameOptional') }}</p>
              <input
                v-model="localTitle"
                class="title-input"
                :placeholder="t('ui.leaveBlankAndAiWillNameItFrom')"
                maxlength="100"
              />
            </div>
            <div v-if="hasBuiltinPrompt" class="workflow-preset-prompt">
              <p class="steps-title">{{ t('ui.builtInPrompt') }}</p>
              <textarea
                class="prompt-input preset-prompt-input"
                :value="builtinPrompt"
                rows="5"
                readonly
              ></textarea>
            </div>
            <div class="workflow-prompt">
              <p class="steps-title">
                {{ promptLabel }}
                <span v-if="!hasBuiltinPrompt" class="required">*</span>
              </p>
              <textarea
                v-model="localPrompt"
                class="prompt-input"
                rows="4"
                :placeholder="promptPlaceholderText"
              ></textarea>
            </div>
          </div>
        </div>
        <div class="workflow-config-footer">
          <button class="workflow-config-btn cancel" @click="handleClose">{{ t('ui.cancel') }}</button>
          <button class="workflow-config-btn confirm" :disabled="!canConfirm" @click="handleConfirm">{{ t('ui.generate') }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { t } from '../../i18n'

interface FileItem {
  id: string
  file_name: string
  file_type: string
  status: string
}

const props = defineProps<{
  visible: boolean
  modalTitle?: string
  description?: string
  hint?: string
  builtinPrompt?: string
  promptPlaceholder?: string
  presetKey?: 'quick_read' | 'deep_dive' | 'custom'
  files?: FileItem[]
  selectedFileIds?: string[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', title: string, prompt: string, fileIds: string[]): void
}>()

const localSelectedIds = ref<string[]>([])
const localPrompt = ref('')
const localTitle = ref('')

const builtinPrompt = computed(() => (props.builtinPrompt || '').trim())
const hasBuiltinPrompt = computed(() => builtinPrompt.value.length > 0)
const presetKey = computed(() => props.presetKey || 'custom')
const workflowIconClass = computed(() => `source-${presetKey.value.replace('_', '-')}`)
const modalHeading = computed(() => props.modalTitle || t('ui.customWorkflow'))
const promptLabel = computed(() => hasBuiltinPrompt.value ? t('ui.additionalRequirementsOptional') : t('ui.workflowInstructions'))
const promptPlaceholderText = computed(() => {
  if (props.promptPlaceholder) return props.promptPlaceholder
  return hasBuiltinPrompt.value
    ? t('ui.optionallyAddOutputStyleFocusAreasLengthRequirements')
    : t('ui.exampleBasedOnTheseMaterialsGenerateAnInvestor')
})


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
  if (!canConfirm.value) {
    return
  }
  emit('confirm', localTitle.value.trim(), localPrompt.value.trim(), localSelectedIds.value)
}
const AUDIO_TYPES = ['wav', 'mp3', 'm4a']

const IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'webp']


const workflowDescription = computed(() => {
  return props.description || t('ui.planAndGenerateFullyFromYourInstructions')
})


const workflowHint = computed(() => {
  return props.hint || t('ui.aiWillSplitYourInstructionsIntoMultipleStages')
})


const canConfirm = computed(() => {
  return localSelectedIds.value.length > 0 && (hasBuiltinPrompt.value || localPrompt.value.trim().length > 0)
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

.workflow-icon.source-quick-read {
  background: linear-gradient(135deg, rgba(147, 197, 253, 0.5) 0%, rgba(96, 165, 250, 0.5) 100%);
  color: #1d4ed8;
}

.workflow-icon.source-deep-dive {
  background: linear-gradient(135deg, rgba(199, 210, 254, 0.5) 0%, rgba(165, 180, 252, 0.5) 100%);
  color: #4338ca;
}

.workflow-icon.source-custom {
  background:
    linear-gradient(135deg, rgba(20, 184, 166, 0.28) 0%, rgba(250, 204, 21, 0.34) 100%),
    radial-gradient(circle at 85% 12%, rgba(255, 255, 255, 0.68) 0%, rgba(255, 255, 255, 0) 34%);
  border: 1px solid rgba(13, 148, 136, 0.28);
  color: #0f766e;
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

.workflow-preset-prompt {
  display: flex;
  flex-direction: column;
  min-height: 150px;
}

.workflow-prompt {
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

.preset-prompt-input {
  min-height: 150px;
  color: var(--text-secondary);
  background: var(--bg-main);
}

.prompt-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
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
