<template>
  <div class="workflow-detail-panel">
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
          title="点击重命名"
        >{{ workflow.title || workflow.display_name }}</span>
      </div>
      <span class="workflow-status-badge" :class="getWorkflowStatusClass(workflow.status)">
        {{ getWorkflowStatusText(workflow.status) }}
      </span>


      <button
        v-if="workflow.status === 'completed' || workflow.status === 'partial'"
        class="panel-export-btn"
        :class="{ loading: isExporting }"
        :disabled="isExporting"
        @click="handleExportWord"
        title="导出为 Word 文档"
      >
        <svg v-if="!isExporting" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
        <svg v-else class="loading-spinner" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M12 4V2A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8z"/>
        </svg>
      </button>
      <button class="panel-toggle-btn" @click="$emit('close')" title="关闭">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      </button>
    </div>
    <div ref="contentRef" class="workflow-report-content" @click="handleContentClick">

      <div class="floating-toc" :class="{ expanded: tocExpanded }">
        <button class="toc-toggle" @click="tocExpanded = !tocExpanded" title="目录导航">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
          </svg>
          <span class="toc-title">目录</span>
        </button>
        <div v-if="tocExpanded" class="toc-list">
          <div
            v-for="(feature, fi) in features"
            :key="feature.id"
            class="toc-item"
            :class="{ active: activeTocIndex === fi }"
            @click="scrollToSection(fi)"
          >
            {{ feature.step_name }}
          </div>
        </div>
      </div>


      <template v-for="(feature, fi) in features" :key="feature.id">

        <div :id="'workflow-section-' + fi" class="workflow-feature-section">
          <div class="workflow-feature-header">
            <div class="feature-section-icon" :class="getFeatureIconColorClass(feature.feature_type)">

              <svg v-if="feature.feature_type === 'content_summary'" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
              </svg>

              <svg v-else-if="feature.feature_type === 'expert_recommendation'" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
              </svg>

              <svg v-else-if="feature.feature_type === 'golden_quotes'" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M6 17h3l2-4V7H5v6h3zm8 0h3l2-4V7h-6v6h3z"/>
              </svg>

              <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
              </svg>
            </div>
            <div class="feature-title-row">
              <span class="feature-section-title">{{ feature.step_name }}</span>
              <button
                class="step-regenerate-btn"
                :disabled="!canRegenerate(feature.status)"
                @click="handleRegenerateStep(feature.step_index)"
                title="重新生成"
              >
                <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                  <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
                </svg>
                <span>重新生成</span>
              </button>
            </div>
          </div>


          <div v-if="feature.blocks && feature.blocks.length > 0" class="report-body">
            <template v-for="(processed, idx) in processFeatureBlocks(feature.blocks)" :key="`${fi}-${idx}`">

              <template v-if="processed.type === 'single' && processed.block">

                <component
                  v-if="processed.block.block_type === 'heading'"
                  :is="'h' + (processed.block.level || 2)"
                  class="feature-heading"
                ><template v-for="(part, pi) in processed.block.content_parts" :key="pi"><span v-if="part.type === 'text'" class="feature-text" v-html="parseInlineMarkdown(part.content)"></span><span
                      v-else-if="part.type === 'citation_ref' && isWebCitation(part.citation_id, feature)"
                      class="inline-citation web-citation"
                      :class="{ active: isCitationActive(part.display_num, feature.id) }"
                      @click="handleWebCitationClick(part.citation_id, feature)"
                      @mouseenter="(e) => showWebCitationCard(e, part.citation_id, feature)"
                      @mouseleave="hideWebCitationCard"
                    >{{ part.display_num }}<img v-if="getWebCitationFavicon(part.citation_id, feature)" class="web-favicon" :src="getWebCitationFavicon(part.citation_id, feature)" width="12" height="12" /><svg v-else class="web-icon" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg></span><sup
                      v-else-if="part.type === 'citation_ref'"
                      class="inline-citation"
                      :class="{ active: isCitationActive(part.display_num, feature.id), disabled: !hasCitationSource(part, feature) }"
                      :title="hasCitationSource(part, feature) ? part.summary : undefined"
                      @click="handleCitationClick(part, feature)"
                    >{{ part.display_num }}</sup></template></component>


                <div
                  v-else-if="processed.block.block_type === 'paragraph' && processed.block.extra?.is_table && parseMarkdownTable(getTableContent(processed.block), feature)"
                  class="feature-table"
                >
                  <table>
                    <thead>
                      <tr>
                        <th v-for="(header, hi) in parseMarkdownTable(getTableContent(processed.block), feature)!.headers" :key="hi">
                          <template v-for="(part, pi) in header.parts" :key="pi">
                            <span v-if="part.type === 'text'" v-html="parseInlineMarkdown(part.content || '')"></span>

                            <span
                              v-else-if="part.type === 'citation_ref' && isWebCitation(part.citation_id!, feature)"
                              class="inline-citation web-citation"
                              :class="{ active: isCitationActive(part.display_num || 0, feature.id) }"
                              @click="handleWebCitationClick(part.citation_id!, feature)"
                              @mouseenter="(e) => showWebCitationCard(e, part.citation_id!, feature)"
                              @mouseleave="hideWebCitationCard"
                            >{{ part.display_num }}<img v-if="getWebCitationFavicon(part.citation_id!, feature)" class="web-favicon" :src="getWebCitationFavicon(part.citation_id!, feature)" width="12" height="12" /><svg v-else class="web-icon" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg></span>

                            <sup
                              v-else-if="part.type === 'citation_ref'"
                              class="inline-citation"
                              :class="{ active: isCitationActive(part.display_num || 0, feature.id), disabled: !hasCitationSource({ type: 'citation_ref', citation_id: part.citation_id, display_num: part.display_num }, feature) }"
                              :title="undefined"
                              @click="handleCitationClick({ type: 'citation_ref', citation_id: part.citation_id, display_num: part.display_num }, feature)"
                            >{{ part.display_num }}</sup>
                          </template>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, ri) in parseMarkdownTable(getTableContent(processed.block), feature)!.rows" :key="ri">
                        <td v-for="(cell, ci) in row" :key="ci">
                          <template v-for="(part, pi) in cell.parts" :key="pi">
                            <span v-if="part.type === 'text'" v-html="parseInlineMarkdown(part.content || '')"></span>

                            <span
                              v-else-if="part.type === 'citation_ref' && isWebCitation(part.citation_id!, feature)"
                              class="inline-citation web-citation"
                              :class="{ active: isCitationActive(part.display_num || 0, feature.id) }"
                              @click="handleWebCitationClick(part.citation_id!, feature)"
                              @mouseenter="(e) => showWebCitationCard(e, part.citation_id!, feature)"
                              @mouseleave="hideWebCitationCard"
                            >{{ part.display_num }}<img v-if="getWebCitationFavicon(part.citation_id!, feature)" class="web-favicon" :src="getWebCitationFavicon(part.citation_id!, feature)" width="12" height="12" /><svg v-else class="web-icon" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg></span>

                            <sup
                              v-else-if="part.type === 'citation_ref'"
                              class="inline-citation"
                              :class="{ active: isCitationActive(part.display_num || 0, feature.id), disabled: !hasCitationSource({ type: 'citation_ref', citation_id: part.citation_id, display_num: part.display_num }, feature) }"
                              :title="undefined"
                              @click="handleCitationClick({ type: 'citation_ref', citation_id: part.citation_id, display_num: part.display_num }, feature)"
                            >{{ part.display_num }}</sup>
                          </template>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>


                <p v-else-if="processed.block.block_type === 'paragraph'" class="feature-paragraph">

                  <template v-for="(part, pi) in processed.block.content_parts" :key="pi"><span v-if="part.type === 'text'" class="feature-text" v-html="parseInlineMarkdown(part.content)"></span><span
                      v-else-if="part.type === 'citation_ref' && isWebCitation(part.citation_id, feature)"
                      class="inline-citation web-citation"
                      :class="{ active: isCitationActive(part.display_num, feature.id) }"
                      @click="handleWebCitationClick(part.citation_id, feature)"
                      @mouseenter="(e) => showWebCitationCard(e, part.citation_id, feature)"
                      @mouseleave="hideWebCitationCard"
                    >{{ part.display_num }}<img v-if="getWebCitationFavicon(part.citation_id, feature)" class="web-favicon" :src="getWebCitationFavicon(part.citation_id, feature)" width="12" height="12" /><svg v-else class="web-icon" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg></span><sup
                      v-else-if="part.type === 'citation_ref'"
                      class="inline-citation"
                      :class="{ active: isCitationActive(part.display_num, feature.id), disabled: !hasCitationSource(part, feature) }"
                      :title="hasCitationSource(part, feature) ? part.summary : undefined"
                      @click="handleCitationClick(part, feature)"
                    >{{ part.display_num }}</sup></template>
                </p>


                <blockquote v-else-if="processed.block.block_type === 'quote'" class="feature-quote"><template v-for="(part, pi) in processed.block.content_parts" :key="pi"><span v-if="part.type === 'text'" class="feature-text" v-html="parseInlineMarkdown(part.content)"></span><span
                      v-else-if="part.type === 'citation_ref' && isWebCitation(part.citation_id, feature)"
                      class="inline-citation web-citation"
                      :class="{ active: isCitationActive(part.display_num, feature.id) }"
                      @click="handleWebCitationClick(part.citation_id, feature)"
                      @mouseenter="(e) => showWebCitationCard(e, part.citation_id, feature)"
                      @mouseleave="hideWebCitationCard"
                    >{{ part.display_num }}<img v-if="getWebCitationFavicon(part.citation_id, feature)" class="web-favicon" :src="getWebCitationFavicon(part.citation_id, feature)" width="12" height="12" /><svg v-else class="web-icon" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg></span><sup
                      v-else-if="part.type === 'citation_ref'"
                      class="inline-citation"
                      :class="{ active: isCitationActive(part.display_num, feature.id), disabled: !hasCitationSource(part, feature) }"
                      :title="hasCitationSource(part, feature) ? part.summary : undefined"
                      @click="handleCitationClick(part, feature)"
                    >{{ part.display_num }}</sup></template></blockquote>


                <figure v-else-if="processed.block.block_type === 'image'" class="feature-image">
                  <div class="image-wrapper">
                    <img v-if="processed.block.asset" :src="getAssetUrl(processed.block.asset.url)" :alt="processed.block.caption || ''" />
                    <button v-if="processed.block.asset" class="image-download-btn" @click="downloadImage(getAssetUrl(processed.block.asset.url))" title="下载图片">
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
                      <button class="image-download-btn" @click="downloadImage(getAssetUrl(asset.url))" title="下载图片">
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
              </template>


              <ul v-else-if="processed.type === 'list_group' && processed.blocks" class="feature-list">
                <li v-for="(listBlock, li) in processed.blocks" :key="li"><template v-for="(part, pi) in listBlock.content_parts" :key="pi"><span v-if="part.type === 'text'" class="feature-text" v-html="parseInlineMarkdown(part.content)"></span><span
                      v-else-if="part.type === 'citation_ref' && isWebCitation(part.citation_id, feature)"
                      class="inline-citation web-citation"
                      :class="{ active: isCitationActive(part.display_num, feature.id) }"
                      @click="handleWebCitationClick(part.citation_id, feature)"
                      @mouseenter="(e) => showWebCitationCard(e, part.citation_id, feature)"
                      @mouseleave="hideWebCitationCard"
                    >{{ part.display_num }}<img v-if="getWebCitationFavicon(part.citation_id, feature)" class="web-favicon" :src="getWebCitationFavicon(part.citation_id, feature)" width="12" height="12" /><svg v-else class="web-icon" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg></span><sup
                      v-else-if="part.type === 'citation_ref'"
                      class="inline-citation"
                      :class="{ active: isCitationActive(part.display_num, feature.id), disabled: !hasCitationSource(part, feature) }"
                      :title="hasCitationSource(part, feature) ? part.summary : undefined"
                      @click="handleCitationClick(part, feature)"
                    >{{ part.display_num }}</sup></template></li>
              </ul>
            </template>
          </div>
          <div v-else class="report-body empty-blocks">
            <div v-if="feature.status === 'pending' || feature.status === 'processing'" class="empty-placeholder">
              <span class="loading-text">正在重新生成，请稍候</span>
              <span class="loading-dots" aria-hidden="true">
                <span class="dot dot-1">.</span>
                <span class="dot dot-2">.</span>
                <span class="dot dot-3">.</span>
              </span>
            </div>
            <div v-else-if="feature.status === 'failed'" class="workflow-feature-error">
              {{ feature.error_message || '生成失败，请点击“重新生成”按钮重试' }}
            </div>
            <div v-else class="empty-placeholder">
              暂无内容
            </div>
          </div>
        </div>
      </template>


      <div v-if="features.length === 0 && workflow.steps.filter(s => s.status === 'failed').length === 0" class="workflow-empty">
        <p>暂无生成结果</p>
      </div>
    </div>


    <WebCitationTooltip
      :visible="webCitationTooltip.visible"
      :x="webCitationTooltip.x"
      :y="webCitationTooltip.y"
      :title="webCitationTooltip.title"
      :url="webCitationTooltip.url"
      :snippet="webCitationTooltip.snippet"
      :source="webCitationTooltip.source"
      :date="webCitationTooltip.date"
      :favicon="webCitationTooltip.favicon"
      @close="webCitationTooltip.visible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import type { WorkflowDetail, WorkflowStatus, WorkflowContentFeature } from '../../services/api'
