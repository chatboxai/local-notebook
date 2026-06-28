<template>
  <div
    ref="messagesRef"
    class="chat-messages"
    @scroll="emit('messages-scroll')"
    @mouseover="emit('web-citation-hover', $event)"
    @mouseout="emit('web-citation-leave', $event)"
    @click="emit('chat-area-click', $event)"
  >
    <div v-if="messages.length === 0" class="chat-empty">
      <template v-if="hasReadyFiles">
        <div class="greeting-message">{{ localizedGreeting }}</div>
      </template>

      <template v-else>
        <div class="empty-upload-icon">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
            <path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z" />
          </svg>
        </div>
        <h3>添加来源即可开始使用</h3>
        <button class="upload-btn" @click="emit('trigger-upload')">上传来源</button>
      </template>
    </div>

    <template v-else>
      <div v-if="isLoadingMoreMessages" class="loading-more-messages">
        <span class="loading-spinner"></span>
        <span>加载历史消息...</span>
      </div>
      <div v-else-if="hasMoreMessages && isMessagesScrollable" class="load-more-hint">
        <span>向上滚动加载更多</span>
      </div>

      <div
        v-for="(msg, index) in messages"
        :key="msg.id"
        class="message"
        :class="[msg.role, {
          'tool-only': isToolOnlyMessage(msg),
          'selection-mode': isExportSelectionMode,
          'conversation-selected': isExportSelectionMode && isMessageInSelectedConversation(index)
        }]"
        @click="isExportSelectionMode && emit('toggle-conversation-selection', index)"
      >
        <div v-if="isExportSelectionMode && msg.role === 'user'" class="message-selection-check">
          <div class="custom-checkbox" :class="{ checked: selectedUserMessageIds.includes(msg.id) }">
            <svg v-if="selectedUserMessageIds.includes(msg.id)" viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
          </div>
        </div>

        <div v-if="msg.role === 'compact_divider'" class="compact-divider">
          <span>── 更早的对话已压缩 ──</span>
        </div>

        <div v-else-if="msg.role === 'user'" class="user-message" :class="{ editing: editingMessageId === msg.id, selectable: isExportSelectionMode }">
          <div v-if="editingMessageId === msg.id" class="user-message-edit">
            <textarea
              ref="editTextareaRef"
              :value="editingContent"
              class="user-edit-textarea"
              @input="handleEditingInput"
              @keydown.enter.exact.prevent="emit('submit-edit-message', msg)"
              @keydown.escape="emit('cancel-edit-message')"
            ></textarea>
            <div class="user-edit-actions">
              <button class="edit-cancel-btn" @click="emit('cancel-edit-message')">取消</button>
              <button
                class="edit-submit-btn"
                :disabled="!editingContent.trim() || isStreaming"
                @click="emit('submit-edit-message', msg)"
              >
                保存并重新生成
              </button>
            </div>
          </div>

          <template v-else>
            <span class="user-message-content">{{ msg.content }}</span>
            <div v-if="!isExportSelectionMode" class="user-action-btns">
              <button
                class="user-action-btn"
                :data-tooltip="isPreCompactMessage(index) ? '已压缩的消息不可编辑' : '编辑'"
                :disabled="isStreaming || isPreCompactMessage(index)"
                @click="emit('start-edit-message', msg)"
              >
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
              </button>
              <button class="user-action-btn" data-tooltip="复制" @click="emit('copy-user-message', msg)">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
              </button>
            </div>
          </template>
        </div>

        <div v-else class="assistant-message">
          <div
            class="assistant-content"
            :class="{ 'has-error': parseMessageContent(msg).hasError }"
          >
            <div
              v-for="(segment, segIndex) in getRenderedMessage(msg)"
              :key="segIndex"
              class="assistant-segment"
              :class="`segment-${segment.type}`"
            >
              <div
                v-if="segment.type === 'body'"
                class="assistant-body markdown-body"
                v-html="segment.html"
              ></div>
              <div
                v-else
                v-html="segment.html"
              ></div>
            </div>
          </div>

          <div v-if="shouldShowMessageActions(index)" class="message-actions">
            <button class="action-btn" data-tooltip="复制纯文本" @click="emit('copy-message-as-text', msg)">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
            <button class="action-btn" data-tooltip="复制 Markdown" @click="emit('copy-message-as-markdown', msg)">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 3v4a1 1 0 001 1h4"></path>
                <path d="M17 21H7a2 2 0 01-2-2V5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2z"></path>
                <path d="M9 15l2-2 2 2"></path>
                <path d="M11 13v4"></path>
              </svg>
            </button>
            <button class="action-btn" disabled data-tooltip="喜欢（即将推出）">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
              </svg>
            </button>
            <button class="action-btn" disabled data-tooltip="不喜欢（即将推出）">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
              </svg>
            </button>
            <button
              class="action-btn"
              :class="{ 'error-retry': parseMessageContent(msg).hasError }"
              :disabled="!isLastAssistantMessage(index) || isStreaming || isPreCompactMessage(index)"
              :data-tooltip="isPreCompactMessage(index) ? '已压缩的消息不可重新生成' : (parseMessageContent(msg).hasError ? '重新生成（上次出错）' : (isLastAssistantMessage(index) ? '重新生成' : '仅最后一条消息可重新生成'))"
              @click="emit('regenerate-message', index)"
            >
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 4v6h6"></path>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
              </svg>
            </button>
            <button
              class="action-btn"
              data-tooltip="下载对话"
              :disabled="isStreaming"
              @click.stop="emit('enter-export-mode-with-selection', index)"
            >
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
            </button>
            <span class="actions-divider">|</span>
            <span class="agent-role-label">{{ msg.agent_role === 'analysis' ? '分析助手' : '小洛' }}</span>
            <span class="message-time">{{ formatMessageTime(msg.created_at) }}</span>
          </div>
        </div>
      </div>

      <div v-if="streamingPartsCount > 0 || isStreaming" class="message assistant">
        <div class="assistant-message">
          <div class="assistant-content">
            <div
              v-for="(segment, segIndex) in streamingRendered"
              :key="segIndex"
              class="assistant-segment"
              :class="`segment-${segment.type}`"
            >
              <div
                v-if="segment.type === 'body'"
                class="assistant-body markdown-body"
                v-html="segment.html"
              ></div>
              <div
                v-else
                v-html="segment.html"
              ></div>
            </div>
          </div>

          <div v-if="isThinking" class="thinking-indicator">
            <svg class="thinking-spinner" viewBox="0 0 24 24" width="14" height="14">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="31.4 31.4" stroke-linecap="round"/>
            </svg>
            <span>思考中...</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Message } from '../../../types'

