<template>
  <div class="panel-header">
    <span class="panel-title">{{ $t('ui.sources2') }}</span>
    <button class="panel-toggle-btn" @click="emit('toggle-collapse')" :title="$t('ui.collapsePanel')">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/>
        <path d="M7 7h4v10H7z" opacity="0.5"/>
      </svg>
    </button>
  </div>

  <button class="add-source-btn" @click="emit('trigger-file-upload')">
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
      <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
    </svg>
    {{ $t('ui.addSource') }}
  </button>

  <div v-if="uploadingFiles.length > 0" class="upload-progress-container">
    <div
      v-for="(item, index) in uploadingFiles"
      :key="index"
      class="upload-progress-item"
      :class="item.status"
    >
      <div class="upload-file-name">{{ item.name }}</div>
      <div class="upload-progress-bar">
        <div
          class="upload-progress-fill"
          :style="{ width: item.progress + '%' }"
        ></div>
      </div>
      <div class="upload-status">
        <template v-if="item.status === 'uploading'">{{ item.progress }}%</template>
        <template v-else-if="item.status === 'success'">{{ $t('ui.done') }}</template>
        <template v-else-if="item.status === 'error'">{{ $t('ui.failed') }}</template>
      </div>
    </div>
  </div>

  <div v-if="readyFiles.length > 0" class="select-all-row" @click="emit('toggle-select-all')">
    <span>{{ $t('ui.selectAllSources') }}</span>
    <div class="select-all-check" :class="{ checked: isAllSelected }">
      <svg v-if="isAllSelected" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
      </svg>
    </div>
  </div>

  <div class="sources-list">
    <div v-if="files.length === 0" class="empty-sources">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
          <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
        </svg>
      </div>
      <p>{{ $t('ui.savedSourcesWillAppearHere') }}</p>
      <p class="hint">{{ $t('ui.clickAddSourceAboveToAddPdfOr') }}</p>
    </div>

    <div
      v-for="file in sortedFiles"
      :key="file.id"
      class="source-item"
      :class="{
        selected: selectedFileIds.includes(file.id),
        processing: file.status === 'processing',
        pending: file.status === 'pending',
        ready: file.status === 'ready'
      }"
      @click="file.status === 'ready' && emit('open-file-preview', file.id)"
      @mouseenter="emit('set-hovering-file', file.id)"
      @mouseleave="emit('set-hovering-file', null)"
    >
      <div class="source-left">
        <div v-if="hoveringFileId === file.id && (file.status === 'ready' || file.status === 'failed')" class="source-menu-wrapper">
          <button
            class="source-menu-btn"
            @click.stop="emit('toggle-file-menu', file.id)"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
            </svg>
          </button>

          <div v-if="openMenuFileId === file.id" class="source-dropdown">
            <button v-if="file.status === 'ready'" class="dropdown-item" @click.stop="emit('rename-file', file.id, file.file_name)">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
              </svg>
              {{ $t('ui.rename') }}
            </button>
            <button class="dropdown-item danger" @click.stop="emit('delete-file', file.id)">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
              </svg>
              {{ $t('ui.delete') }}
            </button>
          </div>
        </div>

        <div v-else class="source-icon" :class="{ 'image-icon': isImageFile(file), 'audio-icon': isAudioFile(file) }">
          <svg v-if="isImageFile(file)" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
          </svg>

          <svg v-else-if="isAudioFile(file)" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
          </svg>

          <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
          </svg>
        </div>
      </div>

      <div class="source-info">
        <span class="source-name">{{ file.file_name }}</span>
        <span
          v-if="file.status !== 'ready'"
          class="source-status"
          :class="file.status"
          :title="file.status === 'failed' ? (file.error_message || '') : ''"
        >
          {{ getSourceStatusText(file) }}
          <span v-if="file.status === 'failed' && file.error_message" class="source-status-reason">
            {{ file.error_message }}
          </span>
        </span>
        <div v-if="hasProcessingProgress(file)" class="source-processing-progress" aria-hidden="true">
          <div
            class="source-processing-fill"
            :style="{ width: getProcessingProgressPercent(file) + '%' }"
          ></div>
        </div>
      </div>

      <div v-if="file.status === 'ready'" class="source-right">
        <div
          class="source-checkbox"
          :class="{ checked: selectedFileIds.includes(file.id) }"
          @click.stop="emit('toggle-file-selection', file.id)"
        >
          <svg v-if="selectedFileIds.includes(file.id)" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FileInfo } from '@/types'
