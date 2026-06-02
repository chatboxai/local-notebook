<template>
  <div class="pdf-viewer" ref="containerRef" @scroll="handleScroll">
    
    <div
      v-if="placeholderBefore.height > 0"
      class="pdf-placeholder"
      :style="{ height: placeholderBefore.height + 'px' }"
    >
      <div class="placeholder-hint" v-if="placeholderBefore.pages > 0">
        第 1 - {{ placeholderBefore.pages }} 页
      </div>
    </div>

    
    <div
      v-for="pageNum in visiblePages"
      :key="pageNum"
      :data-page="pageNum"
      class="pdf-page-section"
    >
      
      <div class="page-divider">
        <span class="page-divider-line"></span>
        <span class="page-divider-text">第 {{ pageNum }} 页</span>
        <span class="page-divider-line"></span>
      </div>

      
      <div class="pdf-page-container" :data-page-num="pageNum">
        <div class="pdf-page-wrapper">
          
          <canvas
            :ref="(el) => setCanvasRef(pageNum, el as HTMLCanvasElement)"
            class="pdf-canvas"
            @click="handleCanvasClick($event, pageNum)"
          ></canvas>

          
          <div class="pdf-highlight-layer">
            <div
              v-for="(box, idx) in getHighlightBoxesForPage(pageNum)"
              :key="idx"
              class="pdf-highlight-box"
              :style="{
                left: box.left + '%',
                top: box.top + '%',
                width: box.width + '%',
                height: box.height + '%'
              }"
            ></div>
          </div>

          
          <div
            v-if="selectedBlockHighlight && selectedBlockHighlight.page === pageNum"
            class="pdf-selected-block-highlight"
            :style="{
              left: selectedBlockHighlight.left + '%',
              top: selectedBlockHighlight.top + '%',
              width: selectedBlockHighlight.width + '%',
              height: selectedBlockHighlight.height + '%'
            }"
          ></div>

          
          <div v-if="!isPageRendered(pageNum)" class="pdf-page-loading">
            <span>渲染中...</span>
          </div>
        </div>
      </div>
    </div>

    
    <div
      v-if="placeholderAfter.height > 0"
      class="pdf-placeholder"
      :style="{ height: placeholderAfter.height + 'px' }"
    >
      <div class="placeholder-hint" v-if="placeholderAfter.pages > 0">
        第 {{ totalPages - placeholderAfter.pages + 1 }} - {{ totalPages }} 页
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef, computed, watch, nextTick, triggerRef } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import type { PDFDocumentProxy } from 'pdfjs-dist'
import PdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { getPdfRawData, getBlocksBbox, findBlockByPosition, type FilePageInfo, type FoundBlock } from '@/services/api'


pdfjsLib.GlobalWorkerOptions.workerSrc = PdfWorker


interface Props {
  fileId: string
  pageInfo: FilePageInfo | null
}

const props = defineProps<Props>()


const emit = defineEmits<{
  (e: 'page-change', pageNum: number): void
  (e: 'block-click', block: FoundBlock, position: { top: number; left: number }): void
  (e: 'clear-selection'): void
  (e: 'loading', isLoading: boolean): void
}>()


const PDF_SCALE = 1.5
const RENDER_BUFFER = 3
const DEFAULT_PAGE_HEIGHT = 800
const PAGE_GAP = 84
const MAX_RENDER_RANGE = 15


const containerRef = ref<HTMLDivElement | null>(null)
const pdfDoc = shallowRef<PDFDocumentProxy | null>(null)
const renderedPages = ref<Set<number>>(new Set())
const renderingPages = ref<Set<number>>(new Set())
const canvasRefs = new Map<number, HTMLCanvasElement>()
const isDocumentLoaded = ref(false)


const pageDimensions = ref<Map<number, { width: number; height: number }>>(new Map())


const currentPageNum = ref(1)