type RenderedSegment = { type: string; html: string }

interface ParsedMessageContent {
  hasError: boolean
  hasPartial: boolean
  mainContent: string
  systemHint: string | null
}

interface Props {
  messages: Message[]
  hasReadyFiles: boolean
  localizedGreeting: string
  isLoadingMoreMessages: boolean
  hasMoreMessages: boolean
  isMessagesScrollable: boolean
  isExportSelectionMode: boolean
  selectedUserMessageIds: string[]
  editingMessageId: string | null
  editingContent: string
  isStreaming: boolean
  streamingPartsCount: number
  streamingRendered: RenderedSegment[]
  isThinking: boolean
  isToolOnlyMessage: (msg: Message) => boolean
  isMessageInSelectedConversation: (index: number) => boolean
  isPreCompactMessage: (index: number) => boolean
  parseMessageContent: (msg: Message) => ParsedMessageContent
  getRenderedMessage: (msg: Message) => RenderedSegment[]
  shouldShowMessageActions: (index: number) => boolean
  isLastAssistantMessage: (index: number) => boolean
  formatMessageTime: (value: string) => string
}

defineProps<Props>()

const emit = defineEmits<{
  'messages-scroll': []
  'web-citation-hover': [event: MouseEvent]
  'web-citation-leave': [event: MouseEvent]
  'chat-area-click': [event: MouseEvent]
  'trigger-upload': []
  'toggle-conversation-selection': [index: number]
  'update:editingContent': [value: string]
  'submit-edit-message': [message: Message]
  'cancel-edit-message': []
  'auto-resize-edit-textarea': []
  'start-edit-message': [message: Message]
  'copy-user-message': [message: Message]
  'copy-message-as-text': [message: Message]
  'copy-message-as-markdown': [message: Message]
  'regenerate-message': [index: number]
  'enter-export-mode-with-selection': [index: number]
}>()

const messagesRef = ref<HTMLDivElement | null>(null)
const editTextareaRef = ref<HTMLTextAreaElement[]>([])

defineExpose({
  get messagesElement() {
    return messagesRef.value
  },
  get editTextareaElements() {
    return editTextareaRef.value
  }
})

