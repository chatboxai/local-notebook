<template>
  <Teleport to="body">
    <div v-if="visible" class="image-gen-overlay" @click.self="handleClose">
      <div class="image-gen-modal">
        <div class="image-gen-header">
          <h3>{{ mode === 'text_to_image' ? '文生图' : '图生图' }}</h3>
          <button class="image-gen-close" @click="handleClose">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>

        <div class="image-gen-body">
          
          <div v-if="mode === 'reference_to_image'" class="form-section">
            <label class="form-label">
              选择参考图片
              <span class="label-hint">（1-3张）</span>
            </label>
            <div v-if="imageFiles.length === 0" class="no-images">
              <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
              </svg>
              <p>暂无可用的图片文件</p>
              <p class="hint">请先上传 jpg、png 或 webp 格式的图片</p>
            </div>
            <div v-else class="image-selector">
              <div
                v-for="file in imageFiles"
                :key="file.id"
                class="image-item"
                :class="{ selected: selectedFileIds.includes(file.id) }"
                @click="toggleImageSelection(file.id)"
              >
                <img :src="getImagePreviewUrl(file.id)" :alt="file.file_name" />
                <span class="file-name">{{ file.file_name }}</span>
                <span v-if="selectedFileIds.includes(file.id)" class="check-mark">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                </span>
              </div>
            </div>
            <p class="selected-count">已选择 {{ selectedFileIds.length }}/3 张</p>
          </div>

          
          <div class="form-section">
            <label class="form-label">
              {{ mode === 'text_to_image' ? '图片描述' : '修改要求' }}
            </label>
            <textarea
              v-model="prompt"
              class="form-textarea"
              :placeholder="mode === 'text_to_image'
                ? '描述您想要生成的图片，例如：\n• 一只可爱的橘猫在阳光下打盹\n• 未来城市的夜景，霓虹灯闪烁'
                : '描述您想要的修改，例如：\n• 将图片转换为水彩画风格\n• 保持构图，改为黑白色调'"
              rows="4"
              maxlength="500"
            ></textarea>
            <p class="char-count">{{ prompt.length }}/500</p>
          </div>

          
          <div class="form-section">
            <label class="form-label">输出比例</label>
            <div class="aspect-ratio-selector">
              <button
                v-for="ratio in ASPECT_RATIOS"
                :key="ratio.value"
                class="ratio-btn"
                :class="{ active: aspectRatio === ratio.value }"
                @click="aspectRatio = ratio.value"
              >
                <span class="ratio-icon">{{ ratio.icon }}</span>
                <span class="ratio-label">{{ ratio.value }}</span>
              </button>
            </div>
          </div>

          
          <div class="form-hint">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
            </svg>
            <span>图片生成通常需要 30-90 秒，请耐心等待</span>
          </div>
        </div>

        <div class="image-gen-footer">
          <button class="btn-cancel" @click="handleClose">取消</button>
          <button
            class="btn-confirm"
            :disabled="!canSubmit"
            @click="handleConfirm"
          >
            开始生成
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getImagePreviewUrl } from '../../services/api'

export interface ImageFile {
  id: string
  file_name: string
  file_type: string
  status: string
}

const props = defineProps<{
  visible: boolean
  mode: 'text_to_image' | 'reference_to_image'
  files: ImageFile[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', config: { prompt: string; fileIds: string[]; aspectRatio: string }): void
}>()

const ASPECT_RATIOS = [
  { value: '16:9', icon: '▭' },
  { value: '9:16', icon: '▯' },
  { value: '1:1', icon: '□' },
  { value: '4:3', icon: '▭' },
  { value: '3:4', icon: '▯' },
]

const IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'webp']

const prompt = ref('')
const aspectRatio = ref('16:9')
const selectedFileIds = ref<string[]>([])


const imageFiles = computed(() =>
  props.files.filter(f =>
    f.status === 'ready' &&
    IMAGE_TYPES.includes(f.file_type?.toLowerCase() || '')
  )
)


const canSubmit = computed(() => {
  if (!prompt.value.trim()) return false
  if (props.mode === 'reference_to_image' && selectedFileIds.value.length === 0) return false
  return true
})


function toggleImageSelection(fileId: string) {
  const index = selectedFileIds.value.indexOf(fileId)
  if (index === -1) {
    if (selectedFileIds.value.length < 3) {
      selectedFileIds.value.push(fileId)
    }
  } else {
    selectedFileIds.value.splice(index, 1)
  }
}

function handleClose() {
  emit('close')
}

function handleConfirm() {
  emit('confirm', {
    prompt: prompt.value.trim(),
    fileIds: props.mode === 'text_to_image' ? [] : selectedFileIds.value,
    aspectRatio: aspectRatio.value
  })
}


watch(() => props.visible, (newVal) => {
  if (!newVal) {
    prompt.value = ''
    aspectRatio.value = '16:9'
    selectedFileIds.value = []
  }
})
</script>

<style scoped>
.image-gen-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.image-gen-modal {
  width: 520px;
  max-width: 90vw;
  max-height: 85vh;
  background: var(--bg-white);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  animation: slideUp 0.25s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.image-gen-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-light);
}

.image-gen-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.image-gen-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
}

.image-gen-close:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.image-gen-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.form-section {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.label-hint {
  font-weight: 400;
  color: var(--text-tertiary);
  font-size: 12px;
}


.no-images {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 20px;
  background: var(--bg-main);
  border-radius: 10px;
  color: var(--text-tertiary);
}

.no-images svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.no-images p {
  margin: 0;
  font-size: 14px;
}

.no-images .hint {
  font-size: 12px;
  margin-top: 6px;
}

.image-selector {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  max-height: 200px;
  overflow-y: auto;
  padding: 4px;
}

.image-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color 0.15s, transform 0.15s;
}

.image-item:hover {
  transform: scale(1.02);
}

.image-item.selected {
  border-color: var(--primary-color);
}

.image-item img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  display: block;
}

.image-item .file-name {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 4px 6px;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  color: white;
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-item .check-mark {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  background: var(--primary-color);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.selected-count {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
}


.form-textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
  background: var(--bg-main);
  resize: vertical;
  min-height: 100px;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.form-textarea:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.form-textarea::placeholder {
  color: var(--text-tertiary);
}

.char-count {
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-tertiary);
  text-align: right;
}


.aspect-ratio-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ratio-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 16px;
  background: var(--bg-main);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.ratio-btn:hover {
  background: var(--bg-hover);
}

.ratio-btn.active {
  background: var(--primary-light);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.ratio-icon {
  font-size: 18px;
  line-height: 1;
}

.ratio-label {
  font-size: 11px;
  font-weight: 500;
}


.form-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  background: var(--bg-main);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.form-hint svg {
  flex-shrink: 0;
}


.image-gen-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-light);
}

.btn-cancel,
.btn-confirm {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-cancel {
  background: var(--bg-main);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-cancel:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-confirm {
  background: var(--primary-color);
  color: white;
  border: none;
}

.btn-confirm:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
