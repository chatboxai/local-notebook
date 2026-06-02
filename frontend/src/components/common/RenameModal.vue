<template>
  <Teleport to="body">
    <div v-if="visible" class="rename-modal-overlay" @click="handleClose">
      <div class="rename-modal" @click.stop>
        <h3 class="rename-modal-title">{{ title }}</h3>
        <input
          ref="inputRef"
          v-model="inputValue"
          class="rename-modal-input"
          :placeholder="placeholder"
          @keydown.enter="handleEnter"
          @keydown.escape="handleClose"
          @compositionstart="isComposing = true"
          @compositionend="isComposing = false"
        />
        <div class="rename-modal-actions">
          <button class="btn-cancel" @click="handleClose">取消</button>
          <button
            class="btn-confirm"
            :disabled="!inputValue.trim() || saving"
            @click="handleConfirm"
          >
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{
  visible: boolean
  title: string
  placeholder?: string
  initialValue: string
  saving?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'confirm', value: string): void
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const inputValue = ref('')
const isComposing = ref(false)


watch(() => props.visible, (newVal) => {
  if (newVal) {
    inputValue.value = props.initialValue
    nextTick(() => {
      inputRef.value?.focus()
      inputRef.value?.select()
    })
  }
})

function handleClose() {
  emit('update:visible', false)
}

function handleEnter() {
  if (isComposing.value) return
  handleConfirm()
}

function handleConfirm() {
  const trimmed = inputValue.value.trim()
  if (!trimmed) return
  emit('confirm', trimmed)
}
</script>

<style scoped>
.rename-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.rename-modal {
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  padding: 24px;
  width: 400px;
  max-width: 90vw;
  box-shadow: var(--shadow-lg);
}

.rename-modal-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px;
}

.rename-modal-input {
  width: 100%;
  padding: 12px 14px;
  font-size: 14px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-white);
  color: var(--text-primary);
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.rename-modal-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.rename-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.btn-cancel {
  padding: 10px 20px;
  background: var(--bg-hover);
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.btn-cancel:hover {
  background: var(--border-light);
}

.btn-confirm {
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  font-size: 14px;
  transition: opacity 0.2s;
}

.btn-confirm:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
