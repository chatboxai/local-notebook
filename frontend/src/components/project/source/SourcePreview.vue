<template>
  <div class="panel-header">
    <span class="panel-title">{{ $t('ui.sources2') }}</span>
    <button class="panel-toggle-btn" @click="emit('close-preview')" :title="$t('ui.backToList')">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
        <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
      </svg>
    </button>
  </div>

  <div class="preview-file-header">
    <div class="preview-file-name">
      <svg v-if="isPreviewingImage" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
        <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
        <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
      </svg>
      <span>{{ previewingFileName }}</span>
    </div>

    <div v-if="isPdfFile && supportsRawView" class="view-toggle">
      <button
        class="view-toggle-btn"
        :class="{ active: viewMode === 'raw' }"
        @click="emit('switch-view-mode', 'raw')"
        :title="$t('ui.originalView')"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/>
        </svg>
        {{ $t('ui.original') }}
      </button>
      <button
        class="view-toggle-btn"
        :class="{ active: viewMode === 'parsed' }"
        @click="emit('switch-view-mode', 'parsed')"
        :title="$t('ui.parsedView')"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/>
        </svg>
        {{ $t('ui.parsed') }}
      </button>
    </div>
  </div>

  <template v-if="isPreviewingImage">
    <div class="preview-content image-preview-content" ref="previewContentRef">
      <div v-if="isLoadingContent" class="preview-loading">{{ $t('ui.loading') }}</div>
      <div v-else class="image-preview-wrapper">
        <img
          v-if="previewingFile"
          :src="getImagePreviewUrl(previewingFile.id)"
          :alt="previewingFileName"
          class="preview-image"
        />
      </div>
    </div>
  </template>

  <template v-else>
    <div v-if="previewSummary" class="source-guide-card">
      <div class="source-guide-header">
        <div class="source-guide-title">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7zm2.85 11.1l-.85.6V16h-4v-2.3l-.85-.6A4.997 4.997 0 0 1 7 9c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.63-.8 3.16-2.15 4.1z"/>
          </svg>
          <span>{{ $t('ui.sourceGuide') }}</span>
        </div>
        <button class="source-guide-toggle" @click="summaryExpandedModel = !summaryExpandedModel">
          <svg :class="{ rotated: !summaryExpanded }" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
          </svg>
        </button>
      </div>
      <div v-show="summaryExpanded" class="source-guide-content" v-html="renderSummary(previewSummary)"></div>

      <div v-show="summaryExpanded" v-if="previewingFileContent?.keywords?.length" class="source-guide-keywords">
        <span
          v-for="(keyword, index) in previewingFileContent.keywords"
          :key="index"
          class="keyword-tag"
          @click="emit('keyword-click', keyword)"
        >{{ keyword }}</span>
      </div>
    </div>

    <div class="preview-content-wrapper">
      <div class="preview-content" ref="previewContentRef" @scroll="emit('preview-scroll')">
        <div v-if="isLoadingContent" class="preview-loading">{{ $t('ui.loading') }}</div>

        <PdfViewer
          v-if="isRawViewMode && pdfPageInfo && previewingFile"
          ref="pdfViewerRef"
          :file-id="previewingFile.id"
          :page-info="pdfPageInfo"
          @page-change="emit('page-change', $event)"
          @block-click="(block, position) => emit('pdf-block-click', block, position)"
          @clear-selection="emit('pdf-clear-selection')"
          @loading="emit('pdf-loading', $event)"
        />

        <template v-else-if="isPdfFile && visibleParsedPages.length > 0">
          <div
            v-for="pageNum in visibleParsedPages"
            :key="pageNum"
            :data-page="pageNum"
            class="parsed-page-section"
          >
            <div class="page-divider">
              <span class="page-divider-line"></span>
              <span class="page-divider-text">{{ $t('ui.pageNumber', { page: pageNum }) }}</span>
              <span class="page-divider-line"></span>
            </div>

            <div class="parsed-page-content">
              <SourceBlockList
                :blocks="parsedBlocksByPage.get(pageNum) || []"
                :highlight-block-ids="highlightBlockIds"
                :previewing-file-id="previewingFile?.id ?? null"
                :previewing-file-name="previewingFileName"
              />
            </div>
          </div>
        </template>

        <template v-else-if="isPreviewingAudio && previewingFileContent?.blocks">
          <div class="audio-preview-shell">
            <div class="audio-player-bar">
              <audio
                v-if="previewingFile"
                ref="audioPlayerRef"
                class="audio-player"
                :src="audioPreviewUrl"
                controls
                preload="metadata"
                @timeupdate="emit('audio-time-update')"
                @play="emit('audio-play')"
              ></audio>
            </div>

            <div class="audio-transcript-list">
              <section
                v-for="group in audioTranscriptGroups"
                :key="group.key"
                class="audio-transcript-group"
              >
                <div v-if="audioSpeakerCount > 1" class="audio-speaker-label">
                  {{ group.speakerLabel }}
                </div>
                <p class="audio-paragraph">
                  <button
                    v-for="block in group.blocks"
                    :key="block.block_id"
                    type="button"
                    :data-block-id="block.block_id"
                    class="audio-text-segment"
                    :class="{
                      highlighted: highlightBlockIds.includes(block.block_id),
                      active: activeAudioBlockId === block.block_id
                    }"
                    @click="emit('seek-audio-to-block', block)"
                  >
                    {{ block.content }}
                  </button>
                </p>
              </section>
            </div>
          </div>
        </template>

        <template v-else-if="previewingFileContent?.blocks">
          <SourceBlockList
            :blocks="previewingFileContent.blocks"
            :highlight-block-ids="highlightBlockIds"
            :previewing-file-id="previewingFile?.id ?? null"
            :previewing-file-name="previewingFileName"
          />
        </template>
      </div>

      <div v-if="isPdfFile && currentTotalPages > 0" class="page-nav-float">
        <span class="page-indicator">{{ $t('ui.pageIndicator', { current: currentPageNum, total: currentTotalPages }) }}</span>
        <div class="page-jump">
          <input
            type="number"
            v-model="jumpInput"
            :min="1"
            :max="currentTotalPages"
            :placeholder="$t('ui.page')"
            @keyup.enter="emit('jump-to-page')"
          />
          <button class="jump-btn" @click="emit('jump-to-page')">{{ $t('ui.go') }}</button>
        </div>
      </div>
    </div>
  </template>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import PdfViewer from '@/components/PdfViewer.vue'