import type { FeatureBlock, CitationMetadata } from '../../types'
import { parseInlineMarkdown } from '../../utils'
import { getAssetUrl, exportWorkflowToWord } from '../../services/api'

import WebCitationTooltip from '../common/WebCitationTooltip.vue'


const props = defineProps<{
  workflow: WorkflowDetail
  features: WorkflowContentFeature[]
  activeCitationNum?: number | null
  activeFeatureId?: string | null

}>()


const emit = defineEmits<{
  (e: 'close'): void
  (e: 'citationClick', part: any, feature: WorkflowContentFeature): void
  (e: 'clearCitation'): void

  (e: 'showToast', message: string, type: 'success' | 'error' | 'info' | 'warning'): void

  (e: 'regenerateStep', stepIndex: number): void
  (e: 'rename', workflow: WorkflowDetail): void
  (e: 'update-title', id: string, title: string): void
}>()


const isEditingTitle = ref(false)
const titleInputRef = ref<HTMLInputElement | null>(null)
const editingTitleValue = ref('')

function startEditTitle() {
  editingTitleValue.value = props.workflow.title || props.workflow.display_name
  isEditingTitle.value = true
  nextTick(() => {
    titleInputRef.value?.focus()
  })
}

function cancelEditTitle() {
  isEditingTitle.value = false
  editingTitleValue.value = ''
}

