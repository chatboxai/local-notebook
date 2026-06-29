<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="web-citation-tooltip"
      :style="{ left: x + 'px', top: y + 'px' }"
      @mouseleave="$emit('close')"
    >
      <div class="tooltip-header">
        
        <img v-if="favicon" :src="favicon" class="tooltip-favicon" alt="" />
        <svg v-else class="tooltip-icon" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
        </svg>
        <span class="tooltip-title">{{ title }}</span>
      </div>
      <div v-if="source || date" class="tooltip-meta">
        <span v-if="source">{{ source }}</span>
        <span v-if="source && date"> · </span>
        <span v-if="date">{{ date }}</span>
      </div>
      <div v-if="snippet" class="tooltip-snippet">{{ snippet }}</div>
      <div class="tooltip-link">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
          <path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/>
        </svg>
        <span>{{ $t('ui.clickToViewSource') }}</span>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean
  x: number
  y: number
  title: string
  url?: string
  snippet?: string
  source?: string
  date?: string
  favicon?: string
}>()

defineEmits<{
  (e: 'close'): void
}>()
</script>

<style scoped>
.web-citation-tooltip {
  position: fixed;
  transform: translate(-50%, calc(-100% - 12px));
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 14px;
  min-width: 280px;
  max-width: 360px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  animation: tooltipFadeIn 0.15s ease;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translate(-50%, calc(-100% - 8px));
  }
  to {
    opacity: 1;
    transform: translate(-50%, calc(-100% - 12px));
  }
}

.tooltip-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.tooltip-icon {
  flex-shrink: 0;
  color: #2196f3;
  margin-top: 2px;
}

.tooltip-favicon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  border-radius: 3px;
  margin-top: 2px;
  object-fit: contain;
}

.tooltip-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tooltip-meta {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 8px;
}

.tooltip-snippet {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--border-light);
}

.tooltip-link {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #2196f3;
  padding-top: 8px;
  border-top: 1px solid var(--border-light);
}
</style>
