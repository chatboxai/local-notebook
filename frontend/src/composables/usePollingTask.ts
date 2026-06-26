import { onUnmounted, ref } from 'vue'

interface PollingTaskOptions {
  run: () => Promise<void> | void
  getDelay?: () => number
  retryDelay?: number
  pauseWhenHidden?: boolean
  refreshOnVisible?: boolean
  canRun?: () => boolean
  onError?: (error: unknown) => void
}

const DEFAULT_POLLING_DELAY_MS = 30000

export function usePollingTask(options: PollingTaskOptions) {
  const active = ref(false)
  const running = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null
  let disposed = false

  const pauseWhenHidden = options.pauseWhenHidden ?? true
  const refreshOnVisible = options.refreshOnVisible ?? true

  function getDelay(): number {
    return options.getDelay?.() ?? DEFAULT_POLLING_DELAY_MS
  }

  function isHidden(): boolean {
    return pauseWhenHidden && typeof document !== 'undefined' && document.hidden
  }

  function clearTimer() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  function schedule(delay = getDelay()) {
    clearTimer()
    if (disposed || !active.value || isHidden()) return

    timer = setTimeout(() => {
      void runNow()
    }, delay)
  }

  async function runNow() {
    if (disposed || !active.value || isHidden()) return

    if (running.value || options.canRun?.() === false) {
      schedule(options.retryDelay ?? getDelay())
      return
    }

    running.value = true
    try {
      await options.run()
    } catch (error) {
      options.onError?.(error)
    } finally {
      running.value = false
      schedule()
    }
  }

  function start(delay = getDelay()) {
    if (disposed) return
    active.value = true
    schedule(delay)
  }

  function stop() {
    active.value = false
    clearTimer()
  }

  function handleVisibilityChange() {
    if (!active.value || !pauseWhenHidden) return

    if (document.hidden) {
      clearTimer()
    } else if (refreshOnVisible) {
      void runNow()
    } else {
      schedule()
    }
  }

  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', handleVisibilityChange)
  }

  onUnmounted(() => {
    disposed = true
    stop()
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  })

  return {
    active,
    running,
    start,
    stop,
    schedule,
    runNow,
  }
}