const renderRange = ref<{ start: number; end: number }>({ start: 1, end: 1 })


let isScrollLocked = false


interface HighlightBox {
  page: number
  left: number
  top: number
  width: number
  height: number
}
const highlightBoxes = ref<HighlightBox[]>([])
const selectedBlockHighlight = ref<HighlightBox | null>(null)


const totalPages = computed(() => pdfDoc.value?.numPages || 0)


const visiblePages = computed(() => {
  if (!props.pageInfo || totalPages.value === 0) return []

  const pages: number[] = []
  for (let p = renderRange.value.start; p <= renderRange.value.end; p++) {
    pages.push(p)
  }
  return pages
})


function expandRenderRangeTo(targetPage: number) {
  const buffer = RENDER_BUFFER
  const newStart = Math.max(1, targetPage - buffer)
  const newEnd = Math.min(totalPages.value, targetPage + buffer)

  const expandedStart = Math.min(renderRange.value.start, newStart)
  const expandedEnd = Math.max(renderRange.value.end, newEnd)

  
  if (expandedEnd - expandedStart + 1 > MAX_RENDER_RANGE) {
    resetRenderRange(targetPage)
  } else {
    renderRange.value = { start: expandedStart, end: expandedEnd }
  }
}


function resetRenderRange(centerPage: number) {
  const buffer = RENDER_BUFFER
  renderRange.value = {
    start: Math.max(1, centerPage - buffer),
    end: Math.min(totalPages.value, centerPage + buffer)
  }
}


function isInRenderRange(pageNum: number): boolean {
  return pageNum >= renderRange.value.start && pageNum <= renderRange.value.end
}


function needsRangeReset(targetPage: number): boolean {
  const buffer = RENDER_BUFFER
  const targetStart = Math.max(1, targetPage - buffer)
  const targetEnd = Math.min(totalPages.value, targetPage + buffer)

  
  const hasOverlap = !(targetEnd < renderRange.value.start || targetStart > renderRange.value.end)
  return !hasOverlap
}


const placeholderBefore = computed(() => {
  if (visiblePages.value.length === 0) return { height: 0, pages: 0 }

  const firstVisible = Math.min(...visiblePages.value)
  if (firstVisible <= 1) return { height: 0, pages: 0 }

  let height = 0
  for (let p = 1; p < firstVisible; p++) {
    const dim = pageDimensions.value.get(p)
    height += (dim?.height || DEFAULT_PAGE_HEIGHT) + PAGE_GAP
  }

  return { height, pages: firstVisible - 1 }
})


const placeholderAfter = computed(() => {
  if (visiblePages.value.length === 0 || totalPages.value === 0) return { height: 0, pages: 0 }

  const lastVisible = Math.max(...visiblePages.value)
  if (lastVisible >= totalPages.value) return { height: 0, pages: 0 }

  let height = 0
  for (let p = lastVisible + 1; p <= totalPages.value; p++) {
    const dim = pageDimensions.value.get(p)
    height += (dim?.height || DEFAULT_PAGE_HEIGHT) + PAGE_GAP
  }

  return { height, pages: totalPages.value - lastVisible }
})


function isPageRendered(pageNum: number): boolean {
  return renderedPages.value.has(pageNum)
}


function getHighlightBoxesForPage(pageNum: number): HighlightBox[] {
  return highlightBoxes.value.filter(box => box.page === pageNum)
}


function setCanvasRef(pageNum: number, el: HTMLCanvasElement | null) {
  if (el) {
    canvasRefs.set(pageNum, el)
    
    if (pdfDoc.value && !renderedPages.value.has(pageNum) && !renderingPages.value.has(pageNum)) {
      renderPage(pageNum)
    }
  } else {
    
    canvasRefs.delete(pageNum)
    
    if (renderedPages.value.has(pageNum)) {
      const newRendered = new Set(renderedPages.value)
      newRendered.delete(pageNum)
      renderedPages.value = newRendered
    }
  }
}


