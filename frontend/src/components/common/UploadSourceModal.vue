<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="handleClose">
      <div class="modal-container" :class="{ 'paste-mode': isPasteMode }">

        <template v-if="!isPasteMode">
          <div class="modal-header">
            <h2>根据以下内容生成笔记</h2>
            <button class="close-btn" @click="handleClose">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">

            <div v-if="isAtLimit" class="limit-warning">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
              </svg>
              <span>已达到文件数量上限（{{ maxFileCount }} 个）</span>
            </div>


            <div
              class="upload-dropzone"
              :class="{ dragover: isDragover && !isAtLimit && !props.isUploading, disabled: isAtLimit, uploading: props.isUploading }"
              @click="!isAtLimit && !props.isUploading && triggerFileInput()"
              @dragover.prevent="!isAtLimit && !props.isUploading && (isDragover = true)"
              @dragleave.prevent="isDragover = false"
              @drop.prevent="!props.isUploading && handleDrop($event)"
            >
              <div class="dropzone-icon" :class="{ spinning: props.isUploading }">
                <svg v-if="props.isUploading" viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
                  <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
                  <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/>
                </svg>
              </div>
              <p class="dropzone-text">{{ props.isUploading ? '正在上传...' : (isAtLimit ? '文件数量已达上限' : '点击上传或将文件拖至此处') }}</p>
              <p class="dropzone-hint">支持 pdf、docx、doc、jpg、jpeg、png</p>
              <p class="dropzone-hint unsupported">wav、mp3、m4a、wma（即将支持）</p>
              <input
                ref="fileInputRef"
                type="file"
                accept=".pdf,.docx,.doc,.jpg,.jpeg,.png"
                multiple
                style="display: none"
                @change="handleFileSelect"
              />
            </div>


            <button class="paste-text-btn" :disabled="isAtLimit || props.isUploading" @click="enterPasteMode">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
              </svg>
              <span>粘贴文字</span>
            </button>
          </div>


          <div class="modal-footer">
            <div class="file-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
              </div>
              <span class="progress-text">{{ currentFileCount }}/{{ maxFileCount }}</span>
            </div>
          </div>
        </template>


        <template v-else>
          <div class="modal-header">
            <button class="back-btn" @click="exitPasteMode">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
              </svg>
            </button>
            <h2>粘贴复制的文字</h2>
            <button class="close-btn" @click="handleClose">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>

          <div class="modal-body paste-body">
            <p class="paste-hint">在下方粘贴复制的文字，即可将其作为来源上传。</p>
            <textarea
              ref="pasteTextareaRef"
              v-model="pasteContent"
              class="paste-textarea"
              placeholder="在此粘贴文字内容..."
            ></textarea>
          </div>

          <div class="modal-footer paste-footer">
            <div class="file-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
              </div>
              <span class="progress-text">{{ currentFileCount }}/{{ maxFileCount }}</span>
            </div>
            <button
              class="insert-btn"
              :disabled="!pasteContent.trim()"
              @click="handleInsertText"
            >
              插入
            </button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps<{
  visible: boolean
  currentFileCount: number
  maxFileCount?: number
  isUploading?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'upload-files', files: File[]): void
  (e: 'insert-text', content: string): void
}>()

const maxFileCount = computed(() => props.maxFileCount || 30)
const progressPercent = computed(() => (props.currentFileCount / maxFileCount.value) * 100)
const isAtLimit = computed(() => props.currentFileCount >= maxFileCount.value)
const remainingCount = computed(() => maxFileCount.value - props.currentFileCount)

const isPasteMode = ref(false)
const isDragover = ref(false)
const pasteContent = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)
const pasteTextareaRef = ref<HTMLTextAreaElement | null>(null)


watch(() => props.visible, (newVal) => {
  if (!newVal) {
    isPasteMode.value = false
    pasteContent.value = ''
    isDragover.value = false
  }
})

function handleClose() {
  emit('close')
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileSelect(event: Event) {
  if (isAtLimit.value) return
  const input = event.target as HTMLInputElement
  const files = input.files
  if (files && files.length > 0) {

    const filesToUpload = Array.from(files).slice(0, remainingCount.value)
    if (filesToUpload.length > 0) {
      emit('upload-files', filesToUpload)
      handleClose()
    }
    input.value = ''
  }
}

function handleDrop(event: DragEvent) {
  isDragover.value = false
  if (isAtLimit.value) return
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {

    const validFiles = Array.from(files).filter(file => {
      const ext = file.name.toLowerCase().split('.').pop()
      return ['docx', 'doc', 'pdf', 'jpg', 'jpeg', 'png'].includes(ext || '')
    })

    const filesToUpload = validFiles.slice(0, remainingCount.value)
    if (filesToUpload.length > 0) {
      emit('upload-files', filesToUpload)
      handleClose()
    }
  }
}

function enterPasteMode() {
  isPasteMode.value = true
  nextTick(() => {
    pasteTextareaRef.value?.focus()
  })
}

function exitPasteMode() {
  isPasteMode.value = false
  pasteContent.value = ''
}

function handleInsertText() {
  if (pasteContent.value.trim()) {
    emit('insert-text', pasteContent.value.trim())
    handleClose()
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-container {
  width: 560px;
  max-width: 90vw;
  max-height: 80vh;
  background: var(--bg-white);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  animation: slideUp 0.25s ease;
}

.modal-container.paste-mode {
  height: 500px;
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

.modal-header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 24px 16px;
  position: relative;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.close-btn {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.back-btn {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 50%;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.back-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.modal-body {
  padding: 16px 24px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.limit-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  color: #b45309;
  font-size: 14px;
}

.upload-dropzone {
  border: 2px dashed var(--border-color);
  border-radius: 16px;
  padding: 40px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--bg-main);
}

.upload-dropzone:hover:not(.disabled),
.upload-dropzone.dragover {
  border-color: var(--primary-color);
  background: var(--primary-light);
}

.upload-dropzone.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-dropzone.uploading {
  cursor: default;
  border-color: var(--primary-color);
  background: var(--primary-light);
}

.dropzone-icon {
  color: var(--text-tertiary);
  margin-bottom: 16px;
  transition: color 0.2s;
}

.upload-dropzone:hover .dropzone-icon,
.upload-dropzone.dragover .dropzone-icon,
.upload-dropzone.uploading .dropzone-icon {
  color: var(--primary-color);
}

.dropzone-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.dropzone-text {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.dropzone-hint {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
}

.dropzone-hint.unsupported {
  text-decoration: line-through;
  opacity: 0.5;
  font-size: 12px;
  margin-top: 4px;
}

.paste-text-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 24px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.paste-text-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.paste-text-btn svg {
  color: var(--text-secondary);
}

.paste-text-btn:hover:not(:disabled) svg {
  color: var(--primary-color);
}

.paste-text-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}


.paste-body {
  padding: 8px 24px 16px;
}

.paste-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 16px;
}

.paste-textarea {
  flex: 1;
  width: 100%;
  padding: 16px;
  border: 2px solid var(--primary-color);
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
  background: var(--bg-white);
  resize: none;
  outline: none;
}

.paste-textarea::placeholder {
  color: var(--text-tertiary);
}

.paste-textarea:focus {
  box-shadow: 0 0 0 3px var(--primary-light);
}

.modal-footer {
  padding: 16px 24px 24px;
}

.paste-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.file-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: var(--bg-hover);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 13px;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.insert-btn {
  padding: 12px 32px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.insert-btn:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: scale(1.02);
}

.insert-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
