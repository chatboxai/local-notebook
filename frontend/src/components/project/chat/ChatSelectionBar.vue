<template>
  <div class="selection-action-bar">
    <div class="selection-info">
      <button class="select-all-btn" @click="emit('toggle-all')">
        {{ allSelected ? '取消全选' : '全选' }}
      </button>
      <span class="selected-count">已选中 {{ selectedCount }} 项</span>
    </div>
    <div class="selection-actions">
      <button class="selection-cancel-btn" @click="emit('cancel')">取消</button>
      <button
        class="selection-export-btn"
        :disabled="exportDisabled"
        @click="emit('export')"
      >
        {{ isExporting ? '导出中...' : '导出为 Word' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  selectedCount: number
  allSelected: boolean
  isExporting: boolean
  exportDisabled: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'toggle-all': []
  cancel: []
  export: []
}>()
</script>

<style scoped>
.selection-action-bar {
  position: absolute;
  bottom: 80px;
  left: 20px;
  right: 20px;
  padding: 12px 20px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.selection-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.select-all-btn {
  padding: 4px 8px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
}

.select-all-btn:hover {
  background: var(--bg-hover);
}

.selected-count {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.selection-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-cancel-btn {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
}

.selection-export-btn {
  padding: 6px 16px;
  background: var(--primary-color);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.selection-export-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.selection-export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