async function renderPage(pageNum: number) {
  if (!pdfDoc.value || renderingPages.value.has(pageNum) || renderedPages.value.has(pageNum)) {
    return
  }

  const canvas = canvasRefs.get(pageNum)
  if (!canvas) return

  renderingPages.value = new Set([...renderingPages.value, pageNum])
  triggerRef(renderingPages)

  try {
    const page = await pdfDoc.value.getPage(pageNum)
    const viewport = page.getViewport({ scale: PDF_SCALE })

    
    canvas.width = viewport.width
    canvas.height = viewport.height

    
    const newDimensions = new Map(pageDimensions.value)
    newDimensions.set(pageNum, { width: viewport.width, height: viewport.height })
    pageDimensions.value = newDimensions

    
    const context = canvas.getContext('2d')
    if (context) {
      await page.render({
        canvasContext: context,
        viewport: viewport,
        canvas: canvas
      } as any).promise
    }

    
    renderedPages.value = new Set([...renderedPages.value, pageNum])
    triggerRef(renderedPages)
  } catch (error) {
    console.error(`Failed to render PDF page ${pageNum}:`, error)
  } finally {
    const newRenderingPages = new Set(renderingPages.value)
    newRenderingPages.delete(pageNum)
    renderingPages.value = newRenderingPages
    triggerRef(renderingPages)
  }
}


async function preloadPageDimensions() {
  if (!pdfDoc.value) return

  const newDimensions = new Map<number, { width: number; height: number }>()
  const numPages = pdfDoc.value.numPages

  for (let i = 1; i <= numPages; i++) {
    try {
      const page = await pdfDoc.value.getPage(i)
      const viewport = page.getViewport({ scale: PDF_SCALE })
      newDimensions.set(i, { width: viewport.width, height: viewport.height })
    } catch (error) {
      console.error(`Failed to get page ${i} dimensions:`, error)
      newDimensions.set(i, { width: 600, height: DEFAULT_PAGE_HEIGHT })
    }
  }

  pageDimensions.value = newDimensions
}


async function loadDocument() {
  if (!props.fileId) return

  
  emit('loading', true)

  
  isDocumentLoaded.value = false
  renderedPages.value = new Set()
  renderingPages.value = new Set()
  pageDimensions.value = new Map()
  highlightBoxes.value = []
  canvasRefs.clear()
  currentPageNum.value = 1

  try {
    const pdfData = await getPdfRawData(props.fileId)
    const loadingTask = pdfjsLib.getDocument({ data: pdfData })
    pdfDoc.value = await loadingTask.promise

    
    await preloadPageDimensions()

    
    const numPages = pdfDoc.value.numPages
    renderRange.value = {
      start: 1,
      end: Math.min(numPages, 1 + RENDER_BUFFER)
    }

    
    isDocumentLoaded.value = true

    
    emit('loading', false)

    
    await nextTick()

    
    for (const pageNum of visiblePages.value) {
      const canvas = canvasRefs.get(pageNum)
      if (canvas && !renderedPages.value.has(pageNum) && !renderingPages.value.has(pageNum)) {
        renderPage(pageNum)
      }
    }
  } catch (error) {
    console.error('Failed to load PDF document:', error)
    emit('loading', false)
  }
}


