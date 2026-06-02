<template>
  <router-view />
  
  <Teleport to="body">
    <Transition name="toast-fade">
      <div v-if="globalToast.visible" class="global-toast" :class="globalToast.type">
        {{ globalToast.message }}
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'


const globalToast = ref({
  visible: false,
  message: '',
  type: 'warning' as 'success' | 'error' | 'warning' | 'info'
})

let toastTimer: number | null = null

function showToast(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'warning') {
  if (toastTimer) {
    clearTimeout(toastTimer)
  }

  globalToast.value = {
    visible: true,
    message,
    type
  }

  toastTimer = window.setTimeout(() => {
    globalToast.value.visible = false
  }, 3000)
}

function handleGlobalToast(event: Event) {
  const customEvent = event as CustomEvent<{ message: string; type: 'success' | 'error' | 'warning' | 'info' }>
  showToast(customEvent.detail.message, customEvent.detail.type)
}

onMounted(() => {
  window.addEventListener('global-toast', handleGlobalToast)
})

onUnmounted(() => {
  window.removeEventListener('global-toast', handleGlobalToast)
  if (toastTimer) {
    clearTimeout(toastTimer)
  }
})
</script>

<style>

.global-toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  color: #fff;
  z-index: 10000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  pointer-events: none;
}

.global-toast.warning {
  background: rgba(245, 158, 11, 0.9);
}

.global-toast.error {
  background: rgba(239, 68, 68, 0.9);
}

.global-toast.success {
  background: rgba(34, 197, 94, 0.9);
}

.global-toast.info {
  background: rgba(59, 130, 246, 0.9);
}


.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.3s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}
</style>
