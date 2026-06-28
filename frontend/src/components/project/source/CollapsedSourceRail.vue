<template>
  <div class="collapsed-sidebar left">
    <div class="collapsed-icon-btn" @click="emit('expand')" title="展开来源面板">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/>
        <path d="M7 7h4v10H7z" opacity="0.5"/>
      </svg>
    </div>
    <div class="collapsed-icon-btn" @click="emit('trigger-file-upload')" title="添加来源">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
      </svg>
    </div>
    <div class="collapsed-icon-btn" @click="emit('expand')" :title="`${fileCount} 个来源文件`">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
      </svg>
      <span v-if="fileCount > 0" class="icon-badge">{{ fileCount }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  fileCount: number
}>()

const emit = defineEmits<{
  (e: 'expand'): void
  (e: 'trigger-file-upload'): void
}>()
</script>

<style scoped>
.collapsed-sidebar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 6px;
  background: var(--bg-white);
  border-radius: 16px;
  flex-shrink: 0;
}

.collapsed-icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  position: relative;
}

.collapsed-icon-btn:hover:not(.disabled) {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.collapsed-icon-btn.disabled {
  color: var(--text-tertiary);
  opacity: 0.6;
  cursor: not-allowed;
}

.icon-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background: var(--primary-color);
  color: white;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