function calculateCurrentPage(): number {
  if (!containerRef.value) return 1

  const container = containerRef.value
  const scrollTop = container.scrollTop
  const viewportHeight = container.clientHeight
  const viewportCenter = scrollTop + viewportHeight / 2

  
  const pageElements = container.querySelectorAll('.pdf-page-section[data-page]')

  for (const el of pageElements) {
    const pageNum = parseInt((el as HTMLElement).dataset.page || '1', 10)
    const rect = el.getBoundingClientRect()
    const containerRect = container.getBoundingClientRect()

    
    const elementTop = rect.top - containerRect.top + scrollTop
    const elementBottom = elementTop + rect.height

    
    if (viewportCenter >= elementTop && viewportCenter < elementBottom) {
      return pageNum
    }
  }

  
  if (visiblePages.value.length > 0) {
    const firstVisible = Math.min(...visiblePages.value)
    const lastVisible = Math.max(...visiblePages.value)

    
    const firstPageEl = container.querySelector(`.pdf-page-section[data-page="${firstVisible}"]`)
    if (firstPageEl) {
      const rect = firstPageEl.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()
      const elementTop = rect.top - containerRect.top + scrollTop

      if (viewportCenter < elementTop) {
        
        const placeholderHeight = placeholderBefore.value.height
        if (placeholderHeight > 0) {
          const ratio = scrollTop / placeholderHeight
          return Math.max(1, Math.floor(ratio * (firstVisible - 1)) + 1)
        }
      }
    }

    
    const lastPageEl = container.querySelector(`.pdf-page-section[data-page="${lastVisible}"]`)
    if (lastPageEl) {
      const rect = lastPageEl.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()
      const elementBottom = rect.bottom - containerRect.top + scrollTop

      if (viewportCenter >= elementBottom) {
        return Math.min(totalPages.value, lastVisible + 1)
      }
    }
  }

  return currentPageNum.value
}


function getRenderedScrollBounds(): { minScroll: number; maxScroll: number; firstPage: number; lastPage: number } | null {
  if (!containerRef.value || renderedPages.value.size === 0) return null

  const container = containerRef.value
  const renderedArray = Array.from(renderedPages.value).sort((a, b) => a - b)
  if (renderedArray.length === 0) return null

  
  const firstRendered = renderedArray[0]!
  const lastRendered = renderedArray[renderedArray.length - 1]!

  
  const firstSection = container.querySelector(`.pdf-page-section[data-page="${firstRendered}"]`)
  const lastSection = container.querySelector(`.pdf-page-section[data-page="${lastRendered}"]`)

  if (!firstSection || !lastSection) return null

  const containerRect = container.getBoundingClientRect()
  const firstRect = firstSection.getBoundingClientRect()
  const lastRect = lastSection.getBoundingClientRect()

  
  const minScroll = firstRect.top - containerRect.top + container.scrollTop
  
  const maxScroll = lastRect.bottom - containerRect.top + container.scrollTop - container.clientHeight

  return {
    minScroll: Math.max(0, minScroll),
    maxScroll: Math.max(0, maxScroll),
    firstPage: firstRendered,
    lastPage: lastRendered
  }
}


function handleScroll() {
  if (!containerRef.value || isScrollLocked) return

  const container = containerRef.value
  const currentScroll = container.scrollTop

  
  const bounds = getRenderedScrollBounds()
  if (bounds) {
    let needsClamp = false
    let clampedScroll = currentScroll

    
    if (currentScroll < bounds.minScroll) {
      clampedScroll = bounds.minScroll
      needsClamp = true
      
      if (bounds.firstPage > 1) {
        expandRenderRangeTo(bounds.firstPage - 1)
      }
    } else if (currentScroll > bounds.maxScroll) {
      clampedScroll = bounds.maxScroll
      needsClamp = true
      
      if (bounds.lastPage < totalPages.value) {
        expandRenderRangeTo(bounds.lastPage + 1)
      }
    }

    if (needsClamp) {
      container.scrollTop = clampedScroll
      
      const newPage = calculateCurrentPage()
      if (newPage !== currentPageNum.value) {
        currentPageNum.value = newPage
        emit('page-change', newPage)
      }
      return
    }
  }

  const newPage = calculateCurrentPage()

  if (newPage !== currentPageNum.value) {
    currentPageNum.value = newPage
    emit('page-change', newPage)

    
    const distanceToStart = newPage - renderRange.value.start
    const distanceToEnd = renderRange.value.end - newPage

    
    if (distanceToStart < 2 || distanceToEnd < 2) {
      expandRenderRangeTo(newPage)
    }
  }
}


