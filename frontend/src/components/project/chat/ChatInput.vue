<template>
  <div ref="inputWrapperRef" class="chat-input-wrapper" :class="{ 'disabled-by-selection': isExportSelectionMode }">
    <div class="chat-input-box">
      <div class="input-main-row">
        <textarea
          ref="textareaRef"
          :value="inputMessage"
          :placeholder="hasReadyFiles ? '有什么想问的？' : '上传来源即可开始使用'"
          :disabled="!hasCurrentSession || isStreaming || !hasReadyFiles"
          rows="1"
          @input="handleInput"
          @keydown.enter.exact.prevent="emit('send-enter')"
          @compositionstart="emit('composition-start')"
          @compositionend="emit('composition-end')"
        ></textarea>
        <button
          v-if="!isStreaming"
          class="send-btn"
          :disabled="!inputMessage.trim() || !hasCurrentSession || !hasReadyFiles"
          title="发送"
          @click="emit('send-message')"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
        <button
          v-else
          class="send-btn"
          title="暂停"
          @click="emit('stop-streaming')"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M6 5h4v14H6zm8 0h4v14h-4z" />
          </svg>
        </button>
      </div>
      <div class="input-options-row">
        <label class="web-search-toggle" :class="{ active: enableWebSearch }">
          <input type="checkbox" :checked="enableWebSearch" @change="handleWebSearchChange" />
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
          </svg>
          <span>联网搜索</span>
        </label>

        <span class="source-count">{{ sourceCount }} 个来源</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  inputMessage: string
  enableWebSearch: boolean
  sourceCount: number
  hasReadyFiles: boolean
  hasCurrentSession: boolean
  isStreaming: boolean
  isExportSelectionMode: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:inputMessage': [value: string]
  'update:enableWebSearch': [value: boolean]
  'send-enter': []
  'composition-start': []
  'composition-end': []
  'auto-resize': []
  'send-message': []
  'stop-streaming': []
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const inputWrapperRef = ref<HTMLDivElement | null>(null)

defineExpose({
  get textareaElement() {
    return textareaRef.value
  },
  get inputWrapperElement() {
    return inputWrapperRef.value
  }
})

function handleInput(event: Event) {
  emit('update:inputMessage', (event.target as HTMLTextAreaElement).value)
  emit('auto-resize')
}

function handleWebSearchChange(event: Event) {
  emit('update:enableWebSearch', (event.target as HTMLInputElement).checked)
}
</script>

<style scoped>
.chat-input-wrapper {
  padding: 10px 14px;
  position: relative;
}

.chat-input-wrapper.disabled-by-selection {
  opacity: 0.5;
  pointer-events: none;
}

.chat-input-box {
  display: flex;
  flex-direction: column;
  padding: 10px 14px;
  background: var(--bg-main);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  box-shadow: var(--shadow-sm);
}

.chat-input-box:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px var(--primary-light);
}

.input-main-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-main-row textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  background: transparent;
  max-height: 150px;
  overflow-y: auto;
}

.input-main-row textarea:focus {
  box-shadow: none;
}

.input-options-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 8px;
  margin-top: 8px;
  border-top: 1px solid var(--border-light);
}

.source-count {
  font-size: 12px;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.send-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: scale(1.05);
}

.send-btn:disabled {
  background: var(--text-disabled);
  border-radius: 50%;
}

.web-search-toggle {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  font-size: 12px;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.2s;
  user-select: none;
}

.web-search-toggle:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.web-search-toggle.active {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.web-search-toggle input[type="checkbox"] {
  display: none;
}

.web-search-toggle svg {
  flex-shrink: 0;
}
</style>