function handleEditingInput(event: Event) {
  emit('update:editingContent', (event.target as HTMLTextAreaElement).value)
  emit('auto-resize-edit-textarea')
}
</script>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--text-secondary);
}

.loading-more-messages,
.load-more-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.loading-more-messages .loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.load-more-hint {
  opacity: 0.6;
}

.empty-upload-icon {
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.chat-empty h3 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
}

.greeting-message {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 1px;
}

.upload-btn {
  padding: 10px 20px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  color: var(--text-primary);
  font-size: 14px;
}

.upload-btn:hover {
  background: var(--bg-hover);
}

.message {
  margin-bottom: 14px;
  position: relative;
  transition: all 0.2s;
}

.message.selection-mode {
  padding-left: 40px;
  cursor: pointer;
}

.message.selection-mode.user {
  cursor: pointer;
}

.message.conversation-selected {
  background-color: rgba(0, 127, 255, 0.06);
  margin-left: -8px;
  margin-right: -8px;
  padding-left: 48px;
  padding-right: 8px;
}

.message.conversation-selected.user {
  border-radius: 12px 12px 0 0;
  margin-bottom: 0;
  padding-bottom: 12px;
}

.message.conversation-selected.assistant {
  border-radius: 0 0 12px 12px;
  margin-top: 0;
  padding-top: 12px;
}

.message-selection-check {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 5;
}

.custom-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-white);
  color: #fff;
  transition: all 0.2s;
}

.custom-checkbox.checked {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.user-message.selectable:hover {
  background: var(--bg-hover);
}

.message.assistant + .message.assistant {
  margin-top: 0;
}

.message.assistant.tool-only {
  margin-bottom: 2px;
}

.message.assistant.tool-only + .message.assistant:not(.tool-only) {
  margin-top: 8px;
}

.compact-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 0;
  color: var(--text-tertiary, #999);
  font-size: 12px;
}

.compact-divider span {
  background: var(--bg-secondary, #f5f5f5);
  padding: 2px 12px;
  border-radius: 10px;
}

.user-message {
  position: relative;
  max-width: 80%;
  padding: 14px 20px;
  background: var(--bg-main);
  border-radius: 20px 20px 4px 20px;
  color: var(--text-primary);
  float: right;
  clear: both;
  line-height: 1.6;
  letter-spacing: 0.02em;
  text-align: left;
}

.user-message-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.user-action-btns {
  position: absolute;
  left: -60px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s;
}

.message.user:hover .user-action-btns {
  opacity: 1;
  visibility: visible;
}

.user-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.user-action-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-secondary);
}

.user-action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.user-action-btn::before,
.user-action-btn::after {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
  pointer-events: none;
}

.user-action-btn::before {
  content: attr(data-tooltip);
  bottom: calc(100% + 6px);
  padding: 4px 8px;
  background: #1f2937;
  color: #fff;
  font-size: 12px;
  font-weight: 400;
  border-radius: 4px;
  white-space: nowrap;
}

.user-action-btn::after {
  content: '';
  bottom: calc(100% + 1px);
  width: 8px;
  height: 4px;
  background: #1f2937;
  clip-path: polygon(50% 100%, 0% 0%, 100% 0%);
}

.user-action-btn:hover::before,
.user-action-btn:hover::after {
  opacity: 1;
  visibility: visible;
}

.user-message.editing {
  width: 80%;
  background: transparent;
  padding: 0;
}

.user-message-edit {
  width: 100%;
}

.user-edit-textarea {
  display: block;
  width: 100%;
  padding: 8px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-white);
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  resize: none;
  font-family: inherit;
  box-sizing: border-box;
  overflow-y: hidden;
  min-height: 60px;
  max-height: 300px;
}

.user-edit-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
}