function handleSaveTitle() {
  const newTitle = editingTitleValue.value.trim()
  if (!newTitle || newTitle === props.workflow.title) {
    cancelEditTitle()
    return
  }
  emit('update-title', props.workflow.id, newTitle)
  isEditingTitle.value = false
}


const isExporting = ref(false)

function canRegenerate(status: string) {
  return status === 'completed' || status === 'failed'
}

function handleRegenerateStep(stepIndex: number) {
  emit('regenerateStep', stepIndex)
}


function isCitationActive(displayNum: number, featureId: string): boolean {
  return props.activeCitationNum === displayNum && props.activeFeatureId === featureId
}


interface CitationPart {
  type: 'citation_ref'
  citation_id?: string
  display_num?: number
  segment_id?: string
  summary?: string
}


function hasCitationSource(part: CitationPart, feature: WorkflowContentFeature): boolean {

  if (part.segment_id) {
    return true
  }


  if (part.citation_id && feature.citations?.[part.citation_id]?.segment_id) {
    return true
  }
  return false
}


function handleCitationClick(part: CitationPart, feature: WorkflowContentFeature) {
  if (!hasCitationSource(part, feature)) {

    return
  }


  const fullPart = {
    citation_id: part.citation_id,
    display_num: part.display_num,
    segment_id: part.segment_id || feature.citations?.[part.citation_id!]?.segment_id,
    summary: part.summary
  }
  emit('citationClick', fullPart, feature)
}


