<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="feature-config-overlay" @click.self="handleCancel">
        <div class="feature-config-modal">
          <div class="feature-config-header">
            <h3 class="feature-config-title">{{ title }}</h3>
            <button class="feature-config-close" @click="handleCancel" aria-label="关闭">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>
          <div class="feature-config-content">
            <div class="feature-config-files">
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
            <div class="feature-config-body">
              <p v-if="message" class="feature-config-message">{{ message }}</p>
              <div class="feature-config-section">
                <p class="section-title">自定义要求（可选）</p>
                <textarea
                  v-model="localPrompt"
                  class="prompt-input"
                  rows="3"
                  placeholder="例如：强调受众画像，减少背景介绍"
                ></textarea>
              </div>
            </div>
          </div>
          <div class="feature-config-actions">
            <button class="feature-config-btn cancel" @click="handleCancel">
              {{ cancelText }}
            </button>
            <button class="feature-config-btn confirm" @click="handleConfirm">
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface FileItem {
  id: string
  file_name: string
  file_type: string
  status: string
}

const props = defineProps<{
  visible: boolean
  title: string
  message?: string
  files?: FileItem[]
  selectedFileIds?: string[]
  initialPrompt?: string
  confirmText?: string
  cancelText?: string
}>()

const emit = defineEmits<{
  (e: 'confirm', prompt: string, fileIds: string[]): void
  (e: 'cancel'): void
  (e: 'update:visible', value: boolean): void
}>()

const AUDIO_TYPES = ['wav', 'mp3', 'm4a', 'wma']
const IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'webp']
const localPrompt = ref('')
const localSelectedIds = ref<string[]>([])

const selectableFiles = computed(() => {
  if (!props.files) return []
  return props.files.filter(f =>
    f.status === 'ready' && !IMAGE_TYPES.includes(f.file_type?.toLowerCase() || '')
  )
})

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

function toggleFileSelection(fileId: string) {
  const index = localSelectedIds.value.indexOf(fileId)
  if (index === -1) {
    localSelectedIds.value.push(fileId)
  } else {
    localSelectedIds.value.splice(index, 1)
  }
}

function isAudioType(fileType: string): boolean {
  return AUDIO_TYPES.includes(fileType?.toLowerCase() || '')
}

function getFileIconClass(fileType: string): string {
  if (isAudioType(fileType)) return 'audio'
  return 'document'
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    const selectableIds = new Set(selectableFiles.value.map(f => f.id))
    localSelectedIds.value = (props.selectedFileIds || []).filter(id => selectableIds.has(id))
    localPrompt.value = props.initialPrompt || ''
  } else {
    localSelectedIds.value = []
    localPrompt.value = ''
  }
})

function handleConfirm() {
  emit('confirm', localPrompt.value.trim(), localSelectedIds.value)
  emit('update:visible', false)
}

function handleCancel() {
  emit('cancel')
  emit('update:visible', false)
}
</script>

<style scoped>
.feature-config-overlay {
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
  backdrop-filter: blur(2px);
}

.feature-config-modal {
  width: 760px;
  max-width: 92vw;
  height: 515px;
  max-height: 92vh;
  background: var(--bg-white);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.feature-config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}

.feature-config-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.feature-config-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--text-tertiary);
  border-radius: 50%;
  transition: all 0.15s;
}

.feature-config-close:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.feature-config-content {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 16px 20px;
}

.feature-config-files {
  width: 240px;
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  padding-right: 8px;
  margin-right: 8px;
}

.files-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 8px;
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

.select-all-checkbox.checked,
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
  padding: 4px 4px 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
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

.feature-config-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.feature-config-section {
  flex: 1;
}

.prompt-input {
  height: 100%;
  min-height: 160px;
}

.feature-config-message {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.feature-config-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.prompt-input {
  width: 100%;
  min-height: 72px;
  resize: vertical;
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

.feature-config-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-light);
  flex-shrink: 0;
}

.feature-config-btn {
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.feature-config-btn.cancel {
  background: var(--bg-main);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.feature-config-btn.cancel:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.feature-config-btn.confirm {
  background: var(--primary-color);
  color: white;
}

.feature-config-btn.confirm:hover {
  background: var(--primary-hover);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .feature-config-modal,
.modal-leave-active .feature-config-modal {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from .feature-config-modal,
.modal-leave-to .feature-config-modal {
  transform: scale(0.96);
  opacity: 0;
}
</style>