import { getImagePreviewUrl, type FilePageInfo, type FoundBlock } from '@/services/api'
import type { FileContent, FileInfo } from '@/types'
import { renderSummary } from '@/utils'
import SourceBlockList from './SourceBlockList.vue'
import type { AudioTranscriptGroup, SourceViewMode } from './types'

const props = defineProps<{
  previewingFile: FileInfo | null
  previewingFileName: string
  previewingFileContent: FileContent | null
  previewSummary: string
  summaryExpanded: boolean
  isPreviewingImage: boolean
  isPreviewingAudio: boolean
  isPdfFile: boolean
  supportsRawView: boolean
  viewMode: SourceViewMode
  isRawViewMode: boolean
  isLoadingContent: boolean
  pdfPageInfo: FilePageInfo | null
  visibleParsedPages: number[]
  parsedBlocksByPage: Map<number, FileContent['blocks']>
  highlightBlockIds: string[]
  audioPreviewUrl: string
  audioTranscriptGroups: AudioTranscriptGroup[]
  audioSpeakerCount: number
  activeAudioBlockId: string | null
  currentTotalPages: number
  currentPageNum: number
  jumpToPageInput: string
}>()

const emit = defineEmits<{
  (e: 'close-preview'): void
  (e: 'update:summaryExpanded', value: boolean): void
  (e: 'switch-view-mode', mode: SourceViewMode): void
  (e: 'keyword-click', keyword: string): void
  (e: 'preview-scroll'): void
  (e: 'page-change', pageNum: number): void
  (e: 'pdf-block-click', block: FoundBlock, position: { top: number; left: number }): void
  (e: 'pdf-clear-selection'): void
  (e: 'pdf-loading', loading: boolean): void
  (e: 'audio-time-update'): void
  (e: 'audio-play'): void
  (e: 'seek-audio-to-block', block: FileContent['blocks'][number]): void
  (e: 'update:jumpToPageInput', value: string): void
  (e: 'jump-to-page'): void
}>()

const previewContentRef = ref<HTMLDivElement | null>(null)
const audioPlayerRef = ref<HTMLAudioElement | null>(null)
const pdfViewerRef = ref<InstanceType<typeof PdfViewer> | null>(null)

const summaryExpandedModel = computed({
  get: () => props.summaryExpanded,
  set: (value: boolean) => emit('update:summaryExpanded', value),
})

const jumpInput = computed({
  get: () => props.jumpToPageInput,
  set: (value: string) => emit('update:jumpToPageInput', value),
})

const previewContentEl = computed(() => previewContentRef.value)
const audioPlayerEl = computed(() => audioPlayerRef.value)
const totalPages = computed(() => pdfViewerRef.value?.totalPages || 0)
const isDocumentLoaded = computed(() => Boolean(pdfViewerRef.value?.isDocumentLoaded))

function clearHighlights() {
  pdfViewerRef.value?.clearHighlights()
}

function clearSelectedBlock() {
  pdfViewerRef.value?.clearSelectedBlock()
}

function goToPage(pageNum: number) {
  pdfViewerRef.value?.goToPage(pageNum)
}

