<template>
  <div class="feature-detail-panel">
    <div class="panel-header">

      <div class="panel-title-row">
        <input
          v-if="isEditingTitle"
          ref="titleInputRef"
          v-model="editingTitleValue"
          class="panel-title-input"
          @blur="handleSaveTitle"
          @keydown.enter="handleSaveTitle"
          @keydown.escape="cancelEditTitle"
        />
        <span
          v-else
          class="panel-title editable"
          @click="startEditTitle"
          :title="$t('ui.clickToRename')"
        >{{ feature.title || $t('ui.toolbox') }}</span>
      </div>
      <span class="feature-status-badge" :class="getFeatureStatusClass(feature.status)">
        {{ getFeatureStatusText(feature.status) }}
      </span>

      <button
        v-if="feature.status === 'completed'"
        class="panel-export-btn"
        :class="{ loading: isDownloading }"
        :disabled="isDownloading"
        @click="handleDownloadWord"
        :title="$t('ui.downloadWordDocument')"
      >
        <svg v-if="!isDownloading" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
        <svg v-else class="loading-spinner" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M12 4V2A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8z"/>
        </svg>
      </button>

      <button class="panel-toggle-btn" @click="$emit('close')" :title="$t('ui.close')">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      </button>
    </div>
    <div class="feature-report-content" ref="featureReportRef" @click="handleContentClick">
      <div v-if="feature.blocks && feature.blocks.length > 0" class="report-body">
        <template v-for="(processed, idx) in processFeatureBlocks(feature.blocks)" :key="idx">
          <div
            v-if="processed.type === 'single' && processed.block"
            class="feature-block"
            :data-block-index="processed.originalIndex"
          >
            <component
              v-if="processed.block.block_type === 'heading'"
              :is="'h' + (processed.block.level || 2)"
              class="feature-heading"
            ><template v-for="(part, pi) in processed.block.content_parts" :key="pi"><span v-if="part.type === 'text'" class="feature-text" v-html="parseInlineMarkdown(part.content)"></span><sup
                  v-else-if="part.type === 'citation_ref'"
                  class="inline-citation"
                  :class="{ active: activeCitationNum === part.display_num }"
                  :data-segment-id="part.segment_id"
                  :data-display-num="part.display_num"
                  :title="part.summary"
                  @click="$emit('citationClick', part)"
                >{{ part.display_num }}</sup></template></component>

            <p v-else-if="processed.block.block_type === 'paragraph'" class="feature-paragraph">
              <template v-for="(part, pi) in processed.block.content_parts" :key="pi"><span v-if="part.type === 'text'" class="feature-text" v-html="parseInlineMarkdown(part.content)"></span><sup
                  v-else-if="part.type === 'citation_ref'"
                  class="inline-citation"
                  :class="{ active: activeCitationNum === part.display_num }"
                  :data-segment-id="part.segment_id"
                  :data-display-num="part.display_num"
                  :title="part.summary"
                  @click="$emit('citationClick', part)"
                >{{ part.display_num }}</sup></template>
            </p>

            <blockquote v-else-if="processed.block.block_type === 'quote'" class="feature-quote"><template v-for="(part, pi) in processed.block.content_parts" :key="pi"><span v-if="part.type === 'text'" class="feature-text" v-html="parseInlineMarkdown(part.content)"></span><sup
                  v-else-if="part.type === 'citation_ref'"
                  class="inline-citation"
                  :class="{ active: activeCitationNum === part.display_num }"
                  :data-segment-id="part.segment_id"
                  :data-display-num="part.display_num"
                  :title="part.summary"
                  @click="$emit('citationClick', part)"
                >{{ part.display_num }}</sup></template></blockquote>

            <figure v-else-if="processed.block.block_type === 'image'" class="feature-image">
              <div class="image-wrapper">
                <img v-if="processed.block.asset" :src="getAssetUrl(processed.block.asset.url)" :alt="processed.block.caption || ''" />
                <button v-if="processed.block.asset" class="image-download-btn" @click="downloadImage(getAssetUrl(processed.block.asset.url))" :title="$t('ui.downloadImage')">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                    <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                  </svg>
                </button>
              </div>
              <figcaption v-if="processed.block.caption">{{ processed.block.caption }}</figcaption>
            </figure>

            <div v-else-if="processed.block.block_type === 'image_group'" class="feature-image-group">
              <figure v-for="(asset, ai) in processed.block.assets" :key="ai" class="feature-image">
                <div class="image-wrapper">
                  <img :src="getAssetUrl(asset.url)" :alt="processed.block.caption || ''" />
                  <button class="image-download-btn" @click="downloadImage(getAssetUrl(asset.url))" :title="$t('ui.downloadImage')">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                      <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                    </svg>
                  </button>
                </div>
              </figure>
              <figcaption v-if="processed.block.caption">{{ processed.block.caption }}</figcaption>
            </div>

            <figure v-else-if="processed.block.block_type === 'video'" class="feature-video">
              <video v-if="processed.block.asset" :src="getAssetUrl(processed.block.asset.url)" controls :poster="processed.block.asset.thumbnail_url ? getAssetUrl(processed.block.asset.thumbnail_url) : undefined"></video>
              <figcaption v-if="processed.block.caption">{{ processed.block.caption }}</figcaption>
            </figure>
          </div>

          <div
            v-else-if="processed.type === 'list_group' && processed.blocks"
            class="feature-block"
          >
            <ul class="feature-list">
              <li v-for="(listBlock, li) in processed.blocks" :key="li"><template v-for="(part, pi) in listBlock.content_parts" :key="pi"><span v-if="part.type === 'text'" class="feature-text" v-html="parseInlineMarkdown(part.content)"></span><sup
                    v-else-if="part.type === 'citation_ref'"
                    class="inline-citation"
                    :class="{ active: activeCitationNum === part.display_num }"
                    :data-segment-id="part.segment_id"
                    :data-display-num="part.display_num"
                    :title="part.summary"
                    @click="$emit('citationClick', part)"
                  >{{ part.display_num }}</sup></template></li>
            </ul>
          </div>
        </template>
      </div>
      <div v-else-if="feature.status === 'failed'" class="report-error">
        <p>{{ $t('ui.generationFailedWithReason', { reason: feature.error_message || $t('ui.unknownError') }) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import type { Feature, FeatureBlock, FeatureCitationRefPart } from '../../types'
import { parseInlineMarkdown } from '../../utils'
import { getAssetUrl, exportFeatureToWord } from '../../services/api'
import { t } from '../../i18n'


const isEditingTitle = ref(false)
const editingTitleValue = ref('')
const titleInputRef = ref<HTMLInputElement | null>(null)


const isDownloading = ref(false)

async function handleDownloadWord() {
  if (isDownloading.value) return
  
  try {
    isDownloading.value = true
    const blob = await exportFeatureToWord(props.feature.id)
    
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    const fileName = props.feature.title ? `${props.feature.title}.docx` : `feature_export_${props.feature.id}.docx`
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出失败:', error)
    
  } finally {
    isDownloading.value = false
  }
}


const props = defineProps<{
  feature: Feature
  activeCitationNum: number | null
}>()


const emit = defineEmits<{
  (e: 'close'): void
  (e: 'citationClick', part: FeatureCitationRefPart): void
  (e: 'clearCitation'): void
  (e: 'rename', newTitle: string): void
}>()


function handleContentClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  
  if (!target.closest('.inline-citation')) {
    emit('clearCitation')
  }
}


interface ProcessedBlock {
  type: 'single' | 'list_group'
  block?: any
  blocks?: any[]
  originalIndex?: number
  originalIndices?: number[]
}

function processFeatureBlocks(blocks: FeatureBlock[]): ProcessedBlock[] {
  if (!blocks || blocks.length === 0) return []

  const result: ProcessedBlock[] = []
  let currentListGroup: { block: FeatureBlock; index: number }[] = []

  for (let i = 0; i < blocks.length; i++) {
    const block = blocks[i]!
    if (block.block_type === 'list') {
      currentListGroup.push({ block, index: i })
    } else {
      
      if (currentListGroup.length > 0) {
        result.push({
          type: 'list_group',
          blocks: currentListGroup.map(item => item.block),
          originalIndices: currentListGroup.map(item => item.index)
        })
        currentListGroup = []
      }
      result.push({ type: 'single', block, originalIndex: i })
    }
  }

  
  if (currentListGroup.length > 0) {
    result.push({
      type: 'list_group',
      blocks: currentListGroup.map(item => item.block),
      originalIndices: currentListGroup.map(item => item.index)
    })
  }

  return result
}


async function downloadImage(url: string) {
  try {
    const response = await fetch(url)
    const blob = await response.blob()
    const blobUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = 'local-notebook-image.png'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(blobUrl)
  } catch (error) {
  }
}


function startEditTitle() {
  editingTitleValue.value = props.feature.title || t('ui.toolbox')
  isEditingTitle.value = true
  nextTick(() => {
    titleInputRef.value?.focus()
  })
}

function handleSaveTitle() {
  if (!isEditingTitle.value) return
  
  const newTitle = editingTitleValue.value.trim()
  if (newTitle && newTitle !== props.feature.title) {
    emit('rename', newTitle)
  }
  isEditingTitle.value = false
}

function cancelEditTitle() {
  isEditingTitle.value = false
  editingTitleValue.value = ''
}


function getFeatureStatusText(status: string): string {
  const map: Record<string, string> = {
    pending: t('ui.waiting'),
    processing: t('ui.generating2'),
    completed: t('ui.completed'),
    failed: t('ui.failed')
  }
  return map[status] || status
}


function getFeatureStatusClass(status: string): string {
  const map: Record<string, string> = {
    pending: 'status-pending',
    processing: 'status-processing',
    completed: 'status-completed',
    failed: 'status-failed'
  }
  return map[status] || ''
}

</script>

<style scoped>
.feature-detail-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #fff;
  flex-shrink: 0;
  gap: 8px;
  border-radius: 16px 16px 0 0;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.panel-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.panel-title.editable {
  cursor: pointer;
  transition: color 0.2s;
}

.panel-title.editable:hover {
  color: #3b82f6;
}

.panel-title-input {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  border: 1px solid #3b82f6;
  border-radius: 4px;
  padding: 4px 8px;
  outline: none;
  background: white;
  width: 100%;
  min-width: 100px;
}


.panel-export-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;
}

