<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="confirm-overlay" @click.self="handleCancel">
        <div class="confirm-dialog">
          <div class="confirm-icon" :class="type">
            <svg v-if="type === 'warning'" viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
            <svg v-else-if="type === 'danger'" viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
              <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <div class="confirm-content">
            <h3 class="confirm-title">{{ title }}</h3>
            <p class="confirm-message">{{ message }}</p>
          </div>
          <div class="confirm-actions">
            <button class="confirm-btn cancel" @click="handleCancel">
              {{ cancelText }}
            </button>
            <button class="confirm-btn confirm" :class="type" @click="handleConfirm">
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean
  title: string
  message: string
  type?: 'info' | 'warning' | 'danger'
  confirmText?: string
  cancelText?: string
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
  (e: 'update:visible', value: boolean): void
}>()

function handleConfirm() {
  emit('confirm')
  emit('update:visible', false)
}

function handleCancel() {
  emit('cancel')
  emit('update:visible', false)
}
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(2px);
}

.confirm-dialog {
  background: white;
  border-radius: 16px;
  padding: 24px;
  width: 380px;
  max-width: 90vw;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.confirm-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.confirm-icon.info {
  background: #e8f5e9;
  color: #4caf50;
}

.confirm-icon.warning {
  background: #fff3e0;
  color: #ff9800;
}

.confirm-icon.danger {
  background: #ffebee;
  color: #f44336;
}

.confirm-content {
  margin-bottom: 24px;
}

.confirm-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.confirm-message {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
  white-space: pre-line;
}

.confirm-actions {
  display: flex;
  gap: 12px;
  width: 100%;
}

.confirm-btn {
  flex: 1;
  padding: 12px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.confirm-btn.cancel {
  background: #f3f4f6;
  color: #4b5563;
}

.confirm-btn.cancel:hover {
  background: #e5e7eb;
}

.confirm-btn.confirm {
  background: #3b82f6;
  color: white;
}

.confirm-btn.confirm:hover {
  background: #2563eb;
}

.confirm-btn.confirm.warning {
  background: #ff9800;
}

.confirm-btn.confirm.warning:hover {
  background: #f57c00;
}

.confirm-btn.confirm.danger {
  background: #f44336;
}

.confirm-btn.confirm.danger:hover {
  background: #d32f2f;
}


.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .confirm-dialog,
.modal-leave-active .confirm-dialog {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from .confirm-dialog,
.modal-leave-to .confirm-dialog {
  transform: scale(0.95);
  opacity: 0;
}
</style>
