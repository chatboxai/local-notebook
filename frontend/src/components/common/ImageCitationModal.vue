<template>
  <Teleport to="body">
    <div v-if="visible" class="image-citation-modal-overlay" @click.self="handleClose">
      <div class="image-citation-modal">
        <div class="image-citation-modal-header">
          <div class="image-citation-modal-title">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
            </svg>
            <span>{{ fileName }}</span>
          </div>
          <button class="image-citation-modal-close" @click="handleClose">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        <div class="image-citation-modal-body">
          <div class="image-citation-preview">
            <img :src="previewUrl" :alt="fileName" />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean
  fileName: string
  previewUrl: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

function handleClose() {
  emit('close')
}
</script>

<style scoped>
.image-citation-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.image-citation-modal {
  max-width: 90vw;
  max-height: 90vh;
  background: var(--bg-white);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: scaleIn 0.2s ease;
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.image-citation-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-main);
}

.image-citation-modal-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.image-citation-modal-title svg {
  color: var(--primary-color);
}

.image-citation-modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
}

.image-citation-modal-close:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.image-citation-modal-body {
  padding: 20px;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-citation-preview {
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-citation-preview img {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
  border-radius: 8px;
}
</style>