const tocExpanded = ref(false)
const activeTocIndex = ref(0)
const contentRef = ref<HTMLElement | null>(null)


const webCitationTooltip = reactive({
  visible: false,
  x: 0,
  y: 0,
  title: '',
  url: '',
  snippet: '',
  source: '',
  date: '',
  favicon: ''
})


function scrollToSection(index: number) {
  const section = document.getElementById(`workflow-section-${index}`)
  if (section) {
    section.scrollIntoView({ behavior: 'smooth', block: 'start' })
    activeTocIndex.value = index
  }
}


function handleScroll() {
  if (!contentRef.value) return
  const sections = contentRef.value.querySelectorAll('[id^="workflow-section-"]')
  const scrollTop = contentRef.value.scrollTop

  for (let i = sections.length - 1; i >= 0; i--) {
    const section = sections[i] as HTMLElement
    if (section.offsetTop <= scrollTop + 50) {
      activeTocIndex.value = i
      break
    }
  }
}


onMounted(() => {
  if (contentRef.value) {
    contentRef.value.addEventListener('scroll', handleScroll)
  }
})


onUnmounted(() => {
  if (contentRef.value) {
    contentRef.value.removeEventListener('scroll', handleScroll)
  }
})


async function handleExportWord() {
  if (isExporting.value) return

  isExporting.value = true
  try {
    const { blob, filename } = await exportWorkflowToWord(props.workflow.id, {
      include_citations: true,
      citation_style: 'endnote'
    })


    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    emit('showToast', '导出成功', 'success')
  } catch (error: any) {
    console.error('导出失败:', error)
    const message = error.response?.status === 429
      ? '操作过于频繁，请稍后再试'
      : error.response?.status === 400
        ? '当前状态不支持导出'
        : '导出失败，请稍后重试'
    emit('showToast', message, 'error')
  } finally {
    isExporting.value = false
  }
}


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
}

