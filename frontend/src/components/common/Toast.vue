<template>
  <Teleport to="body">
    <Transition name="toast-fade">
      <div v-if="visible" class="toast-notification" :class="typeClass">
        <svg v-if="type === 'success'" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
        </svg>
        <svg v-else-if="type === 'error'" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
        <svg v-else-if="type === 'warning'" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
        </svg>
        <span>{{ message }}</span>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  visible: boolean
  message: string
  type?: 'success' | 'error' | 'info' | 'warning'
}>(), {
  type: 'success'
})

const typeClass = computed(() => `toast-${props.type}`)
</script>

<style scoped>
.toast-notification {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: var(--bg-white);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10001;
  font-size: 14px;
  color: var(--text-primary);
}

.toast-success svg {
  color: #4caf50;
}

.toast-error {
  background: rgba(244, 67, 54, 0.85);
  color: white;
}

.toast-error svg {
  color: white;
}

.toast-info svg {
  color: #2196f3;
}

.toast-warning svg {
  color: #ff9800;
}


.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}
</style>
