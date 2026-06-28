<template>
  <main class="chat-panel">
    <ChatHeader
      :title="title"
      :is-editing="isEditingTitle"
      :editing-value="editingTitleValue"
      :is-streaming="isStreaming"
      @update:editing-value="emit('update:editingTitleValue', $event)"
      @start-title-edit="emit('start-title-edit')"
      @save-title-edit="emit('save-title-edit')"
      @cancel-title-edit="emit('cancel-title-edit')"
      @create-session="emit('create-session')"
      @open-history="emit('open-history')"
    />

    <ChatMessages
      ref="messagesComponentRef"
      :messages="messages"
      :has-ready-files="hasReadyFiles"
      :localized-greeting="localizedGreeting"
      :is-loading-more-messages="isLoadingMoreMessages"
      :has-more-messages="hasMoreMessages"
      :is-messages-scrollable="isMessagesScrollable"
      :is-export-selection-mode="isExportSelectionMode"
      :selected-user-message-ids="selectedUserMessageIds"
      :editing-message-id="editingMessageId"
      :editing-content="editingContent"
      :is-streaming="isStreaming"
      :streaming-parts-count="streamingPartsCount"
      :streaming-rendered="streamingRendered"
      :is-thinking="isThinking"
      :is-tool-only-message="isToolOnlyMessage"
      :is-message-in-selected-conversation="isMessageInSelectedConversation"
      :is-pre-compact-message="isPreCompactMessage"
      :parse-message-content="parseMessageContent"
      :get-rendered-message="getRenderedMessage"
      :should-show-message-actions="shouldShowMessageActions"
      :is-last-assistant-message="isLastAssistantMessage"
      :format-message-time="formatMessageTime"
      @messages-scroll="emit('messages-scroll')"
      @web-citation-hover="emit('web-citation-hover', $event)"
      @web-citation-leave="emit('web-citation-leave', $event)"
      @chat-area-click="emit('chat-area-click', $event)"
      @trigger-upload="emit('trigger-upload')"
      @toggle-conversation-selection="emit('toggle-conversation-selection', $event)"
      @update:editing-content="emit('update:editingContent', $event)"
      @submit-edit-message="emit('submit-edit-message', $event)"
      @cancel-edit-message="emit('cancel-edit-message')"
      @auto-resize-edit-textarea="emit('auto-resize-edit-textarea')"
      @start-edit-message="emit('start-edit-message', $event)"
      @copy-user-message="emit('copy-user-message', $event)"
      @copy-message-as-text="emit('copy-message-as-text', $event)"
      @copy-message-as-markdown="emit('copy-message-as-markdown', $event)"
      @regenerate-message="emit('regenerate-message', $event)"
      @enter-export-mode-with-selection="emit('enter-export-mode-with-selection', $event)"
    />

    <transition name="fade">
      <button
        v-if="showScrollToBottom"
        class="scroll-to-bottom-btn"
        :style="{ bottom: scrollBtnBottom + (isExportSelectionMode ? 60 : 0) + 'px' }"
        title="滚动到底部"
        @click="emit('force-scroll-to-bottom')"
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
        </svg>
      </button>
    </transition>

    <transition name="slide-up">
      <ChatSelectionBar
        v-if="isExportSelectionMode"
        :selected-count="selectedUserMessageIds.length"
        :all-selected="allUserMessagesSelected"
        :is-exporting="isExportingMessages"
        :export-disabled="selectedUserMessageIds.length === 0 || isExportingMessages"
        @toggle-all="emit('toggle-select-all-user-messages')"
        @cancel="emit('toggle-export-selection-mode')"
        @export="emit('export-selected-messages')"
      />
    </transition>

    <ChatInput
      ref="inputComponentRef"
      :input-message="inputMessage"
      :enable-web-search="enableWebSearch"
      :source-count="sourceCount"
      :has-ready-files="hasReadyFiles"
      :has-current-session="hasCurrentSession"
      :is-streaming="isStreaming"
      :is-export-selection-mode="isExportSelectionMode"
      @update:input-message="emit('update:inputMessage', $event)"
      @update:enable-web-search="emit('update:enableWebSearch', $event)"
      @send-enter="emit('send-enter')"
      @composition-start="emit('composition-start')"
      @composition-end="emit('composition-end')"
      @auto-resize="emit('auto-resize-textarea')"
      @send-message="emit('send-message')"
      @stop-streaming="emit('stop-streaming')"
    />

    <ChatCopyToast :visible="copyToastVisible" :message="copyToastMessage" />
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Message } from '../../../types'
import ChatCopyToast from './ChatCopyToast.vue'
import ChatHeader from './ChatHeader.vue'
import ChatInput from './ChatInput.vue'
import ChatMessages from './ChatMessages.vue'
import ChatSelectionBar from './ChatSelectionBar.vue'