function processFeatureBlocks(blocks: FeatureBlock[]): ProcessedBlock[] {
  if (!blocks || blocks.length === 0) return []

  const result: ProcessedBlock[] = []
  let currentListGroup: FeatureBlock[] = []

  for (let i = 0; i < blocks.length; i++) {
    const block = blocks[i]!
    if (block.block_type === 'list') {
      currentListGroup.push(block)
    } else {
      if (currentListGroup.length > 0) {
        result.push({ type: 'list_group', blocks: currentListGroup })
        currentListGroup = []
      }
      result.push({ type: 'single', block, originalIndex: i })
    }
  }

  if (currentListGroup.length > 0) {
    result.push({ type: 'list_group', blocks: currentListGroup })
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
    console.error('下载图片失败:', error)
  }
}


function getWorkflowStatusText(status: WorkflowStatus): string {
  const map: Record<WorkflowStatus, string> = {
    pending: '等待中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败',
    partial: '部分完成'
  }
  return map[status] || status
}


function getWorkflowStatusClass(status: WorkflowStatus): string {
  const map: Record<WorkflowStatus, string> = {
    pending: 'status-pending',
    processing: 'status-processing',
    completed: 'status-completed',
    failed: 'status-failed',
    partial: 'status-partial'
  }
  return map[status] || ''
}


function getFeatureIconColorClass(featureType: string): string {
  const colorMap: Record<string, string> = {
    content_summary: 'icon-blue',
    expert_recommendation: 'icon-orange',
    golden_quotes: 'icon-cream',
    research_evaluation: 'icon-green',
    mind_map: 'icon-purple',
    text_to_image: 'icon-brown',
    reference_to_image: 'icon-teal',
    text_to_video: 'icon-indigo',
    image_to_video: 'icon-rose',
    start_end_to_video: 'icon-amber',
    reference_to_video: 'icon-emerald',

    communication_highlights: 'icon-pink',
    communication_assets: 'icon-cyan',
    general_communication: 'icon-lime',
    social_copy: 'icon-red'
  }
  return colorMap[featureType] || 'icon-default'
}


function isWebCitation(citationId: string, feature: WorkflowContentFeature): boolean {
  const citation = feature.citations?.[citationId] as any
  return citation?.type === 'web'
}


function getWebCitationMeta(citationId: string, feature: WorkflowContentFeature): CitationMetadata | null {
  const citation = feature.citations?.[citationId] as any
  if (citation?.type === 'web') {
    return citation
  }
  return null
}


