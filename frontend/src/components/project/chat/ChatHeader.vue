<template>
  <div class="chat-header">
    <div class="session-title-wrapper">
      <input
        v-if="isEditing"
        ref="titleInputRef"
        :value="editingValue"
        class="session-title-input"
        @input="handleTitleInput"
        @blur="requestSaveTitle"
        @keydown.enter="requestSaveTitle"
        @keydown.escape="emit('cancel-title-edit')"
        @compositionstart="isComposing = true"
        @compositionend="isComposing = false"
      />
      <span
        v-else
        class="chat-title"
        :title="$t('ui.clickToEditChatTitle')"
        @click="emit('start-title-edit')"
      >{{ title || $t('ui.newChat') }}</span>
    </div>

    <div class="chat-header-actions">
      <button
        class="header-action-btn"
        :disabled="isStreaming"
        :title="$t('ui.newChat2')"
        @click="emit('create-session')"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
        </svg>
      </button>
      <button
        class="header-action-btn"
        :title="$t('ui.chatHistory')"
        @click="emit('open-history')"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

interface Props {
  title: string
  isEditing: boolean
  editingValue: string
  isStreaming: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:editingValue': [value: string]
  'start-title-edit': []
  'save-title-edit': []
  'cancel-title-edit': []
  'create-session': []
  'open-history': []
}>()

const titleInputRef = ref<HTMLInputElement | null>(null)
const isComposing = ref(false)

watch(
  () => props.isEditing,
  (isEditing) => {
    if (!isEditing) {
      isComposing.value = false
      return
    }

    nextTick(() => {
      titleInputRef.value?.focus()
      titleInputRef.value?.select()
    })
  }
)

function handleTitleInput(event: Event) {
  emit('update:editingValue', (event.target as HTMLInputElement).value)
}

function requestSaveTitle() {
  if (!isComposing.value) {
    emit('save-title-edit')
  }
}
</script>

<style scoped>
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
}

.session-title-wrapper {
  flex: 1;
  min-width: 0;
}

.chat-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.15s;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.chat-title:hover {
  background: var(--bg-hover);
}

.session-title-input {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  padding: 4px 8px;
  border: 1px solid var(--primary-color);
  border-radius: 6px;
  outline: none;
  background: var(--bg-white);
  width: 280px;
  max-width: 100%;
}

.chat-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.header-action-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.header-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