async function handleCanvasClick(event: MouseEvent, pageNum: number) {
  const canvas = event.target as HTMLCanvasElement
  if (!canvas || canvas.tagName !== 'CANVAS') return

  
  if (!renderedPages.value.has(pageNum)) return

  const rect = canvas.getBoundingClientRect()
  
  if (rect.width === 0 || rect.height === 0) return
  const clickX = ((event.clientX - rect.left) / rect.width) * 1000
  const clickY = ((event.clientY - rect.top) / rect.height) * 1000

  try {
    const response = await findBlockByPosition(props.fileId, pageNum, clickX, clickY)

    if (response.found && response.block) {
      const [x1, y1, x2, y2] = response.block.bbox
      selectedBlockHighlight.value = {
        page: pageNum,
        left: x1 / 10,
        top: y1 / 10,
        width: (x2 - x1) / 10,
        height: (y2 - y1) / 10
      }

      
      const highlightTop = rect.top + (y1 / 1000) * rect.height
      const highlightRight = rect.left + (x2 / 1000) * rect.width

      emit('block-click', response.block, { top: highlightTop, left: highlightRight })
    } else {
      clearSelectedBlock()
    }
  } catch (error) {
    console.error('Failed to find block at position:', error)
  }
}


function clearSelectedBlock() {
  selectedBlockHighlight.value = null
  emit('clear-selection')
}


async function scrollToSegment(segmentId: string) {
  if (!props.pageInfo || !containerRef.value) return

  
  const segment = props.pageInfo.segments.find((s: { segment_id: string; block_ids: string[] }) => s.segment_id === segmentId)
  if (!segment || !segment.block_ids.length) return

  const blockIds = segment.block_ids

  try {
    
    const bboxResponse = await getBlocksBbox(props.fileId, blockIds)

    
    let targetPage = 1
    let firstBbox: number[] | null = null
    for (const blockId of blockIds) {
      const info = bboxResponse.blocks[blockId]
      if (info && info.page > 0) {
        targetPage = info.page
        if (info.bbox) {
          firstBbox = info.bbox
        }
        break
      }
    }

    
    const newHighlightBoxes: HighlightBox[] = []
    for (const blockId of blockIds) {
      const info = bboxResponse.blocks[blockId]
      if (info && info.bbox && info.page > 0) {
        const [x1, y1, x2, y2] = info.bbox
        newHighlightBoxes.push({
          page: info.page,
          left: x1 / 10,
          top: y1 / 10,
          width: (x2 - x1) / 10,
          height: (y2 - y1) / 10
        })
      }
    }

    
    const isAlreadyInRange = isInRenderRange(targetPage)
    const isAlreadyRendered = renderedPages.value.has(targetPage)

    if (isAlreadyInRange && isAlreadyRendered) {
      
      highlightBoxes.value = newHighlightBoxes
      currentPageNum.value = targetPage
      emit('page-change', targetPage)
      await nextTick()
      scrollToHighlightCenter(targetPage, firstBbox, true)
    } else if (needsRangeReset(targetPage)) {
      
      resetRenderRange(targetPage)
      currentPageNum.value = targetPage
      emit('page-change', targetPage)
      await nextTick()

      
      await waitForPageRendered(targetPage)

      
      highlightBoxes.value = newHighlightBoxes
      await nextTick()
      scrollToHighlightCenter(targetPage, firstBbox, false)
    } else {
      
      expandRenderRangeTo(targetPage)
      currentPageNum.value = targetPage
      emit('page-change', targetPage)
      await nextTick()

      
      await waitForPageRendered(targetPage)

      
      highlightBoxes.value = newHighlightBoxes
      await nextTick()
      scrollToHighlightCenter(targetPage, firstBbox, true)
    }
  } catch (error) {
    console.error('Failed to scroll to segment:', error)
  }
}