function getWebCitationFavicon(citationId: string, feature: WorkflowContentFeature): string {
  const meta = getWebCitationMeta(citationId, feature)
  return meta?.favicon || ''
}


function showWebCitationCard(event: MouseEvent, citationId: string, feature: WorkflowContentFeature) {
  const meta = getWebCitationMeta(citationId, feature)
  if (!meta) return

  const target = event.target as HTMLElement
  const rect = target.getBoundingClientRect()
  webCitationTooltip.x = rect.left + rect.width / 2
  webCitationTooltip.y = rect.top
  webCitationTooltip.title = meta.title || ''
  webCitationTooltip.url = meta.url || ''
  webCitationTooltip.snippet = meta.snippet || ''
  webCitationTooltip.source = meta.source || ''
  webCitationTooltip.date = meta.published_date || ''
  webCitationTooltip.favicon = meta.favicon || ''
  webCitationTooltip.visible = true
}


function hideWebCitationCard() {

  setTimeout(() => {
    webCitationTooltip.visible = false
  }, 100)
}


function handleWebCitationClick(citationId: string, feature: WorkflowContentFeature) {
  const meta = getWebCitationMeta(citationId, feature)
  if (meta?.url) {
    window.open(meta.url, '_blank', 'noopener,noreferrer')
  }
}


interface TableCellPart {
  type: 'text' | 'citation_ref'
  content?: string
  citation_id?: string
  display_num?: number
}


interface ParsedTable {
  headers: Array<{ parts: TableCellPart[] }>
  rows: Array<Array<{ parts: TableCellPart[] }>>
}


function getTableContent(block: any): string {

  if (block.content && typeof block.content === 'string') {
    return block.content
  }

  if (block.content_parts && Array.isArray(block.content_parts)) {
    return block.content_parts
      .map((p: any) => {
        if (p.type === 'text') return p.content || ''
        if (p.type === 'citation_ref') return `[citation_${p.citation_id}]`
        return ''
      })
      .join('')
  }
  return ''
}


function parseTableCellContent(cellText: string, feature: WorkflowContentFeature): TableCellPart[] {
  const parts: TableCellPart[] = []

  const regex = /\[citation_(\d+_\d+)\]/g
  let lastIndex = 0
  let match

  while ((match = regex.exec(cellText)) !== null) {

    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: cellText.slice(lastIndex, match.index)
      })
    }


    const matchId = match[1] as string
    const citationId = `citation_${matchId}`
    const citation = feature.citations?.[citationId]
    parts.push({
      type: 'citation_ref',
      citation_id: citationId,
      display_num: citation?.display_num || 0
    })

    lastIndex = regex.lastIndex
  }


  if (lastIndex < cellText.length) {
    parts.push({
      type: 'text',
      content: cellText.slice(lastIndex)
    })
  }


  if (parts.length === 0) {
    parts.push({ type: 'text', content: '' })
  }

  return parts
}


function parseMarkdownTable(content: string, feature: WorkflowContentFeature): ParsedTable | null {
  if (!content) return null

  const lines = content.trim().split('\n').filter(line => line.trim())
  if (lines.length < 2) return null


  const headerLine = lines[0]
  if (!headerLine?.startsWith('|') || !headerLine?.endsWith('|')) return null

  const headerCells = headerLine
    .slice(1, -1)
    .split('|')
    .map(cell => cell.trim())


  const separatorLine = lines[1]
  if (!separatorLine?.includes('---')) return null


  const dataLines = lines.slice(2)
  const rows: Array<Array<{ parts: TableCellPart[] }>> = []

  for (const line of dataLines) {
    if (!line.startsWith('|') || !line.endsWith('|')) continue

    const cells = line
      .slice(1, -1)
      .split('|')
      .map(cell => ({
        parts: parseTableCellContent(cell.trim(), feature)
      }))

    rows.push(cells)
  }

  return {
    headers: headerCells.map(cell => ({
      parts: parseTableCellContent(cell, feature)
    })),
    rows
  }
}
</script>

<style scoped>
.workflow-detail-panel {
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

.workflow-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 9999px;
  white-space: nowrap;
}

.workflow-status-badge.status-pending {
  background: #f3f4f6;
  color: #6b7280;
}