.user-edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.edit-cancel-btn {
  padding: 6px 14px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-cancel-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.edit-submit-btn {
  padding: 6px 14px;
  background: var(--primary-color);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-submit-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.edit-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message.user {
  text-align: right;
}

.message.user::after {
  content: '';
  display: table;
  clear: both;
}

.assistant-message {
  max-width: 80%;
}

.message-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
}

.message-actions .action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.message-actions .action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.message-actions .action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message-actions .actions-divider {
  color: var(--border-color);
  font-size: 12px;
  margin: 0 4px;
}

.message-actions .agent-role-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.message-actions .message-time {
  font-size: 12px;
  color: #b0b0b0;
  margin-left: 8px;
}

.message-actions .action-btn {
  position: relative;
}

.message-actions .action-btn::before,
.message-actions .action-btn::after {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
  pointer-events: none;
}

.message-actions .action-btn::before {
  content: attr(data-tooltip);
  bottom: calc(100% + 6px);
  padding: 6px 10px;
  background: #1f2937;
  color: #fff;
  font-size: 12px;
  font-weight: 400;
  border-radius: 6px;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.message-actions .action-btn::after {
  content: '';
  bottom: calc(100% + 1px);
  width: 10px;
  height: 5px;
  background: #1f2937;
  clip-path: polygon(50% 100%, 0% 0%, 100% 0%);
}

.message-actions .action-btn:hover::before,
.message-actions .action-btn:hover::after {
  opacity: 1;
  visibility: visible;
}

.assistant-content {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
  letter-spacing: 0.02em;
}

.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.thinking-spinner {
  animation: spin 1s linear infinite;
  color: var(--text-tertiary);
}

.assistant-content :deep(.thinking-block) {
  margin-bottom: 2px;
}

.assistant-content :deep(.thinking-header) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-tertiary);
  user-select: none;
}

.assistant-content :deep(.thinking-header:hover) {
  color: var(--text-secondary);
}

.assistant-content :deep(.thinking-header svg) {
  flex-shrink: 0;
}

.assistant-content :deep(.thinking-content) {
  margin-top: 2px;
  font-size: 12px;
  line-height: 1.2;
  color: var(--text-tertiary);
  white-space: pre-wrap;
  word-break: break-word;
}

.assistant-content :deep(.thinking-block.collapsed .thinking-content) {
  display: none;
}

.assistant-content :deep(.thinking-block.expanded .thinking-content) {
  display: block;
}

.assistant-content :deep(.thinking-citation) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 14px;
  height: 14px;
  padding: 0 3px;
  margin: 0 1px;
  background: var(--primary-light, #e3f2fd);
  color: var(--primary-color, #667eea);
  border-radius: 7px;
  font-size: 9px;
  font-weight: 600;
  vertical-align: baseline;
  position: relative;
  top: -1px;
  cursor: default;
}

.assistant-content :deep(.thinking-streaming-dot) {
  display: inline-block;
  width: 5px;
  height: 5px;
  background: var(--text-tertiary);
  border-radius: 50%;
  margin-left: 4px;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
  }
  50% {
    opacity: 1;
  }
}

.assistant-content :deep(.inline-citation) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 2px;
  margin: 0 2px;
  background: var(--primary-light);
  color: var(--primary-color);
  border-radius: 9px;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  vertical-align: middle;
  transition: background 0.15s, color 0.15s, transform 0.15s;
}

.assistant-content :deep(.inline-citation:hover) {
  background: var(--primary-color);
  color: white;
  transform: scale(1.15);
}

.assistant-content :deep(.inline-citation.active) {
  background: var(--primary-color);
  color: white;
  transform: scale(1.15);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
}

.assistant-content :deep(.inline-citation.disabled) {
  background: #e0e0e0;
  color: #9e9e9e;
  cursor: default;
  position: relative;
}

.assistant-content :deep(.inline-citation.disabled:hover) {
  background: #d0d0d0;
  transform: none;
}

.assistant-content :deep(.inline-citation.disabled::after) {
  content: '抱歉，暂时无法定位该引用来源';
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%) scale(0.9);
  padding: 8px 12px;
  background: rgba(30, 30, 30, 0.9);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  white-space: nowrap;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 1000;
  pointer-events: none;
}

.assistant-content :deep(.inline-citation.disabled::before) {
  content: '';
  position: absolute;
  bottom: calc(100% + 2px);
  left: 50%;
  transform: translateX(-50%) scale(0.9);
  border: 6px solid transparent;
  border-top-color: rgba(30, 30, 30, 0.9);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 1000;
  pointer-events: none;
}

.assistant-content :deep(.inline-citation.disabled:hover::after),
.assistant-content :deep(.inline-citation.disabled:hover::before) {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) scale(1);
}

.assistant-content :deep(.tool-status-item) {
  padding: 0;
  margin: 0;
  color: var(--text-tertiary);
  font-size: 13px;
  line-height: 1.2;
}

.assistant-content :deep(.tool-status-item + .tool-status-item) {
  margin-top: 2px;
}

.assistant-content :deep(.assistant-segment) {
  margin: 0;
}