.panel-export-btn:hover:not(:disabled) {
  background: #dcfce7;
  color: #16a34a;
}

.panel-export-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.panel-export-btn.loading {
  color: #16a34a;
}

.panel-export-btn .loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}


.panel-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;
  margin-left: auto;
}

.panel-toggle-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

.feature-report-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.report-body {
  max-width: 100%;
}


.feature-block {
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
  border-radius: 6px;
  padding: 2px 0;
  margin: -2px 0;
}

.feature-heading {
  color: #111827;
  margin: 0 0 16px 0;
  line-height: 1.4;
}

h1.feature-heading {
  font-size: 24px;
}

h2.feature-heading {
  font-size: 20px;
}

h3.feature-heading {
  font-size: 18px;
}

h4.feature-heading,
h5.feature-heading,
h6.feature-heading {
  font-size: 16px;
}

.feature-paragraph {
  color: #374151;
  font-size: 15px;
  line-height: 1.75;
  margin: 0 0 16px 0;
}

.feature-quote {
  margin: 0 0 16px 0;
  padding: 12px 16px;
  border-left: 4px solid #3b82f6;
  background: #f8fafc;
  color: #4b5563;
  font-style: italic;
}

.feature-list {
  margin: 0 0 16px 0;
  padding-left: 24px;
  color: #374151;
  font-size: 15px;
  line-height: 1.75;
}