import { t } from '@/i18n'
import {
  getStatusText,
  isAudioFile,
  isImageFile,
} from '@/views/projectPage/fileHelpers'
import type { UploadingFile } from './types'

defineProps<{
  files: FileInfo[]
  sortedFiles: FileInfo[]
  readyFiles: FileInfo[]
  selectedFileIds: string[]
  uploadingFiles: UploadingFile[]
  hoveringFileId: string | null
  openMenuFileId: string | null
  isAllSelected: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle-collapse'): void
  (e: 'trigger-file-upload'): void
  (e: 'toggle-select-all'): void
  (e: 'open-file-preview', fileId: string): void
  (e: 'set-hovering-file', fileId: string | null): void
  (e: 'toggle-file-menu', fileId: string): void
  (e: 'rename-file', fileId: string, fileName: string): void
  (e: 'delete-file', fileId: string): void
  (e: 'toggle-file-selection', fileId: string): void
}>()

function getProcessingNumbers(file: FileInfo): { current: number; total: number } | null {
  const total = Number(file.processing_total || 0)
  if (!Number.isFinite(total) || total <= 0) return null
  const rawCurrent = Number(file.processing_current || 0)
  const current = Math.max(0, Math.min(total, Number.isFinite(rawCurrent) ? rawCurrent : 0))
  return { current, total }
}

function hasProcessingProgress(file: FileInfo): boolean {
  return file.status === 'processing' && getProcessingNumbers(file) !== null
}

function getProcessingProgressPercent(file: FileInfo): number {
  const progress = getProcessingNumbers(file)
  if (!progress) return 0
  return Math.round((progress.current / progress.total) * 100)
}

function getSourceStatusText(file: FileInfo): string {
  if (file.status === 'processing') {
    const progress = getProcessingNumbers(file)
    if (progress) return t('ui.processingProgress', progress)
    return file.processing_message || t('ui.readyToProcess')
  }
  return getStatusText(file.status)
}
</script>

<style scoped>
.panel-header {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  overflow: visible;
  position: relative;
  z-index: 10;
}

.panel-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.panel-toggle-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 6px;
  color: var(--text-tertiary);
  transition: background 0.15s, color 0.15s;
}

.panel-toggle-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.add-source-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 12px 20px;
  padding: 12px 20px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 24px;
  color: var(--text-primary);
  font-size: 15px;
}

.add-source-btn:hover {
  background: var(--bg-hover);
}

.upload-progress-container {
  padding: 8px 12px;
  margin-top: 8px;
  background: var(--bg-main);
  border-radius: 8px;
}

.upload-progress-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  background: var(--bg-white);
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid var(--border-color);
}

.upload-progress-item:last-child {
  margin-bottom: 0;
}

.upload-progress-item.success {
  background: rgba(82, 196, 26, 0.08);
  border-color: rgba(82, 196, 26, 0.3);
}

.upload-progress-item.error {
  background: rgba(255, 77, 79, 0.08);
  border-color: rgba(255, 77, 79, 0.3);
}

.upload-file-name {
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-progress-bar {
  height: 6px;
  background: var(--border-color);
  border-radius: 3px;
  overflow: hidden;
}

.upload-progress-fill {
  height: 100%;
  background: var(--primary-color);
  border-radius: 3px;
  transition: width 0.2s ease;
}

.upload-progress-item.success .upload-progress-fill {
  background: #52c41a;
}

.upload-progress-item.error .upload-progress-fill {
  background: #ff4d4f;
}

.upload-status {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: right;
}

.upload-progress-item.success .upload-status {
  color: #52c41a;
}

.upload-progress-item.error .upload-status {
  color: #ff4d4f;
}

.select-all-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 28px 8px 16px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
}

