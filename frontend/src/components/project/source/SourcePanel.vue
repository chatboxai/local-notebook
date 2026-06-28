<template>
  <aside
    class="sources-panel"
    :class="{ collapsed }"
    :style="{ width: collapsed ? '0px' : width + 'px' }"
  >
    <SourcePreview
      v-if="showPreview"
      ref="sourcePreviewRef"
      :previewing-file="previewingFile"
      :previewing-file-name="previewingFileName"
      :previewing-file-content="previewingFileContent"
      :preview-summary="previewSummary"
      :summary-expanded="summaryExpanded"
      :is-previewing-image="isPreviewingImage"
      :is-previewing-audio="isPreviewingAudio"
      :is-pdf-file="isPdfFile"
      :supports-raw-view="supportsRawView"
      :view-mode="viewMode"
      :is-raw-view-mode="isRawViewMode"
      :is-loading-content="isLoadingContent"
      :pdf-page-info="pdfPageInfo"
      :visible-parsed-pages="visibleParsedPages"
      :parsed-blocks-by-page="parsedBlocksByPage"
      :highlight-block-ids="highlightBlockIds"
      :audio-preview-url="audioPreviewUrl"
      :audio-transcript-groups="audioTranscriptGroups"
      :audio-speaker-count="audioSpeakerCount"
      :active-audio-block-id="activeAudioBlockId"
      :current-total-pages="currentTotalPages"
      :current-page-num="currentPageNum"
      :jump-to-page-input="jumpToPageInput"
      @close-preview="emit('close-preview')"
      @update:summary-expanded="emit('update:summaryExpanded', $event)"
      @switch-view-mode="emit('switch-view-mode', $event)"
      @keyword-click="emit('keyword-click', $event)"
      @preview-scroll="emit('preview-scroll')"
      @page-change="emit('page-change', $event)"
      @pdf-block-click="(block, position) => emit('pdf-block-click', block, position)"
      @pdf-clear-selection="emit('pdf-clear-selection')"
      @pdf-loading="emit('pdf-loading', $event)"
      @audio-time-update="emit('audio-time-update')"
      @audio-play="emit('audio-play')"
      @seek-audio-to-block="emit('seek-audio-to-block', $event)"
      @update:jump-to-page-input="emit('update:jumpToPageInput', $event)"
      @jump-to-page="emit('jump-to-page')"
    />

    <SourceList
      v-else
      :files="files"
      :sorted-files="sortedFiles"
      :ready-files="readyFiles"
      :selected-file-ids="selectedFileIds"
      :uploading-files="uploadingFiles"
      :hovering-file-id="hoveringFileId"
      :open-menu-file-id="openMenuFileId"
      :is-all-selected="isAllSelected"
      @toggle-collapse="emit('toggle-collapse')"
      @trigger-file-upload="emit('trigger-file-upload')"
      @toggle-select-all="emit('toggle-select-all')"
      @open-file-preview="emit('open-file-preview', $event)"
      @set-hovering-file="emit('set-hovering-file', $event)"
      @toggle-file-menu="emit('toggle-file-menu', $event)"
      @rename-file="(fileId, fileName) => emit('rename-file', fileId, fileName)"
      @delete-file="emit('delete-file', $event)"
      @toggle-file-selection="emit('toggle-file-selection', $event)"
    />
  </aside>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FilePageInfo, FoundBlock } from '@/services/api'
import type { FileContent, FileInfo } from '@/types'
import SourceList from './SourceList.vue'
import SourcePreview from './SourcePreview.vue'
import type { AudioTranscriptGroup, SourceViewMode, UploadingFile } from './types'

defineProps<{
  collapsed: boolean
  width: number
  showPreview: boolean
  files: FileInfo[]
  sortedFiles: FileInfo[]
  readyFiles: FileInfo[]
  selectedFileIds: string[]
  uploadingFiles: UploadingFile[]
  hoveringFileId: string | null
  openMenuFileId: string | null
  isAllSelected: boolean
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
  (e: 'toggle-collapse'): void
  (e: 'trigger-file-upload'): void
  (e: 'toggle-select-all'): void
  (e: 'open-file-preview', fileId: string): void
  (e: 'set-hovering-file', fileId: string | null): void
  (e: 'toggle-file-menu', fileId: string): void
  (e: 'rename-file', fileId: string, fileName: string): void
  (e: 'delete-file', fileId: string): void
  (e: 'toggle-file-selection', fileId: string): void
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

const sourcePreviewRef = ref<InstanceType<typeof SourcePreview> | null>(null)

const previewContentEl = computed(() => sourcePreviewRef.value?.previewContentEl ?? null)
const audioPlayerEl = computed(() => sourcePreviewRef.value?.audioPlayerEl ?? null)
const totalPages = computed(() => sourcePreviewRef.value?.totalPages || 0)
const isDocumentLoaded = computed(() => Boolean(sourcePreviewRef.value?.isDocumentLoaded))

function clearHighlights() {
  sourcePreviewRef.value?.clearHighlights()
}

function clearSelectedBlock() {
  sourcePreviewRef.value?.clearSelectedBlock()
}

function goToPage(pageNum: number) {
  sourcePreviewRef.value?.goToPage(pageNum)
}

async function scrollToSegment(segmentId: string) {
  await sourcePreviewRef.value?.scrollToSegment(segmentId)
}

async function scrollToPageAndHighlightBbox(pageNum: number, bbox?: number[]) {
  await sourcePreviewRef.value?.scrollToPageAndHighlightBbox(pageNum, bbox)
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
.sources-panel {
  background: var(--bg-white);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  transition: width 0.2s ease;
}

.sources-panel.collapsed {
  padding: 0;
  border: none;
  overflow: hidden;
  min-width: 0;
}

.sources-panel.collapsed > * {
  display: none;
}
</style>
