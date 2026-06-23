<template>
  <Transition name="panel">
    <div v-if="visible" class="session-history-overlay" @click.self="$emit('close')">
      <div class="session-history-panel">
        <div class="panel-header">
          <h3>历史对话</h3>
          <button class="close-btn" @click="$emit('close')">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>

        <div class="panel-content">
          <div v-if="loading" class="loading-state">
            <span class="loading-spinner"></span>
            <span>加载中...</span>
          </div>

          <div v-else-if="sessions.length === 0" class="empty-state">
            <span>暂无历史对话</span>
          </div>

          <div v-else class="sessions-list">
            <div v-if="groupedSessions.today.length > 0" class="session-group">
              <div class="group-label">今天</div>
              <div
                v-for="session in groupedSessions.today"
                :key="session.id"
                class="session-item"
                :class="{ active: session.id === currentSessionId }"
                @click="$emit('select', session.id)"
              >
                <span class="session-title">{{ session.title || '新对话' }}</span>
                <span class="session-time">{{ formatRelativeTime(session.updated_at) }}</span>
                <button
                  class="delete-btn"
                  @click.stop="$emit('delete', session.id, session.title)"
                  title="删除"
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                  </svg>
                </button>
              </div>
            </div>

            <div v-if="groupedSessions.pastWeek.length > 0" class="session-group">
              <div class="group-label">最近7天</div>
              <div
                v-for="session in groupedSessions.pastWeek"
                :key="session.id"
                class="session-item"
                :class="{ active: session.id === currentSessionId }"
                @click="$emit('select', session.id)"
              >
                <span class="session-title">{{ session.title || '新对话' }}</span>
                <span class="session-time">{{ formatRelativeTime(session.updated_at) }}</span>
                <button
                  class="delete-btn"
                  @click.stop="$emit('delete', session.id, session.title)"
                  title="删除"
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                  </svg>
                </button>
              </div>
            </div>

            <div v-if="groupedSessions.pastMonth.length > 0" class="session-group">
              <div class="group-label">最近30天</div>
              <div
                v-for="session in groupedSessions.pastMonth"
                :key="session.id"
                class="session-item"
                :class="{ active: session.id === currentSessionId }"
                @click="$emit('select', session.id)"
              >
                <span class="session-title">{{ session.title || '新对话' }}</span>
                <span class="session-time">{{ formatRelativeTime(session.updated_at) }}</span>
                <button
                  class="delete-btn"
                  @click.stop="$emit('delete', session.id, session.title)"
                  title="删除"
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                  </svg>
                </button>
              </div>
            </div>

            <div v-if="groupedSessions.older.length > 0" class="session-group">
              <div class="group-label">更早</div>
              <div
                v-for="session in groupedSessions.older"
                :key="session.id"
                class="session-item"
                :class="{ active: session.id === currentSessionId }"
                @click="$emit('select', session.id)"
              >
                <span class="session-title">{{ session.title || '新对话' }}</span>
                <span class="session-time">{{ formatRelativeTime(session.updated_at) }}</span>
                <button
                  class="delete-btn"
                  @click.stop="$emit('delete', session.id, session.title)"
                  title="删除"
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Session } from '../types'
import { formatRelativeTime as formatLocalizedRelativeTime } from '../utils/format'

const props = defineProps<{
  visible: boolean
  sessions: Session[]
  currentSessionId: string | null
  loading?: boolean
}>()

defineEmits<{
  (e: 'close'): void
  (e: 'select', sessionId: string): void
  (e: 'delete', sessionId: string, title: string): void
}>()

const groupedSessions = computed(() => {
  const now = new Date()
  const today: Session[] = []
  const pastWeek: Session[] = []
  const pastMonth: Session[] = []
  const older: Session[] = []

  for (const session of props.sessions) {
    const updated = new Date(session.updated_at)
    const diffMs = now.getTime() - updated.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) today.push(session)
    else if (diffDays <= 7) pastWeek.push(session)
    else if (diffDays <= 30) pastMonth.push(session)
    else older.push(session)
  }

  return { today, pastWeek, pastMonth, older }
})

function formatRelativeTime(dateStr: string): string {
  return formatLocalizedRelativeTime(dateStr, {
    maxRelativeDays: 30,
    fallback: 'month',
  })
}
</script>

<style scoped>
.session-history-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 80px;
  z-index: 1000;
}

.session-history-panel {
  width: 420px;
  max-height: 70vh;
  background: var(--bg-white);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}

.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 20px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.sessions-list {
  display: flex;
  flex-direction: column;
}

.session-group {
  margin-bottom: 8px;
}

.group-label {
  padding: 8px 20px 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
}

.session-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  cursor: pointer;
  transition: background 0.15s;
}

.session-item:hover {
  background: var(--bg-hover);
}

.session-item.active {
  background: var(--primary-light);
}

.session-item.active .session-title {
  color: var(--primary-color);
  font-weight: 500;
}

.session-title {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 12px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  border-radius: 4px;
  cursor: pointer;
  opacity: 0;
  transition: all 0.15s;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.2s ease;
}

.panel-enter-active .session-history-panel,
.panel-leave-active .session-history-panel {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
}

.panel-enter-from .session-history-panel,
.panel-leave-to .session-history-panel {
  transform: translateY(-10px);
  opacity: 0;
}
</style>