.workflow-status-badge.status-processing {
  background: #dbeafe;
  color: #2563eb;
  animation: breathing 1.6s ease-in-out infinite;
}

.workflow-status-badge.status-processing::after {
  content: '...';
  display: inline-block;
  margin-left: 2px;
  animation: workflowDots 1.2s steps(4, end) infinite;
}

.workflow-status-badge.status-completed {
  background: #dcfce7;
  color: #16a34a;
}

.workflow-status-badge.status-failed {
  background: #fee2e2;
  color: #dc2626;
}

.workflow-status-badge.status-partial {
  background: #fef3c7;
  color: #d97706;
}

.loading-dots {
  display: inline-flex;
  align-items: center;
  margin-left: 4px;
}

.loading-dots .dot {
  opacity: 0.25;
  animation: dotPulse 1.2s infinite ease-in-out;
}

.loading-dots .dot-2 {
  animation-delay: 0.2s;
}

.loading-dots .dot-3 {
  animation-delay: 0.4s;
}

@keyframes dotPulse {
  0%, 100% {
    opacity: 0.2;
  }
  50% {
    opacity: 1;
  }
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

.workflow-report-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  position: relative;
}


.floating-toc {
  position: sticky;
  top: 0;
  float: right;
  z-index: 10;
  margin-left: 12px;
  margin-bottom: 12px;
}

.toc-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  color: #6b7280;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.2s;
}

.toc-toggle:hover {
  background: #f9fafb;
  color: #374151;
  border-color: #d1d5db;
}

.floating-toc.expanded .toc-toggle {
  border-radius: 8px 8px 0 0;
  border-bottom: none;
}

.toc-title {
  font-weight: 500;
}

.toc-list {
  position: absolute;
  top: 100%;
  right: 0;
  min-width: 140px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-top: none;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-height: 300px;
  overflow-y: auto;
}

.toc-item {
  padding: 8px 12px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s;
  border-left: 2px solid transparent;
}

.toc-item:hover {
  background: #f9fafb;
  color: #374151;
}

.toc-item.active {
  background: #eff6ff;
  color: #3b82f6;
  border-left-color: #3b82f6;
  font-weight: 500;
}

.toc-item:last-child {
  border-radius: 0 0 8px 8px;
}

.workflow-feature-section {
  margin-bottom: 32px;
}

.workflow-feature-section.failed {
  opacity: 0.8;
}

.workflow-feature-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.feature-title-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.step-regenerate-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 24px;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  background: transparent;
  border: 1px solid #e5e7eb;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.step-regenerate-btn svg {
  transition: transform 0.4s ease;
  color: #9ca3af;
}

.step-regenerate-btn:hover:not(:disabled) {
  color: #2563eb;
  background: #eff6ff;
  border-color: #bfdbfe;
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.1);
  transform: translateY(-0.5px);
}

.step-regenerate-btn:hover:not(:disabled) svg {
  color: #2563eb;
  transform: rotate(180deg);
}

.step-regenerate-btn:active:not(:disabled) {
  transform: translateY(0);
  background: #dbeafe;
}

.step-regenerate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f9fafb;
}

.feature-section-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
}

.feature-section-icon.icon-blue {
  background: #dbeafe;
  color: #2563eb;
}

.feature-section-icon.icon-orange {
  background: #ffedd5;
  color: #ea580c;
}

.feature-section-icon.icon-cream {
  background: #fef3c7;
  color: #d97706;
}

.feature-section-icon.icon-green {
  background: #dcfce7;
  color: #16a34a;
}

.feature-section-icon.icon-purple {
  background: #f3e8ff;
  color: #9333ea;
}

.feature-section-icon.icon-brown {
  background: #fde68a;
  color: #92400e;
}

.feature-section-icon.icon-teal {
  background: #ccfbf1;
  color: #0d9488;
}

.feature-section-icon.icon-indigo {
  background: #e0e7ff;
  color: #4f46e5;
}

.feature-section-icon.icon-rose {
  background: #fce7f3;
  color: #db2777;
}

.feature-section-icon.icon-amber {
  background: #fef3c7;
  color: #b45309;
}

.feature-section-icon.icon-emerald {
  background: #d1fae5;
  color: #059669;
}