async function waitForPageRendered(pageNum: number, maxWait = 3000): Promise<boolean> {
  const startTime = Date.now()

  while (Date.now() - startTime < maxWait) {
    
    if (renderedPages.value.has(pageNum)) {
      
      await new Promise<void>(resolve => requestAnimationFrame(() => resolve()))
      return true
    }

    
    if (visiblePages.value.includes(pageNum) && !renderingPages.value.has(pageNum)) {
      await renderPage(pageNum)
      await nextTick()
      return true
    }

    
    await new Promise(resolve => setTimeout(resolve, 50))
  }

  return false
}


function scrollToHighlightCenter(targetPage: number, bbox: number[] | null, smooth = false) {
  if (!containerRef.value) return

  const container = containerRef.value

  
  const canvas = canvasRefs.get(targetPage)
  if (!canvas) return

  const canvasRect = canvas.getBoundingClientRect()

  
  if (canvasRect.width === 0 || canvasRect.height === 0) return

  const containerRect = container.getBoundingClientRect()

  
  const canvasTop = canvasRect.top - containerRect.top + container.scrollTop

  
  let boxCenterRatio = 0.5
  if (bbox && bbox.length >= 4) {
    const y1 = bbox[1]!
    const y2 = bbox[3]!
    
    boxCenterRatio = (y1 + y2) / 2 / 1000
  }

  
  const boxCenterY = canvasTop + canvasRect.height * boxCenterRatio

  
  const viewportHeight = container.clientHeight
  const targetScrollTop = Math.max(0, boxCenterY - viewportHeight / 2)

  
  isScrollLocked = true

  if (smooth) {
    container.scrollTo({ top: targetScrollTop, behavior: 'smooth' })
    
    setTimeout(() => {
      isScrollLocked = false
      updateCurrentPageAfterScroll()
    }, 350)
  } else {
    container.scrollTop = targetScrollTop
    
    isScrollLocked = false
    updateCurrentPageAfterScroll()
  }
}


function updateCurrentPageAfterScroll() {
  
  const newPage = calculateCurrentPage()
  if (newPage !== currentPageNum.value) {
    currentPageNum.value = newPage
    emit('page-change', newPage)
  }
}


function clearHighlights() {
  highlightBoxes.value = []
  selectedBlockHighlight.value = null
}


async function goToPage(pageNum: number) {
  if (pageNum < 1 || pageNum > totalPages.value || !containerRef.value) return

  
  const isAlreadyInRange = isInRenderRange(pageNum)
  const isAlreadyRendered = renderedPages.value.has(pageNum)

  if (isAlreadyInRange && isAlreadyRendered) {
    
    currentPageNum.value = pageNum
    emit('page-change', pageNum)
    scrollToPageTop(pageNum, true)
  } else if (needsRangeReset(pageNum)) {
    
    resetRenderRange(pageNum)
    currentPageNum.value = pageNum
    emit('page-change', pageNum)
    await nextTick()

    
    await waitForPageRendered(pageNum)

    
    scrollToPageTop(pageNum, false)
  } else {
    
    expandRenderRangeTo(pageNum)
    currentPageNum.value = pageNum
    emit('page-change', pageNum)
    await nextTick()

    
    await waitForPageRendered(pageNum)

    
    scrollToPageTop(pageNum, true)
  }
}


function scrollToPageTop(pageNum: number, smooth = false) {
  if (!containerRef.value) return

  const container = containerRef.value

  
  const pageSection = container.querySelector(`.pdf-page-section[data-page="${pageNum}"]`)
  if (!pageSection) return

  const containerRect = container.getBoundingClientRect()
  const sectionRect = pageSection.getBoundingClientRect()

  
  const sectionTop = sectionRect.top - containerRect.top + container.scrollTop

  
  isScrollLocked = true

  if (smooth) {
    container.scrollTo({ top: sectionTop, behavior: 'smooth' })
    
    setTimeout(() => {
      isScrollLocked = false
      updateCurrentPageAfterScroll()
    }, 350)
  } else {
    container.scrollTop = sectionTop
    
    isScrollLocked = false
    updateCurrentPageAfterScroll()
  }
}