.assistant-content :deep(.assistant-segment.segment-thinking + .assistant-segment.segment-tool),
.assistant-content :deep(.assistant-segment.segment-tool + .assistant-segment.segment-thinking),
.assistant-content :deep(.assistant-segment.segment-tool + .assistant-segment.segment-tool) {
  margin-top: 2px;
}

.markdown-body {
  font-size: 15px;
  line-height: 1.8;
  letter-spacing: 0.02em;
  color: var(--text-primary);
}

.markdown-body :deep(p) {
  margin: 0.8em 0;
}

.markdown-body :deep(p:first-child) {
  margin-top: 0;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.assistant-content :deep(.assistant-segment.segment-thinking + .assistant-segment.segment-body),
.assistant-content :deep(.assistant-segment.segment-tool + .assistant-segment.segment-body),
.assistant-content :deep(.assistant-segment.segment-body + .assistant-segment.segment-thinking),
.assistant-content :deep(.assistant-segment.segment-body + .assistant-segment.segment-tool) {
  margin-top: 6px;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 1.2em 0 0.6em;
  font-weight: 600;
  color: var(--text-primary);
}

.markdown-body :deep(h1) { font-size: 1.5em; }
.markdown-body :deep(h2) { font-size: 1.3em; }
.markdown-body :deep(h3) { font-size: 1.15em; }
.markdown-body :deep(h4) { font-size: 1.05em; }

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.8em 0;
  padding-left: 1.8em;
}

.markdown-body :deep(li) {
  margin: 0.4em 0;
}

.markdown-body :deep(code) {
  padding: 2px 6px;
  background: var(--bg-hover);
  border-radius: 4px;
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 0.9em;
  color: #c53030;
}

.markdown-body :deep(pre) {
  background: #1a202c;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1em 0;
}

.markdown-body :deep(pre code) {
  padding: 0;
  background: transparent;
  color: #e2e8f0;
}

.markdown-body :deep(blockquote) {
  margin: 1em 0;
  padding: 12px 16px;
  border-left: 4px solid var(--primary-color);
  background: var(--bg-sidebar);
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
}

.markdown-body :deep(hr) {
  border: none;
  height: 1px;
  background: var(--border-color);
  margin: 1.5em 0;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  text-align: left;
}

.markdown-body :deep(th) {
  background: var(--bg-sidebar);
  font-weight: 600;
}

.markdown-body :deep(a) {
  color: var(--primary-color);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.assistant-content :deep(.inline-citation.image-citation) {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border: 1px solid #81c784;
}

.assistant-content :deep(.inline-citation.image-citation:hover) {
  background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
  border-color: #66bb6a;
}

.assistant-content :deep(.inline-citation.web-citation) {
  width: auto;
  min-width: 18px;
  padding: 0 5px;
  gap: 2px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border: 1px solid #64b5f6;
  position: relative;
}

.assistant-content :deep(.inline-citation.web-citation .web-icon) {
  flex-shrink: 0;
  margin-left: 1px;
}

.assistant-content :deep(.inline-citation.web-citation .web-favicon) {
  flex-shrink: 0;
  margin-left: 2px;
  border-radius: 2px;
  vertical-align: middle;
}

.assistant-content :deep(.inline-citation.web-citation:hover) {
  background: linear-gradient(135deg, #bbdefb 0%, #90caf9 100%);
  border-color: #42a5f5;
}

.assistant-content.has-error {
  border-left: 3px solid #f59e0b;
  padding-left: 12px;
}

.assistant-content :deep(.error-placeholder) {
  color: #dc2626;
  font-size: 14px;
  line-height: 1.6;
}

.assistant-content :deep(.system-hint) {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  line-height: 1.5;
}

.assistant-content :deep(.system-hint.warning) {
  background-color: #fef3c7;
  border: 1px solid #fbbf24;
  color: #92400e;
}

.assistant-content :deep(.system-hint.error) {
  background-color: #fee2e2;
  border: 1px solid #f87171;
  color: #991b1b;
}

.assistant-content :deep(.system-hint .hint-icon) {
  flex-shrink: 0;
  font-size: 16px;
  line-height: 1;
}

.assistant-content :deep(.system-hint .hint-text) {
  flex: 1;
}

.action-btn.error-retry {
  color: #f59e0b;
}

.action-btn.error-retry:hover:not(:disabled) {
  background-color: #fef3c7;
  color: #d97706;
}
</style>
