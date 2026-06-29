import { computed, reactive, ref, type ComputedRef, type Ref } from 'vue'
import type { ImageFile } from '@/components/common/ImageGenerationModal.vue'
import type { VideoFile, VideoGenerationConfig, VideoGenerationMode } from '@/components/common/VideoGenerationModal.vue'
import {
  deleteFeature,
  generateFeature,
  getFeature,
  getFeaturesStatusBatch,
  getProjectFeatures,
  updateFeature,
  type FeatureListItem,
} from '@/services/api'
import type { Feature, FileInfo } from '@/types'
import {
  IMAGE_GENERATION_FILE_TYPES,
  VIDEO_GENERATION_FILE_TYPES,
} from './fileHelpers'
import { IMAGE_GENERATION_TYPES, TOOL_TYPES, VIDEO_GENERATION_TYPES } from './toolTypes'
import { t } from '@/i18n'

type ToastType = 'success' | 'error' | 'info' | 'warning'
type ToolConfig = typeof TOOL_TYPES[0]

interface UseProjectFeaturesOptions {
  projectId: string
  files: Ref<FileInfo[]>
  readyFiles: ComputedRef<FileInfo[]>
  hasReadyFiles: ComputedRef<boolean>
  rightPanelWidth: Ref<number>
  rightPanelWidthBeforeReport: Ref<number | null>
  reportMinWidth: number
  showToast: (message: string, type?: ToastType, duration?: number) => void
  openRenameModal: (type: 'feature', id: string, name: string) => void
}