async function scrollToPageAndHighlightBbox(pageNum: number, bbox?: number[]) {
  if (pageNum < 1 || pageNum > totalPages.value || !containerRef.value) return

  
  const newHighlightBoxes: HighlightBox[] = []
  if (bbox && bbox.length >= 4) {
    const x1 = bbox[0]!
    const y1 = bbox[1]!
    const x2 = bbox[2]!
    const y2 = bbox[3]!
    newHighlightBoxes.push({
      page: pageNum,
      left: x1 / 10,
      top: y1 / 10,
      width: (x2 - x1) / 10,
      height: (y2 - y1) / 10
    })
  }

  
  const isAlreadyInRange = isInRenderRange(pageNum)
  const isAlreadyRendered = renderedPages.value.has(pageNum)

  if (isAlreadyInRange && isAlreadyRendered) {
    
    highlightBoxes.value = newHighlightBoxes
    currentPageNum.value = pageNum
    emit('page-change', pageNum)
    await nextTick()
    scrollToHighlightCenter(pageNum, bbox || null, true)
  } else if (needsRangeReset(pageNum)) {
    
    resetRenderRange(pageNum)
    currentPageNum.value = pageNum
    emit('page-change', pageNum)
    await nextTick()

    
    await waitForPageRendered(pageNum)

    
    highlightBoxes.value = newHighlightBoxes
    await nextTick()
    scrollToHighlightCenter(pageNum, bbox || null, false)
  } else {
    
    expandRenderRangeTo(pageNum)
    currentPageNum.value = pageNum
    emit('page-change', pageNum)
    await nextTick()

    
    await waitForPageRendered(pageNum)

    
    highlightBoxes.value = newHighlightBoxes
    await nextTick()
    scrollToHighlightCenter(pageNum, bbox || null, true)
  }
}


watch(() => props.fileId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadDocument()
  }
}, { immediate: true })


watch(() => props.pageInfo, () => {
  
}, { deep: true })


defineExpose({
  scrollToSegment,
  scrollToPageAndHighlightBbox,
  clearHighlights,
  clearSelectedBlock,
  goToPage,
  loadDocument,
  currentPageNum,
  totalPages,
  isDocumentLoaded
})
</script>

<style scoped>
.pdf-viewer {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}


.pdf-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary, #f5f5f5);
  color: var(--text-tertiary, #999);
  font-size: 13px;
}

.placeholder-hint {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
}


.pdf-page-section {
  margin-bottom: 24px;
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
  background: var(--border-color, #e0e0e0);
}

.page-divider-text {
  font-size: 12px;
  color: var(--text-tertiary, #999);
  white-space: nowrap;
}


.pdf-page-container {
  display: flex;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.pdf-page-wrapper {
  position: relative;
  display: inline-block;
  max-width: 100%;
}

.pdf-canvas {
  display: block;
  max-width: 100%;
  height: auto;
}


.pdf-highlight-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.pdf-highlight-box {
  position: absolute;
  border: 2px solid #8b5cf6;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 2px;
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.4);
  animation: highlight-pulse 1.5s ease-in-out infinite;
}

@keyframes highlight-pulse {
  0%, 100% {
    box-shadow: 0 0 8px rgba(139, 92, 246, 0.4);
  }
  50% {
    box-shadow: 0 0 16px rgba(139, 92, 246, 0.6);
  }
}


.pdf-selected-block-highlight {
  position: absolute;
  border: 2px solid #10b981;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 2px;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
  pointer-events: auto;
  cursor: default;
}


.pdf-page-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-tertiary, #999);
  font-size: 13px;
  pointer-events: none;
}
</style>
