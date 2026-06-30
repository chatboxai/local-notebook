<template>
  <Teleport to="body">
    <div v-if="visible" class="tool-config-overlay" @click.self="handleClose">
      <div class="tool-config-modal">
        <div class="tool-config-header">
          <h3>{{ toolTitle }}</h3>
          <button class="tool-config-close" @click="handleClose">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        <div class="tool-config-content">
          
          <div class="tool-config-files">
            <div class="files-header" @click="toggleSelectAll">
              <span class="files-title">{{ $t('ui.selectFiles') }}</span>
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
                {{ $t('ui.noSelectableFiles') }}
              </div>
            </div>
          </div>

          
          <div class="tool-config-body">
            <template v-if="!hidePrompt">
              <label class="tool-config-label">{{ $t('ui.customRequirementsOptional') }}</label>
              <textarea
                v-model="promptText"
                class="tool-config-textarea"
                :placeholder="$t('ui.customRequirementPlaceholder')"
              ></textarea>
              <p class="tool-config-hint">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                </svg>
                {{ $t('ui.leaveBlankToUseDefaultConfig') }}
              </p>
            </template>
            <p v-else class="tool-config-hint developing">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
              </svg>
              {{ $t('ui.customRequirementsComingSoonUseDefault') }}
            </p>
          </div>
        </div>
        <div class="tool-config-footer">
          <button class="tool-config-btn cancel" @click="handleClose">{{ $t('ui.cancel') }}</button>
          <button class="tool-config-btn confirm" :disabled="localSelectedIds.length === 0" @click="handleConfirm">{{ $t('ui.generate') }}</button>
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
  toolType: string
  toolTitle: string
  hidePrompt?: boolean
  files?: FileItem[]
  selectedFileIds?: string[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', toolType: string, prompt: string, fileIds: string[]): void
}>()

const promptText = ref('')
const localSelectedIds = ref<string[]>([])


const AUDIO_TYPES = ['wav', 'mp3', 'm4a']

const IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'webp']


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


watch(() => props.visible, (newVal) => {
  if (newVal) {
    
    
    const selectableIds = new Set(selectableFiles.value.map(f => f.id))
    localSelectedIds.value = (props.selectedFileIds || []).filter(id => selectableIds.has(id))
  } else {
    promptText.value = ''
    localSelectedIds.value = []
  }
})

function handleClose() {
  emit('close')
}

function handleConfirm() {
  emit('confirm', props.toolType, promptText.value.trim(), localSelectedIds.value)
}
</script>

<style scoped>
.tool-config-overlay {
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

.tool-config-modal {
  width: 680px;
  max-width: 90vw;
  height: 420px;
  max-height: 80vh;
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

.tool-config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}

.tool-config-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.tool-config-close {
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

.tool-config-close:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.tool-config-content {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}


.tool-config-files {
  width: 240px;
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


.tool-config-body {
  flex: 1;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tool-config-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 10px;
  flex-shrink: 0;
}

.tool-config-textarea {
  flex: 1;
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
  background: var(--bg-main);
  resize: none;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.tool-config-textarea:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.tool-config-textarea::placeholder {
  color: var(--text-tertiary);
}

.tool-config-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.tool-config-hint svg {
  flex-shrink: 0;
}

.tool-config-hint.developing {
  padding: 16px;
  background: var(--bg-main);
  border-radius: 8px;
  margin: 0;
}

.tool-config-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-light);
  flex-shrink: 0;
}

.tool-config-btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: none;
}

.tool-config-btn.cancel {
  background: var(--bg-main);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.tool-config-btn.cancel:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.tool-config-btn.confirm {
  background: var(--primary-color);
  color: white;
}

.tool-config-btn.confirm:hover:not(:disabled) {
  background: var(--primary-hover);
}

.tool-config-btn.confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