type RenderedSegment = { type: string; html: string }

interface ParsedMessageContent {
  hasError: boolean
  hasPartial: boolean
  mainContent: string
  systemHint: string | null
}

interface Props {
  title: string
  isEditingTitle: boolean
  editingTitleValue: string
  isStreaming: boolean
  messages: Message[]
  hasReadyFiles: boolean
  localizedGreeting: string
  isLoadingMoreMessages: boolean
  hasMoreMessages: boolean
  isMessagesScrollable: boolean
  isExportSelectionMode: boolean
  selectedUserMessageIds: string[]
  isExportingMessages: boolean
  editingMessageId: string | null
  editingContent: string
  streamingPartsCount: number
  streamingRendered: RenderedSegment[]
  isThinking: boolean
  showScrollToBottom: boolean
  scrollBtnBottom: number
  inputMessage: string
  enableWebSearch: boolean
  sourceCount: number
  hasCurrentSession: boolean
  copyToastVisible: boolean
  copyToastMessage: string
  isToolOnlyMessage: (msg: Message) => boolean
  isMessageInSelectedConversation: (index: number) => boolean
  isPreCompactMessage: (index: number) => boolean
  parseMessageContent: (msg: Message) => ParsedMessageContent
  getRenderedMessage: (msg: Message) => RenderedSegment[]
  shouldShowMessageActions: (index: number) => boolean
  isLastAssistantMessage: (index: number) => boolean
  formatMessageTime: (value: string) => string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:editingTitleValue': [value: string]
  'start-title-edit': []
  'save-title-edit': []
  'cancel-title-edit': []
  'create-session': []
  'open-history': []
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
  'force-scroll-to-bottom': []
  'toggle-select-all-user-messages': []
  'toggle-export-selection-mode': []
  'export-selected-messages': []
  'update:inputMessage': [value: string]
  'update:enableWebSearch': [value: boolean]
  'send-enter': []
  'composition-start': []
  'composition-end': []
  'auto-resize-textarea': []
  'send-message': []
  'stop-streaming': []
}>()

const messagesComponentRef = ref<InstanceType<typeof ChatMessages> | null>(null)
const inputComponentRef = ref<InstanceType<typeof ChatInput> | null>(null)

const allUserMessagesSelected = computed(() => {
  const userMessageCount = props.messages.filter(message => message.role === 'user').length
  return userMessageCount > 0 && props.selectedUserMessageIds.length === userMessageCount
})

defineExpose({
  get messagesElement() {
    return messagesComponentRef.value?.messagesElement ?? null
  },
  get editTextareaElements() {
    return messagesComponentRef.value?.editTextareaElements ?? []
  },
  get textareaElement() {
    return inputComponentRef.value?.textareaElement ?? null
  },
  get inputWrapperElement() {
    return inputComponentRef.value?.inputWrapperElement ?? null
  }
})
</script>

<style scoped>
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-white);
  border-radius: 16px;
  min-width: 400px;
  position: relative;
}

.scroll-to-bottom-btn {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  color: var(--text-secondary);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  transition: all 0.2s;
  z-index: 10;
}

.scroll-to-bottom-btn:hover {
  background: var(--bg-hover);
  color: var(--primary-color);
  transform: translateX(-50%) scale(1.1);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
</style>
