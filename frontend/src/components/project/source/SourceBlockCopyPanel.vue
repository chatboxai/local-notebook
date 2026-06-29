<template>
  <Teleport to="body">
    <div
      v-if="visible && block && position"
      class="block-copy-panel-floating"
      :style="{
        top: position.top + 'px',
        left: position.left + 'px'
      }"
    >
      <div class="copy-panel-content">
        <div class="copy-panel-text">{{ block.content }}</div>
        <div class="copy-panel-actions">
          <button class="copy-btn" @click.stop="emit('copy')">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
              <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
            </svg>
            {{ $t('ui.copyText') }}
          </button>
          <button class="close-btn" @click.stop="emit('close')">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import type { FoundBlock } from '@/services/api'

defineProps<{
  visible: boolean
  block: FoundBlock | null
  position: { top: number; left: number } | null
}>()

const emit = defineEmits<{
  (e: 'copy'): void
  (e: 'close'): void
}>()
</script>

<style scoped>
.block-copy-panel-floating {
  position: fixed;
  z-index: 10000;
  pointer-events: auto;
}

.copy-panel-content {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  max-width: 320px;
  overflow: hidden;
}

.copy-panel-text {
  padding: 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  max-height: 150px;
  overflow-y: auto;
  border-bottom: 1px solid var(--border-color);
  word-break: break-word;
}

.copy-panel-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-secondary);
}

.copy-panel-actions .copy-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.copy-panel-actions .copy-btn:hover {
  background: var(--primary-hover);
}

.copy-panel-actions .close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.copy-panel-actions .close-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}
</style>
