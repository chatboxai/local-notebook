<template>
  <Transition name="copy-toast">
    <div v-if="visible" class="copy-toast">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
      </svg>
      {{ message }}
    </div>
  </Transition>
</template>

<script setup lang="ts">
interface Props {
  visible: boolean
  message: string
}

defineProps<Props>()
</script>

<style scoped>
.copy-toast {
  position: absolute;
  top: 10%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: rgba(240, 249, 240, 0.98);
  backdrop-filter: blur(8px);
  color: #2e7d32;
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 100;
  pointer-events: none;
}

.copy-toast svg {
  flex-shrink: 0;
}

.copy-toast-enter-active,
.copy-toast-leave-active {
  transition: all 0.3s ease;
}

.copy-toast-enter-from,
.copy-toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.9);
}
</style>