.feature-list li {
  margin-bottom: 8px;
}

.feature-image {
  margin: 0 0 16px 0;
}

.feature-image .image-wrapper {
  position: relative;
  display: inline-block;
}

.feature-image img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}

.image-download-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 6px;
  cursor: pointer;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s;
}

.feature-image .image-wrapper:hover .image-download-btn {
  opacity: 1;
}

.image-download-btn:hover {
  background: rgba(0, 0, 0, 0.7);
}

.feature-image figcaption {
  margin-top: 8px;
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}

.feature-image-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 0 0 16px 0;
}

.feature-image-group .feature-image {
  margin: 0;
  flex: 1;
  min-width: 150px;
  max-width: calc(50% - 6px);
}

.feature-image-group > figcaption {
  width: 100%;
  margin-top: 8px;
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}

.feature-video {
  margin: 0 0 16px 0;
}

.feature-video video {
  max-width: 100%;
  border-radius: 8px;
}

.feature-video figcaption {
  margin-top: 8px;
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}

.inline-citation {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  font-size: 11px;
  font-weight: 500;
  color: #3b82f6;
  background: #eff6ff;
  border-radius: 9px;
  cursor: pointer;
  vertical-align: middle;
  margin-left: 3px;
  position: relative;
  top: -1px;
  transition: all 0.2s;
}

.inline-citation:hover {
  background: #dbeafe;
  color: #2563eb;
}

.inline-citation.active {
  background: #3b82f6;
  color: #fff;
}

.report-error {
  padding: 24px;
  text-align: center;
  color: #ef4444;
}

.report-error p {
  margin: 0;
}

.feature-text :deep(strong) {
  font-weight: 600;
}

.feature-text :deep(em) {
  font-style: italic;
}

.feature-text :deep(code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
}
</style>

<style scoped>
.feature-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 9999px;
  white-space: nowrap;
}

.feature-status-badge.status-pending {
  background: #f3f4f6;
  color: #6b7280;
}

.feature-status-badge.status-processing {
  background: #dbeafe;
  color: #2563eb;
  animation: breathing 1.6s ease-in-out infinite;
}

.feature-status-badge.status-processing::after {
  content: '...';
  display: inline-block;
  margin-left: 2px;
  animation: workflowDots 1.2s steps(4, end) infinite;
}

.feature-status-badge.status-completed {
  background: #dcfce7;
  color: #16a34a;
}

.feature-status-badge.status-failed {
  background: #fee2e2;
  color: #dc2626;
}

@keyframes breathing {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.25);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(37, 99, 235, 0);
  }
}

@keyframes workflowDots {
  0% { clip-path: inset(0 100% 0 0); }
  33% { clip-path: inset(0 66% 0 0); }
  66% { clip-path: inset(0 33% 0 0); }
  100% { clip-path: inset(0 0 0 0); }
}
</style>