.feature-section-icon.icon-red {
  background: #fee2e2;
  color: #dc2626;
}

.feature-section-icon.icon-pink {
  background: #fce7f3;
  color: #ec4899;
}

.feature-section-icon.icon-cyan {
  background: #cffafe;
  color: #06b6d4;
}

.feature-section-icon.icon-lime {
  background: #ecfccb;
  color: #84cc16;
}

.feature-section-icon.icon-default {
  background: #f3f4f6;
  color: #6b7280;
}

.feature-section-title {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.report-body {
  max-width: 100%;
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


.inline-citation.disabled {
  color: #9ca3af;
  background: #f3f4f6;
  cursor: not-allowed;
  position: relative;
}

.inline-citation.disabled:hover {
  color: #9ca3af;
  background: #f3f4f6;
}


.inline-citation.disabled::after {
  content: '抱歉，暂时无法定位该引用来源';
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 12px;
  background: #1f2937;
  color: #fff;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  white-space: nowrap;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 1000;
  pointer-events: none;
}


.inline-citation.disabled::before {
  content: '';
  position: absolute;
  bottom: calc(100% + 2px);
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: #1f2937;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 1000;
  pointer-events: none;
}

.inline-citation.disabled:hover::after,
.inline-citation.disabled:hover::before {
  opacity: 1;
  visibility: visible;
}


.inline-citation.web-citation {
  display: inline-flex;
  align-items: center;
  width: auto;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  gap: 2px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border: 1px solid #64b5f6;
  font-size: 11px;
  font-weight: 500;
  color: #1976d2;
  cursor: pointer;
  vertical-align: middle;
  margin-left: 3px;
  position: relative;
  top: -1px;
  transition: all 0.2s;
}

.inline-citation.web-citation:hover {
  background: linear-gradient(135deg, #bbdefb 0%, #90caf9 100%);
  border-color: #42a5f5;
}

.inline-citation.web-citation.active {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  border-color: #1565c0;
  color: #fff;
}

.inline-citation.web-citation .web-icon {
  flex-shrink: 0;
  margin-left: 1px;
}

.inline-citation.web-citation .web-favicon {
  flex-shrink: 0;
  margin-left: 2px;
  border-radius: 2px;
  vertical-align: middle;
}

.workflow-feature-error {
  padding: 12px 16px;
  background: #fef2f2;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
}

.workflow-empty {
  text-align: center;
  padding: 48px 24px;
  color: #9ca3af;
}

.workflow-empty p {
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


.feature-table {
  margin: 0 0 16px 0;
  overflow-x: auto;
}


.feature-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.feature-table th,
.feature-table td {
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  text-align: left;
}

.feature-table th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.feature-table tbody tr:nth-child(even) {
  background: #f9fafb;
}

.feature-table tbody tr:hover {
  background: #f3f4f6;
}


.feature-table .inline-citation {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  font-size: 10px;
  font-weight: 500;
  color: #3b82f6;
  background: #eff6ff;
  border-radius: 8px;
  cursor: pointer;
  vertical-align: middle;
}

.feature-table .inline-citation:hover {
  background: #dbeafe;
  color: #2563eb;
}


.feature-table .inline-citation.web-citation {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border: 1px solid #64b5f6;
  color: #1976d2;
}

.feature-table .inline-citation.web-citation:hover {
  background: linear-gradient(135deg, #bbdefb 0%, #90caf9 100%);
}


.feature-table :deep(strong) {
  font-weight: 600;
}

.feature-table :deep(em) {
  font-style: italic;
}


.feature-text :deep(.hashtag),
.feature-paragraph :deep(.hashtag),
.feature-list :deep(.hashtag) {
  display: inline;
  color: #f43f5e;
  font-weight: 500;
  cursor: default;
}

.panel-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-rename-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  opacity: 0;
}


.panel-title.editable {
  cursor: pointer;
  transition: color 0.2s;
}

.panel-title.editable:hover {
  color: var(--primary-color);
}

.panel-title-input {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  border: 1px solid var(--primary-color);
  border-radius: 4px;
  padding: 4px 8px;
  outline: none;
  background: white;
  width: 100%;
  min-width: 200px;
}
</style>