.select-all-row:hover {
  background: var(--bg-hover);
}

.select-all-check {
  position: relative;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1.5px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-tertiary);
  transition: all 0.15s;
}

.select-all-check::before {
  content: '';
  position: absolute;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: transparent;
  transition: background 0.15s;
}

.select-all-row:hover .select-all-check::before {
  background: rgba(0, 0, 0, 0.04);
}

.select-all-row:hover .select-all-check {
  border-color: var(--text-tertiary);
}

.select-all-check.checked {
  background: var(--text-tertiary);
  border-color: var(--text-tertiary);
  color: white;
}

.select-all-row:hover .select-all-check.checked::before {
  background: rgba(0, 0, 0, 0.06);
}

.sources-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.empty-sources {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
  font-size: 13px;
}

.empty-sources .empty-icon {
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.empty-sources p {
  font-size: 14px;
  margin-bottom: 10px;
}

.empty-sources .hint {
  font-size: 13px;
  color: var(--text-tertiary);
}

.source-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.3s;
  position: relative;
}

.source-item:hover {
  background: var(--bg-hover);
}

.source-item.ready:hover {
  background: var(--bg-hover);
}

.source-item.pending {
  cursor: not-allowed;
  background: rgba(0, 0, 0, 0.03);
}

.source-item.pending:hover {
  background: rgba(0, 0, 0, 0.05);
}

.source-item.processing {
  cursor: not-allowed;
  background: linear-gradient(
    90deg,
    rgba(74, 155, 168, 0.05) 0%,
    rgba(74, 155, 168, 0.12) 50%,
    rgba(74, 155, 168, 0.05) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 2s ease-in-out infinite;
}

.source-item.processing:hover {
  background: linear-gradient(
    90deg,
    rgba(74, 155, 168, 0.08) 0%,
    rgba(74, 155, 168, 0.15) 50%,
    rgba(74, 155, 168, 0.08) 100%
  );
  background-size: 200% 100%;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.source-left {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.source-icon {
  color: #1a73e8;
  flex-shrink: 0;
}

.source-icon.image-icon {
  color: #34a853;
}

.source-icon.audio-icon {
  color: #9333ea;
}

.source-menu-wrapper {
  position: relative;
}

.source-menu-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.source-menu-btn:hover {
  background: var(--bg-active);
  color: var(--text-primary);
}

.source-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  min-width: 120px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}

.dropdown-item:hover:not(.disabled) {
  background: var(--bg-hover);
}

.dropdown-item.disabled {
  color: var(--text-disabled);
  cursor: not-allowed;
}

.source-info {
  flex: 1;
  min-width: 0;
}

.source-name {
  display: block;
  font-size: 14px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-status {
  font-size: 12px;
  color: var(--text-tertiary);
}

.source-status.ready {
  color: var(--success-color);
}

.source-status.processing {
  color: var(--primary-color);
}

.source-processing-progress {
  width: 100%;
  height: 4px;
  margin-top: 5px;
  background: rgba(74, 155, 168, 0.14);
  border-radius: 999px;
  overflow: hidden;
}

.source-processing-fill {
  height: 100%;
  background: var(--primary-color);
  border-radius: inherit;
  transition: width 0.25s ease;
}

.source-status.error,
.source-status.failed {
  color: var(--error-color);
}

.source-status-reason {
  margin-left: 6px;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.source-right {
  flex-shrink: 0;
  margin-left: auto;
  cursor: pointer;
}

.source-checkbox {
  position: relative;
  width: 18px;
  height: 18px;
  border: 1.5px solid var(--border-color);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  background: transparent;
  cursor: pointer;
}

.source-checkbox::before {
  content: '';
  position: absolute;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: transparent;
  transition: background 0.15s;
}

.source-checkbox:hover::before {
  background: rgba(0, 0, 0, 0.04);
}

.source-checkbox:hover {
  border-color: var(--text-tertiary);
}

.source-checkbox.checked {
  background: var(--text-tertiary);
  border-color: var(--text-tertiary);
  color: white;
}

.source-checkbox.checked:hover::before {
  background: rgba(0, 0, 0, 0.06);
}
</style>