async function scrollToSegment(segmentId: string) {
  await pdfViewerRef.value?.scrollToSegment(segmentId)
}

async function scrollToPageAndHighlightBbox(pageNum: number, bbox?: number[]) {
  await pdfViewerRef.value?.scrollToPageAndHighlightBbox(pageNum, bbox)
}

defineExpose({
  previewContentEl,
  audioPlayerEl,
  totalPages,
  isDocumentLoaded,
  clearHighlights,
  clearSelectedBlock,
  goToPage,
  scrollToSegment,
  scrollToPageAndHighlightBbox,
})
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

.preview-file-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.preview-file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 0;
  flex: 1;
}

.preview-file-name span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-file-name svg {
  color: #1a73e8;
  flex-shrink: 0;
}

.view-toggle {
  display: flex;
  gap: 4px;
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 3px;
  flex-shrink: 0;
}

.view-toggle-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.view-toggle-btn:hover {
  color: var(--text-primary);
  background: rgba(0, 0, 0, 0.04);
}

.view-toggle-btn.active {
  background: white;
  color: var(--primary-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.view-toggle-btn svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.source-guide-card {
  margin: 12px 16px;
  border: 1.5px dashed rgba(0, 0, 0, 0.12);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(249, 250, 251, 0.8) 0%, rgba(243, 244, 246, 0.6) 100%);
  overflow: hidden;
}

.source-guide-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px 8px;
}

.source-guide-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.source-guide-title svg {
  color: var(--primary-color);
  width: 20px;
  height: 20px;
}

.source-guide-toggle {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.source-guide-toggle svg {
  width: 22px;
  height: 22px;
  transition: transform 0.2s;
}

.source-guide-toggle:hover {
  background: rgba(0, 0, 0, 0.08);
  color: var(--text-secondary);
}

.source-guide-toggle svg.rotated {
  transform: rotate(-90deg);
}

.source-guide-content {
  padding: 0 14px 14px;
  font-size: 14px;
  line-height: 1.8;
  color: #1a1a1a;
}

.source-guide-content :deep(strong) {
  color: #1a5c5c;
  font-weight: 600;
}

.source-guide-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 4px 14px 14px;
}

.keyword-tag {
  display: inline-block;
  padding: 4px 12px;
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.15s;
}

.keyword-tag:hover {
  background: var(--primary-light);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  scroll-behavior: smooth;
}

.preview-content-wrapper {
  position: relative;
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.page-nav-float {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 10;
  backdrop-filter: blur(8px);
}

.page-nav-float .page-indicator {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

.page-nav-float .page-jump {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-nav-float .page-jump input {
  width: 50px;
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 12px;
  text-align: center;
  background: var(--bg-white);
  color: var(--text-primary);
}

.page-nav-float .page-jump input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.page-nav-float .page-jump input::-webkit-outer-spin-button,
.page-nav-float .page-jump input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.page-nav-float .page-jump input[type=number] {
  -moz-appearance: textfield;
}

.page-nav-float .jump-btn {
  padding: 4px 10px;
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.page-nav-float .jump-btn:hover {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.parsed-page-section {
  margin-bottom: 24px;
}

.parsed-page-content {
  padding: 0 4px;
}

.page-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0 16px;
  padding: 0 4px;
}

.page-divider:first-child {
  margin-top: 0;
}

.page-divider-line {
  flex: 1;
  height: 1px;
  background: var(--border-color);
}

.page-divider-text {
  font-size: 12px;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.image-preview-content {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 20px;
}

.image-preview-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 600px;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-loading {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.preview-loading::before {
  content: '';
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: loadingSpin 0.8s linear infinite;
}

@keyframes loadingSpin {
  to {
    transform: rotate(360deg);
  }
}

.audio-preview-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.audio-player-bar {
  position: sticky;
  top: 0;
  z-index: 4;
  padding: 0 0 6px;
  background: var(--bg-white);
}

.audio-player {
  width: 100%;
  height: 36px;
}

.audio-transcript-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.audio-transcript-group {
  padding: 2px 0;
}

.audio-speaker-label {
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 600;
}

.audio-paragraph {
  margin: 0;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.9;
  word-break: break-word;
}

.audio-text-segment {
  display: inline;
  margin: 0 2px 0 0;
  padding: 1px 2px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: inherit;
  font: inherit;
  line-height: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.audio-text-segment:hover {
  background: var(--bg-hover);
}

.audio-text-segment.highlighted {
  background: rgba(147, 51, 234, 0.12);
  animation: highlightFadeIn 0.3s ease-out;
}

.audio-text-segment.active {
  background: rgba(37, 99, 235, 0.16);
  color: var(--primary-color);
}

@keyframes highlightFadeIn {
  0% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}
</style>