export function useProjectFeatures({
  projectId,
  files,
  readyFiles,
  hasReadyFiles,
  rightPanelWidth,
  rightPanelWidthBeforeReport,
  reportMinWidth,
  showToast,
  openRenameModal,
}: UseProjectFeaturesOptions) {
  const features = ref<FeatureListItem[]>([])
  const activeFeature = ref<Feature | null>(null)
  const showFeatureDetail = ref(false)
  const featureMenuId = ref<string | null>(null)
  const pollingFeatureIds = ref<Set<string>>(new Set())
  let featurePollingTimer: ReturnType<typeof setInterval> | null = null

  const toolConfigModal = reactive({
    visible: false,
    toolType: '',
    toolTitle: '',
    prompt: '',
    hidePrompt: false
  })

  const imageGenerationModal = reactive({
    visible: false,
    mode: 'text_to_image' as 'text_to_image' | 'reference_to_image'
  })

  const imageFilesForGeneration = computed<ImageFile[]>(() =>
    files.value
      .filter(f => f.status === 'ready' && IMAGE_GENERATION_FILE_TYPES.includes(f.file_type?.toLowerCase() || ''))
      .map(f => ({
        id: f.id,
        file_name: f.file_name,
        file_type: f.file_type,
        status: f.status
      }))
  )

  const videoGenerationModal = reactive({
    visible: false,
    mode: 'text_to_video' as VideoGenerationMode
  })

  const videoFilesForGeneration = computed<VideoFile[]>(() =>
    files.value
      .filter(f => f.status === 'ready' && VIDEO_GENERATION_FILE_TYPES.includes(f.file_type?.toLowerCase() || ''))
      .map(f => ({
        id: f.id,
        file_name: f.file_name,
        file_type: f.file_type,
        status: f.status
      }))
  )

  const processingToolTypes = computed(() =>
    features.value
      .filter(f => f.status === 'pending' || f.status === 'processing')
      .map(f => f.feature_type)
  )

  async function loadFeatures() {
  }

  function startFeaturePolling() {
    if (featurePollingTimer) return

    featurePollingTimer = setInterval(async () => {
      if (pollingFeatureIds.value.size === 0) {
        stopFeaturePolling()
        return
      }

      try {
        const featureIds = Array.from(pollingFeatureIds.value)
        const result = await getFeaturesStatusBatch(featureIds)

        let hasCompleted = false

        for (const [featureId, statusInfo] of Object.entries(result.features)) {
          const index = features.value.findIndex(f => f.id === featureId)
          if (index !== -1) {
            const existingFeature = features.value[index]!
            features.value[index] = {
              ...existingFeature,
              status: statusInfo.status as FeatureListItem['status'],
              error_message: statusInfo.error_message,
              display_name: statusInfo.display_name ?? existingFeature.display_name,
              prompt: statusInfo.prompt ?? existingFeature.prompt,
              title: statusInfo.title ?? existingFeature.title
            }
          }

          if (statusInfo.status === 'completed' || statusInfo.status === 'failed') {
            pollingFeatureIds.value.delete(featureId)
            hasCompleted = true
          }
        }

        if (hasCompleted) {
          const { features: featureList } = await getProjectFeatures(projectId)
          features.value = featureList
        }

        if (pollingFeatureIds.value.size === 0) {
          stopFeaturePolling()
        }
      } catch (error) {
        console.error('Failed to poll features:', error)
      }
    }, 3000)
  }

  function stopFeaturePolling() {
    if (featurePollingTimer) {
      clearInterval(featurePollingTimer)
      featurePollingTimer = null
    }
  }

  function openToolConfig(tool: ToolConfig) {
    if (!hasReadyFiles.value) return

    if (IMAGE_GENERATION_TYPES.includes(tool.type)) {
      imageGenerationModal.mode = tool.type as 'text_to_image' | 'reference_to_image'
      imageGenerationModal.visible = true
      return
    }

    if (VIDEO_GENERATION_TYPES.includes(tool.type)) {
      videoGenerationModal.mode = tool.type as VideoGenerationMode
      videoGenerationModal.visible = true
      return
    }

    toolConfigModal.toolType = tool.type
    toolConfigModal.toolTitle = t(tool.titleKey)
    toolConfigModal.prompt = ''
    toolConfigModal.hidePrompt = false
    toolConfigModal.visible = true
  }

  function closeToolConfig() {
    toolConfigModal.visible = false
    toolConfigModal.toolType = ''
    toolConfigModal.toolTitle = ''
    toolConfigModal.prompt = ''
  }

  async function handleToolConfigConfirm(toolType: string, prompt: string, fileIds: string[]) {
    closeToolConfig()
    await handleToolClick(toolType, prompt, fileIds)
  }

  function closeImageGenerationModal() {
    imageGenerationModal.visible = false
  }

  async function handleImageGenerationConfirm(config: { prompt: string; fileIds: string[]; aspectRatio: string }) {
    const toolType = imageGenerationModal.mode
    closeImageGenerationModal()

    try {
      const { feature_id } = await generateFeature(projectId, toolType, {
        prompt: config.prompt,
        file_ids: config.fileIds,
        aspect_ratio: config.aspectRatio
      })

      const toolConfig = TOOL_TYPES.find(t => t.type === toolType)
      features.value.unshift({
        id: feature_id,
        feature_type: toolType,
        display_name: toolConfig ? t(toolConfig.titleKey) : toolType,
        title: null,
        prompt: config.prompt || null,
        status: 'pending',
        error_message: null,
        created_at: new Date().toISOString(),
        started_at: null,
        finished_at: null
      })

      pollingFeatureIds.value.add(feature_id)
      startFeaturePolling()
    } catch (error) {
      console.error('Failed to generate image:', error)
    }
  }

  function closeVideoGenerationModal() {
    videoGenerationModal.visible = false
  }

  async function handleVideoGenerationConfirm(mode: VideoGenerationMode, config: VideoGenerationConfig) {
    closeVideoGenerationModal()

    try {
      const { feature_id } = await generateFeature(projectId, mode, {
        prompt: config.prompt,
        file_ids: config.fileIds,
        duration: config.duration,
        aspect_ratio: config.aspectRatio,
        resolution: config.resolution,
        bgm: config.bgm
      })

      const toolConfig = TOOL_TYPES.find(t => t.type === mode)
      features.value.unshift({
        id: feature_id,
        feature_type: mode,
        display_name: toolConfig ? t(toolConfig.titleKey) : mode,
        title: null,
        prompt: config.prompt || null,
        status: 'pending',
        error_message: null,
        created_at: new Date().toISOString(),
        started_at: null,
        finished_at: null
      })

      pollingFeatureIds.value.add(feature_id)
      startFeaturePolling()
    } catch (error) {
      console.error('Failed to generate video:', error)
    }
  }

  async function handleToolClick(toolType: string, customPrompt?: string, fileIds?: string[]) {
    if (!hasReadyFiles.value) return

    try {
      const readyFileIds = fileIds && fileIds.length > 0 ? fileIds : readyFiles.value.map(f => f.id)

      const { feature_id } = await generateFeature(projectId, toolType, {
        prompt: customPrompt || '',
        file_ids: readyFileIds
      })

      const toolConfig = TOOL_TYPES.find(t => t.type === toolType)
      features.value.unshift({
        id: feature_id,
        feature_type: toolType,
        display_name: toolConfig ? t(toolConfig.titleKey) : toolType,
        title: null,
        prompt: customPrompt || null,
        status: 'pending',
        error_message: null,
        created_at: new Date().toISOString(),
        started_at: null,
        finished_at: null
      })

      pollingFeatureIds.value.add(feature_id)
      startFeaturePolling()
    } catch (error) {
      console.error('Failed to generate feature:', error)
    }
  }

  async function handleFeatureClick(featureItem: FeatureListItem) {
    if (featureItem.status === 'pending' || featureItem.status === 'processing') {
      return
    }

    if (featureItem.status === 'failed') {
      return
    }

    try {
      const feature = await getFeature(featureItem.id)
      activeFeature.value = feature

      if (rightPanelWidth.value < reportMinWidth) {
        rightPanelWidthBeforeReport.value = rightPanelWidth.value
        rightPanelWidth.value = reportMinWidth
      }
      showFeatureDetail.value = true
    } catch (error) {
      console.error('Failed to load feature detail:', error)
    }
  }

  function closeFeatureDetail() {
    showFeatureDetail.value = false
    activeFeature.value = null
    if (rightPanelWidthBeforeReport.value !== null) {
      rightPanelWidth.value = rightPanelWidthBeforeReport.value
      rightPanelWidthBeforeReport.value = null
    }
  }

  async function renameFeatureTitle(id: string, newTitle: string) {
    await updateFeature(id, { title: newTitle })

    const feature = features.value.find(f => f.id === id)
    if (feature) feature.title = newTitle

    if (activeFeature.value?.id === id) {
      activeFeature.value.title = newTitle
    }
  }

  function handleRenameFeature(feature: FeatureListItem) {
    openRenameModal('feature', feature.id, feature.title || '')
  }

  async function handleFeatureDetailRename(newTitle: string) {
    if (!activeFeature.value) return

    try {
      const id = activeFeature.value.id
      await renameFeatureTitle(id, newTitle)

      showToast(t('ui.renameSuccess'), 'success')
    } catch (error) {
      console.error('Failed to rename feature:', error)
      showToast(t('ui.renameFailed'), 'error')
    }
  }

  async function handleRegenerateFeature(featureItem: FeatureListItem) {
    featureMenuId.value = null

    try {
      await deleteFeature(featureItem.id)

      features.value = features.value.filter(f => f.id !== featureItem.id)

      await handleToolClick(featureItem.feature_type)
    } catch (error) {
      console.error('Failed to regenerate feature:', error)
    }
  }

  async function handleDeleteFeature(featureItem: FeatureListItem) {
    featureMenuId.value = null

    try {
      await deleteFeature(featureItem.id)
      features.value = features.value.filter(f => f.id !== featureItem.id)

      if (activeFeature.value?.id === featureItem.id) {
        closeFeatureDetail()
      }
    } catch (error) {
      console.error('Failed to delete feature:', error)
    }
  }

  return {
    features,
    activeFeature,
    showFeatureDetail,
    featureMenuId,
    pollingFeatureIds,
    processingToolTypes,
    toolConfigModal,
    imageGenerationModal,
    imageFilesForGeneration,
    videoGenerationModal,
    videoFilesForGeneration,
    loadFeatures,
    startFeaturePolling,
    stopFeaturePolling,
    openToolConfig,
    closeToolConfig,
    handleToolConfigConfirm,
    closeImageGenerationModal,
    handleImageGenerationConfirm,
    closeVideoGenerationModal,
    handleVideoGenerationConfirm,
    handleToolClick,
    handleFeatureClick,
    closeFeatureDetail,
    renameFeatureTitle,
    handleRenameFeature,
    handleFeatureDetailRename,
    handleRegenerateFeature,
    handleDeleteFeature,
  }
}
