<template>
  <template v-for="block in blocks" :key="block.block_id">
    <div
      v-if="block.extra?.is_table"
      :data-block-id="block.block_id"
      class="preview-block table-block"
      :class="{ highlighted: highlightBlockIds.includes(block.block_id) }"
    >
      <div v-if="block.extra?.table_caption" class="table-caption">{{ block.extra.table_caption }}</div>
      <div class="table-content" v-html="block.extra?.table_html || renderLatexOnly(block.content)"></div>
      <div v-if="block.extra?.table_footnote" class="table-footnote">{{ block.extra.table_footnote }}</div>
    </div>

    <div
      v-else-if="block.extra?.is_image"
      :data-block-id="block.block_id"
      class="preview-block image-block"
      :class="{ highlighted: highlightBlockIds.includes(block.block_id) }"
    >
      <img
        v-if="getBlockImagePreviewUrl(block)"
        :src="getBlockImagePreviewUrl(block)"
        :alt="previewingFileName"
        class="parsed-block-image"
      />
      <span v-else v-html="renderLatexOnly(block.content)"></span>
    </div>

    <div
      v-else
      :data-block-id="block.block_id"
      class="preview-block"
      :class="{ [block.block_type]: true, highlighted: highlightBlockIds.includes(block.block_id) }"
    >
      <span
        v-if="highlightBlockIds.includes(block.block_id)"
        class="highlight-text"
        v-html="renderLatexOnly(block.content)"
      ></span>
      <span v-else v-html="renderLatexOnly(block.content)"></span>
    </div>
  </template>
</template>

<script setup lang="ts">
import { getEmbeddedImagePreviewUrl } from '@/services/api'
import type { FileContent } from '@/types'
import { renderLatexOnly } from '@/utils'

const props = defineProps<{
  blocks: FileContent['blocks']
  highlightBlockIds: string[]
  previewingFileId: string | null
  previewingFileName: string
}>()

function getBlockImagePreviewUrl(block: FileContent['blocks'][number]): string {
  if (!props.previewingFileId) return ''
  const imageIndex = block.extra?.image_index
  if (typeof imageIndex !== 'number') return ''
  return getEmbeddedImagePreviewUrl(props.previewingFileId, imageIndex)
}
</script>

<style scoped>
.preview-block {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #1a1a1a;
  font-size: 14px;
  transition: background 0.3s;
  padding: 2px 8px;
  border-radius: 4px;
}

.preview-block.heading {
  font-size: 18px;
  font-weight: 600;
  margin-top: 16px;
  margin-bottom: 8px;
}

.preview-block.quote {
  border-left: 3px solid var(--primary-color);
  padding-left: 12px;
  color: var(--text-secondary);
  font-style: italic;
}

.preview-block.table-block {
  margin: 16px 0;
  padding: 0;
  overflow-x: auto;
}

.preview-block.image-block {
  margin: 16px 0;
  padding: 0;
}

.parsed-block-image {
  display: block;
  max-width: 100%;
  max-height: 520px;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 6px;
}

.preview-block.image-block.highlighted {
  padding: 8px;
  background: rgba(216, 180, 254, 0.2);
}

.table-caption {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding: 0 8px;
}

.table-content {
  overflow-x: auto;
}

.table-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  font-size: 13px;
}

.table-content :deep(td),
.table-content :deep(th) {
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  text-align: left;
  vertical-align: top;
}

.table-content :deep(th) {
  background: var(--bg-secondary);
  font-weight: 600;
}

.table-content :deep(tr:nth-child(even)) {
  background-color: var(--bg-main);
}

.table-content :deep(tr:hover) {
  background-color: var(--bg-hover);
}

.table-footnote {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 6px;
  padding: 0 8px;
}

.preview-block.table-block.highlighted .table-content :deep(table) {
  background: rgba(216, 180, 254, 0.2);
}

.preview-block.highlighted {
  animation: highlightFadeIn 0.3s ease-out;
}

.highlight-text {
  background: rgba(216, 180, 254, 0.5);
  box-decoration-break: clone;
  -webkit-box-decoration-break: clone;
  padding: 0 4px;
  border-radius: 3px;
  font-weight: 700;
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
