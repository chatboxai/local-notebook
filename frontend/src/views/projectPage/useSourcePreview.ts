import { computed, nextTick, ref, type Ref } from 'vue'
import type SourcePanel from '@/components/project/source/SourcePanel.vue'
import type { AudioTranscriptGroup, SourceViewMode } from '@/components/project/source/types'
import {
  getAudioPreviewUrl,
  getBlocksLocation,
  getFile,
  getFileContent,
  getFilePageInfo,
  type FilePageInfo,
  type FoundBlock,
} from '@/services/api'
import type { FileContent, FileInfo } from '@/types'
import { isAudioFile, isImageFile } from './fileHelpers'

type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface ImageCitationSource {
  fileId: string
  fileName?: string
  imageName?: string
  imageIndex?: number
  page?: number
}

interface UseSourcePreviewOptions {
  files: Ref<FileInfo[]>
  leftPanelWidth: Ref<number>
  copyTextToClipboard: (text: string) => Promise<void>
  showToast: (message: string, type?: ToastType, duration?: number) => void
  previewMinWidth?: number
}

export function useSourcePreview({
  files,
  leftPanelWidth,
  copyTextToClipboard,
  showToast,
  previewMinWidth = 700,
}: UseSourcePreviewOptions) {
  const sourcePanelRef = ref<InstanceType<typeof SourcePanel> | null>(null)
  const isPreviewMode = ref(false)
  const previewingFileContent = ref<FileContent | null>(null)
  const previewingFileName = ref('')
  const previewingFile = ref<FileInfo | null>(null)
  const highlightBlockIds = ref<string[]>([])
  const activeAudioBlockId = ref<string | null>(null)
  const fileContentCache = ref<Map<string, FileContent>>(new Map())
  const pageInfoCache = ref<Map<string, FilePageInfo>>(new Map())
  const isLoadingContent = ref(false)
  const summaryExpanded = ref(true)
  const isPdfFile = ref(false)
  const supportsRawView = ref(false)
  const viewMode = ref<SourceViewMode>('raw')
  const currentBlockIds = ref<string[]>([])
  const pdfPageInfo = ref<FilePageInfo | null>(null)
  const currentPageNum = ref(1)
  const jumpToPageInput = ref('')
  const selectedPdfBlock = ref<FoundBlock | null>(null)
  const copyPanelVisible = ref(false)
  const copyPanelPosition = ref<{ top: number; left: number } | null>(null)
  const leftPanelWidthBeforePreview = ref<number | null>(null)

  const isRawViewMode = computed(() => isPdfFile.value && viewMode.value === 'raw')

  const parsedBlocksByPage = computed<Map<number, FileContent['blocks']>>(() => {
    if (!previewingFileContent.value?.blocks) return new Map<number, FileContent['blocks']>()

    const grouped = new Map<number, FileContent['blocks']>()
    for (const block of previewingFileContent.value.blocks) {
      const page = block.page || 1
      if (!grouped.has(page)) {
        grouped.set(page, [])
      }
      grouped.get(page)!.push(block)
    }
    return grouped
  })

  const parsedTotalPages = computed(() => {
    if (!previewingFileContent.value?.blocks) return 0
    let maxPage = 0
    for (const block of previewingFileContent.value.blocks) {
      if (block.page && block.page > maxPage) {
        maxPage = block.page
      }
    }
    return maxPage
  })

  const visibleParsedPages = computed(() => {
    if (!isPdfFile.value || isRawViewMode.value || parsedTotalPages.value === 0) return []

    const pages: number[] = []
    for (let p = 1; p <= parsedTotalPages.value; p++) {
      pages.push(p)
    }
    return pages
  })

  const currentTotalPages = computed(() => {
    if (isRawViewMode.value) {
      return sourcePanelRef.value?.totalPages || 0
    }
    return parsedTotalPages.value
  })

  const isPreviewingImage = computed(() => {
    return previewingFile.value ? isImageFile(previewingFile.value) : false
  })

  const isPreviewingAudio = computed(() => {
    return previewingFile.value ? isAudioFile(previewingFile.value) : false
  })

  const audioPreviewUrl = computed(() => {
    return previewingFile.value && isPreviewingAudio.value
      ? getAudioPreviewUrl(previewingFile.value.id)
      : ''
  })

  const audioSpeakerCount = computed(() => {
    const fromMeta = previewingFileContent.value?.audio_meta?.speaker_count
    if (fromMeta && fromMeta > 0) return fromMeta
    const speakers = new Set<number>()
    for (const block of previewingFileContent.value?.blocks || []) {
      const speaker = Number(block.extra?.speaker)
      if (Number.isFinite(speaker)) speakers.add(speaker)
    }
    return speakers.size
  })

  const audioTranscriptGroups = computed<AudioTranscriptGroup[]>(() => {
    const blocks = previewingFileContent.value?.blocks || []
    if (!blocks.length) return []

    if (audioSpeakerCount.value <= 1) {
      return [{
        key: 'speaker-all',
        speaker: null,
        speakerLabel: '',
        blocks
      }]
    }

    const groups: AudioTranscriptGroup[] = []
    for (const block of blocks) {
      const speakerValue = Number(block.extra?.speaker)
      const speaker = Number.isFinite(speakerValue) ? speakerValue : null
      const previous = groups[groups.length - 1]
      if (previous && previous.speaker === speaker) {
        previous.blocks.push(block)
        continue
      }
      groups.push({
        key: `speaker-${speaker ?? 'unknown'}-${groups.length}`,
        speaker,
        speakerLabel: getAudioSpeakerLabel(block),
        blocks: [block]
      })
    }
    return groups
  })

  const previewSummary = computed(() => {
    if (previewingFileContent.value?.summary) {
      return previewingFileContent.value.summary
    }

    return ''
  })

  const showSourcePreview = computed(() =>
    Boolean(isPreviewMode.value && (previewingFileContent.value || isPreviewingImage.value || isPdfFile.value))
  )

  function getPreviewContentEl(): HTMLDivElement | null {
    return sourcePanelRef.value?.previewContentEl || null
  }

  function getAudioPlayerEl(): HTMLAudioElement | null {
    return sourcePanelRef.value?.audioPlayerEl || null
  }

  function clearSourceHighlights() {
    sourcePanelRef.value?.clearHighlights()
    highlightBlockIds.value = []
    currentBlockIds.value = []
  }

  function clearSelectedBlock() {
    selectedPdfBlock.value = null
    copyPanelVisible.value = false
    copyPanelPosition.value = null
    sourcePanelRef.value?.clearSelectedBlock()
  }

  function handlePdfPageChange(pageNum: number) {
    currentPageNum.value = pageNum
  }

  function handlePdfLoading(loading: boolean) {
    isLoadingContent.value = loading
  }

  function handlePdfBlockClick(block: FoundBlock, position: { top: number; left: number }) {
    selectedPdfBlock.value = block
    copyPanelVisible.value = true

    const panelWidth = 320
    const viewportWidth = window.innerWidth
    let panelLeft = position.left + 8

    if (panelLeft + panelWidth > viewportWidth - 20) {
      panelLeft = position.left - panelWidth - 8
    }

    copyPanelPosition.value = {
      top: position.top,
      left: Math.max(8, panelLeft)
    }
  }

  function handlePdfClearSelection() {
    selectedPdfBlock.value = null
    copyPanelVisible.value = false
    copyPanelPosition.value = null
  }

  async function copySelectedBlockText() {
    if (!selectedPdfBlock.value) return

    try {
      await copyTextToClipboard(selectedPdfBlock.value.content)
      showToast('复制成功')
    } catch (error) {
      console.error('Failed to copy text:', error)
      showToast('复制失败', 'error')
    }
  }

  async function loadFileContent(fileId: string): Promise<FileContent | null> {
    if (fileContentCache.value.has(fileId)) {
      return fileContentCache.value.get(fileId)!
    }

    isLoadingContent.value = true
    try {
      const content = await getFileContent(fileId)
      fileContentCache.value.set(fileId, content)
      return content
    } catch (error) {
      console.error('Failed to load file content:', error)
      return null
    } finally {
      isLoadingContent.value = false
    }
  }

  async function openFilePreview(fileId: string, segmentId?: string) {
    const file = files.value.find(f => f.id === fileId)
    if (!file || file.status !== 'ready') return

    const isSwitchingFile = previewingFile.value && previewingFile.value.id !== fileId
    const isFirstOpen = !isPreviewMode.value
    const isImage = isImageFile(file)

    summaryExpanded.value = !segmentId

    if (isFirstOpen) {
      leftPanelWidthBeforePreview.value = leftPanelWidth.value
      if (leftPanelWidth.value < previewMinWidth) {
        leftPanelWidth.value = previewMinWidth
      }
    }

    if (isSwitchingFile || isFirstOpen) {
      previewingFileName.value = file.file_name
      previewingFile.value = file
      isPreviewMode.value = true
      highlightBlockIds.value = []
      isLoadingContent.value = true

      previewingFileContent.value = null
      isPdfFile.value = false
      supportsRawView.value = false
      viewMode.value = 'raw'
      currentBlockIds.value = []
      pdfPageInfo.value = null
      currentPageNum.value = 1
      jumpToPageInput.value = ''
      activeAudioBlockId.value = null

      if (isSwitchingFile) {
        await nextTick()
        const previewContent = getPreviewContentEl()
        if (previewContent) {
          previewContent.scrollTop = 0
        }
      }

      if (!isImage) {
        try {
          const fileInfo = await getFile(fileId)

          let pageInfo = pageInfoCache.value.get(fileId)
          if (!pageInfo) {
            pageInfo = await getFilePageInfo(fileId)
            pageInfoCache.value.set(fileId, pageInfo)
          }

          if (pageInfo.has_pages && file.file_type === 'pdf') {
            isPdfFile.value = true
            supportsRawView.value = fileInfo.supports_raw_view ?? true
            pdfPageInfo.value = pageInfo

            viewMode.value = 'raw'
          } else {
            const content = await loadFileContent(fileId)
            if (!content) {
              isLoadingContent.value = false
              return
            }
            previewingFileContent.value = content
          }
        } catch (error) {
          console.error('[Preview] Failed to get page info:', error)

          const content = await loadFileContent(fileId)
          if (content) {
            previewingFileContent.value = content
          }
        }
      }

      if (!isPdfFile.value || viewMode.value !== 'raw') {
        isLoadingContent.value = false
      }

      await nextTick()
      const previewContent = getPreviewContentEl()
      if (previewContent) {
        previewContent.scrollTop = 0
      }
    }

    highlightBlockIds.value = []

    if (segmentId && !isImage) {
      await scrollToSegment(fileId, segmentId)
    }
  }

  function parseOptionalInt(value?: string): number | undefined {
    if (!value) return undefined
    const parsed = Number.parseInt(value, 10)
    return Number.isFinite(parsed) ? parsed : undefined
  }

  function imageBlockMatches(extra: any, citation: ImageCitationSource) {
    if (!extra?.is_image) return false
    if (citation.imageIndex !== undefined && extra.image_index === citation.imageIndex) return true
    if (citation.imageName && extra.image_name === citation.imageName) return true
    return false
  }

  async function openImageCitationSource(citation: ImageCitationSource) {
    await jumpToPdfImageLocation(citation)
  }

  async function jumpToPdfImageLocation(citation: ImageCitationSource) {
    await openFilePreview(citation.fileId)

    await nextTick()

    const pageInfoImageBlock = pdfPageInfo.value?.blocks?.find(block =>
      imageBlockMatches(block.extra, citation)
    )
    const targetPage = citation.page && citation.page > 0
      ? citation.page
      : pageInfoImageBlock?.page || 0
    const targetBbox = pageInfoImageBlock?.extra?.bbox

    if (isRawViewMode.value && pdfPageInfo.value && targetPage > 0) {
      await nextTick()

      const maxWait = 5000
      const checkInterval = 50
      let waited = 0
      while (waited < maxWait) {
        if (sourcePanelRef.value?.isDocumentLoaded) {
          break
        }
        await new Promise(resolve => setTimeout(resolve, checkInterval))
        waited += checkInterval
      }

      await waitForLayoutStable()

      await sourcePanelRef.value?.scrollToPageAndHighlightBbox(targetPage, targetBbox)
    } else if (previewingFileContent.value) {
      const imageBlock = previewingFileContent.value.blocks.find(block =>
        imageBlockMatches(block.extra, citation)
      )

      if (imageBlock) {
        highlightBlockIds.value = [imageBlock.block_id]
        currentBlockIds.value = [imageBlock.block_id]
        await nextTick()
        scrollToBlock(imageBlock.block_id)
      } else if (targetPage > 0) {
        const pageSection = getPreviewContentEl()?.querySelector(`[data-page="${targetPage}"]`) as HTMLElement
        pageSection?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
  }

  function getAudioSpeakerLabel(block: FileContent['blocks'][number]): string {
    const speaker = Number(block.extra?.speaker)
    if (!Number.isFinite(speaker)) return '说话人'
    return `说话人 ${speaker + 1}`
  }

  function getAudioStartMs(block: FileContent['blocks'][number]): number | null {
    const value = Number(block.extra?.time_start)
    return Number.isFinite(value) ? value : null
  }

  function getAudioEndMs(block: FileContent['blocks'][number]): number | null {
    const value = Number(block.extra?.time_end)
    return Number.isFinite(value) ? value : null
  }

  function findAudioBlockAtTime(ms: number): FileContent['blocks'][number] | null {
    const blocks = previewingFileContent.value?.blocks || []
    for (const block of blocks) {
      const start = getAudioStartMs(block)
      const end = getAudioEndMs(block)
      if (start === null || end === null) continue
      if (ms >= start && ms < Math.max(end, start + 1)) return block
    }
    return null
  }

  function handleAudioPlay() {
    highlightBlockIds.value = []
  }

  function handleAudioTimeUpdate() {
    const player = getAudioPlayerEl()
    if (!player) return
    const currentMs = Math.round(player.currentTime * 1000)

    const activeBlock = findAudioBlockAtTime(currentMs)
    if (!activeBlock || activeBlock.block_id === activeAudioBlockId.value) return

    activeAudioBlockId.value = activeBlock.block_id
    if (!player.paused) {
      nextTick(() => scrollToBlock(activeBlock.block_id))
    }
  }

  async function seekAudioToBlock(block: FileContent['blocks'][number]) {
    const start = getAudioStartMs(block)
    if (start === null) return
    await seekAudioToMs(start, [block.block_id])
  }

  async function seekAudioToMs(startMs: number, blockIds: string[]) {
    await nextTick()
    const player = getAudioPlayerEl()
    if (player) {
      player.currentTime = Math.max(0, startMs / 1000)
    }
    activeAudioBlockId.value = blockIds[0] || null
    highlightBlockIds.value = blockIds
    if (blockIds[0]) {
      await nextTick()
      scrollToBlock(blockIds[0])
    }
  }

  function getAudioStartForBlockIds(blockIds: string[]): number | null {
    const blocks = previewingFileContent.value?.blocks || []
    const ids = new Set(blockIds)
    const starts = blocks
      .filter(block => ids.has(block.block_id))
      .map(block => getAudioStartMs(block))
      .filter((value): value is number => value !== null)
    return starts.length ? Math.min(...starts) : null
  }

  async function scrollToSegment(_fileId: string, segmentId: string) {
    let blockIds: string[] = []
    if (pdfPageInfo.value) {
      const segment = pdfPageInfo.value.segments.find((s: { segment_id: string }) => s.segment_id === segmentId)
      if (segment) blockIds = segment.block_ids
    } else if (previewingFileContent.value) {
      const segment = previewingFileContent.value.segments.find(s => s.segment_id === segmentId)
      if (segment) blockIds = segment.block_ids
    }

    if (blockIds.length === 0) return

    currentBlockIds.value = blockIds

    if (isPreviewingAudio.value && previewingFileContent.value) {
      const startMs = getAudioStartForBlockIds(blockIds)
      if (startMs !== null) {
        await seekAudioToMs(startMs, blockIds)
      } else {
        highlightBlockIds.value = blockIds
        await nextTick()
        if (blockIds[0]) {
          scrollToBlock(blockIds[0])
        }
      }
      return
    }

    if (isRawViewMode.value && pdfPageInfo.value) {
      await nextTick()

      const maxWait = 5000
      const checkInterval = 50
      let waited = 0
      while (waited < maxWait) {
        if (sourcePanelRef.value?.isDocumentLoaded) {
          break
        }
        await new Promise(resolve => setTimeout(resolve, checkInterval))
        waited += checkInterval
      }

      await waitForLayoutStable()

      await sourcePanelRef.value?.scrollToSegment(segmentId)
    } else if (previewingFileContent.value) {
      await new Promise(resolve => setTimeout(resolve, 100))
      highlightBlockIds.value = blockIds
      await nextTick()
      const firstBlockId = blockIds[0]
      if (firstBlockId) {
        scrollToBlock(firstBlockId)
      }
    }
  }

  async function waitForLayoutStable(maxWait = 500): Promise<void> {
    const previewContent = getPreviewContentEl()
    if (!previewContent) {
      await new Promise(resolve => setTimeout(resolve, 300))
      return
    }

    let lastWidth = previewContent.clientWidth
    let lastHeight = previewContent.clientHeight
    let stableCount = 0
    const startTime = Date.now()

    while (Date.now() - startTime < maxWait) {
      await new Promise<void>(resolve => requestAnimationFrame(() => resolve()))

      const currentWidth = previewContent.clientWidth
      const currentHeight = previewContent.clientHeight

      if (currentWidth === lastWidth && currentHeight === lastHeight) {
        stableCount++

        if (stableCount >= 3) {
          return
        }
      } else {
        stableCount = 0
        lastWidth = currentWidth
        lastHeight = currentHeight
      }
    }
  }

  async function switchViewMode(mode: SourceViewMode) {
    if (mode === viewMode.value || !previewingFile.value) return

    const fileId = previewingFile.value.id
    const savedPageNum = currentPageNum.value
    const savedBlockIds = currentBlockIds.value

    viewMode.value = mode

    try {
      if (mode === 'raw') {
        isLoadingContent.value = true

        previewingFileContent.value = null
        highlightBlockIds.value = []

        currentPageNum.value = savedPageNum

        await nextTick()
        await new Promise(resolve => setTimeout(resolve, 200))

        if (savedBlockIds.length > 0 && pdfPageInfo.value) {
          const segment = pdfPageInfo.value.segments.find(s =>
            s.block_ids.some(bid => savedBlockIds.includes(bid))
          )
          if (segment) {
            await sourcePanelRef.value?.scrollToSegment(segment.segment_id)
          }
        } else {
          sourcePanelRef.value?.goToPage(savedPageNum)
        }
      } else {
        isLoadingContent.value = true

        const content = await loadFileContent(fileId)
        if (content) {
          previewingFileContent.value = content
        }

        if (savedBlockIds.length > 0) {
          highlightBlockIds.value = savedBlockIds

          try {
            const locationResponse = await getBlocksLocation(fileId, savedBlockIds)
            const firstBlockId = savedBlockIds[0]
            if (firstBlockId) {
              const location = locationResponse.blocks[firstBlockId]
              if (location && location.exists) {
                currentPageNum.value = location.page
              }
            }
          } catch (error) {
            console.error('Failed to get block location:', error)
          }

          await nextTick()
          await new Promise(resolve => setTimeout(resolve, 100))
          const firstBlockId = savedBlockIds[0]
          if (firstBlockId) {
            scrollToBlock(firstBlockId)
          }
        }
      }
    } catch (error) {
      console.error('Failed to switch view mode:', error)
    } finally {
      if (viewMode.value !== 'raw') {
        isLoadingContent.value = false
      }
    }
  }

  function closePreview() {
    isPreviewMode.value = false
    previewingFileContent.value = null
    previewingFileName.value = ''
    previewingFile.value = null
    highlightBlockIds.value = []
    activeAudioBlockId.value = null

    isPdfFile.value = false
    supportsRawView.value = false
    viewMode.value = 'raw'
    currentBlockIds.value = []
    pdfPageInfo.value = null
    currentPageNum.value = 1
    jumpToPageInput.value = ''

    if (leftPanelWidthBeforePreview.value !== null) {
      leftPanelWidth.value = leftPanelWidthBeforePreview.value
      leftPanelWidthBeforePreview.value = null
    }
  }

  function scrollToBlock(blockId: string) {
    const container = getPreviewContentEl()
    if (!container) return
    const blockEl = container.querySelector(`[data-block-id="${blockId}"]`) as HTMLElement
    if (blockEl) {
      const containerRect = container.getBoundingClientRect()
      const blockRect = blockEl.getBoundingClientRect()
      const targetScrollTop = container.scrollTop + (blockRect.top - containerRect.top) - (containerRect.height / 2) + (blockRect.height / 2)
      container.scrollTo({ top: targetScrollTop, behavior: 'smooth' })
    }
  }

  async function jumpToPage() {
    if (currentTotalPages.value === 0 || !previewingFile.value) return

    const pageNum = parseInt(jumpToPageInput.value)
    if (isNaN(pageNum) || pageNum < 1 || pageNum > currentTotalPages.value) {
      jumpToPageInput.value = ''
      return
    }

    currentPageNum.value = pageNum
    jumpToPageInput.value = ''

    if (isRawViewMode.value) {
      sourcePanelRef.value?.goToPage(pageNum)
    } else {
      await nextTick()
      const pageSection = getPreviewContentEl()?.querySelector(`[data-page="${pageNum}"]`) as HTMLElement
      if (pageSection) {
        pageSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
  }

  function handlePreviewScroll() {
    if (isRawViewMode.value) return
    const container = getPreviewContentEl()
    if (!container || !isPdfFile.value || currentTotalPages.value === 0) return

    if (copyPanelVisible.value) {
      clearSelectedBlock()
    }

    const containerRect = container.getBoundingClientRect()
    const containerTop = containerRect.top

    const pageSections = container.querySelectorAll('[data-page]')
    let currentVisiblePage = 1

    for (const section of pageSections) {
      const rect = section.getBoundingClientRect()

      if (rect.top <= containerTop + containerRect.height / 2) {
        currentVisiblePage = parseInt(section.getAttribute('data-page') || '1')
      }
    }

    if (currentVisiblePage !== currentPageNum.value) {
      currentPageNum.value = currentVisiblePage
    }
  }

  function handleSourceFileDeleted(fileId: string) {
    fileContentCache.value.delete(fileId)
    pageInfoCache.value.delete(fileId)

    if (previewingFile.value?.id === fileId || previewingFileContent.value?.file_id === fileId) {
      closePreview()
    }
  }

  return {
    sourcePanelRef,
    isPreviewMode,
    previewingFileContent,
    previewingFileName,
    previewingFile,
    highlightBlockIds,
    activeAudioBlockId,
    isLoadingContent,
    summaryExpanded,
    isPdfFile,
    supportsRawView,
    viewMode,
    currentBlockIds,
    pdfPageInfo,
    currentPageNum,
    jumpToPageInput,
    selectedPdfBlock,
    copyPanelVisible,
    copyPanelPosition,
    isRawViewMode,
    parsedBlocksByPage,
    visibleParsedPages,
    currentTotalPages,
    isPreviewingImage,
    isPreviewingAudio,
    audioPreviewUrl,
    audioTranscriptGroups,
    audioSpeakerCount,
    previewSummary,
    showSourcePreview,
    previewMinWidth,
    clearSourceHighlights,
    clearSelectedBlock,
    handlePdfPageChange,
    handlePdfLoading,
    handlePdfBlockClick,
    handlePdfClearSelection,
    copySelectedBlockText,
    openFilePreview,
    parseOptionalInt,
    openImageCitationSource,
    handleAudioPlay,
    handleAudioTimeUpdate,
    seekAudioToBlock,
    switchViewMode,
    closePreview,
    jumpToPage,
    handlePreviewScroll,
    handleSourceFileDeleted,
  }
}
