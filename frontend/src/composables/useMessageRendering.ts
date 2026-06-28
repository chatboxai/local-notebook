import { computed, type Ref } from 'vue'
import { escapeHtml, renderMarkdownWithLatex } from '../utils'
import { ENABLE_THINK_PARSING, parseThinkingContent, renderThinkingBlock } from '../utils/think'
import { translateText } from '../i18n'
import type { ContentPart, Message } from '../types'

type RenderedSegmentType = 'thinking' | 'tool' | 'body'
export type RenderedSegment = { type: RenderedSegmentType; html: string }

interface ReasoningExpandState {
  shouldExpand: boolean
  isStreaming: boolean
}

export interface ParsedMessageContent {
  hasError: boolean
  hasPartial: boolean
  mainContent: string
  systemHint: string | null
}

interface UseMessageRenderingOptions {
  messages: Ref<Message[]>
  streamingParts: Ref<ContentPart[]>
}

export function useMessageRendering({
  messages,
  streamingParts,
}: UseMessageRenderingOptions) {
  const userExpandedThinkingBlocks = new Set<string>()

  function localizedThinkingLabel() {
    return escapeHtml(translateText('思考过程'))
  }

  function renderThinkingToggleContent(isExpanded: boolean) {
    const iconPath = isExpanded
      ? 'M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z'
      : 'M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z'

    return `<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="${iconPath}"/></svg><span>${localizedThinkingLabel()}</span>`
  }

  function handleThinkingToggleClick(target: HTMLElement): boolean {
    const thinkingToggle = target.closest('[data-thinking-toggle]') as HTMLElement | null
    if (!thinkingToggle) return false

    const thinkingBlock = thinkingToggle.closest('.thinking-block') as HTMLElement | null
    if (!thinkingBlock) return false

    const isExpanded = thinkingBlock.classList.contains('expanded')
    const blockId = thinkingBlock.dataset.thinkingId || ''

    if (isExpanded) {
      thinkingBlock.classList.remove('expanded')
      thinkingBlock.classList.add('collapsed')
      thinkingToggle.innerHTML = renderThinkingToggleContent(false)

      if (blockId) {
        userExpandedThinkingBlocks.delete(blockId)
      }
    } else {
      thinkingBlock.classList.remove('collapsed')
      thinkingBlock.classList.add('expanded')
      thinkingToggle.innerHTML = renderThinkingToggleContent(true)

      if (blockId) {
        userExpandedThinkingBlocks.add(blockId)
      }
    }

    return true
  }

  function processUnresolvedCitations(text: string): string {
    const unresolvedHtml = (displayNum: string) =>
      `<span class="inline-citation segment-citation disabled unresolved" data-citation-type="segment">${displayNum}</span>`

    let processed = text.replace(/\[citation:([^\]]+)\]/gi, (_match, value) => {
      const trimmed = String(value || '').trim()
      const displayNum = /^\d+$/.test(trimmed) ? trimmed : 'x'
      return unresolvedHtml(displayNum)
    })

    processed = processed.replace(/\bcitation_([a-z0-9]+)\b/gi, (_match, value) => {
      const trimmed = String(value || '').trim()
      const displayNum = /^\d+$/.test(trimmed) ? trimmed : 'x'
      return unresolvedHtml(displayNum)
    })

    return processed
  }

  function analyzeReasoningExpandStates(
    parts: ContentPart[],
    isStreamingMode: boolean,
    messageId: string
  ): Map<number, ReasoningExpandState> {
    const states = new Map<number, ReasoningExpandState>()
    if (!parts || parts.length === 0) return states

    let reasoningBlockIndex = 0

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      if (!part || part.type !== 'reasoning') continue

      const blockId = messageId ? `${messageId}_reasoning_${reasoningBlockIndex++}` : ''
      const userExpanded = blockId && userExpandedThinkingBlocks.has(blockId)

      let hasContentAfter = false
      for (let j = i + 1; j < parts.length; j++) {
        const nextPart = parts[j]
        if (!nextPart) continue

        if (nextPart.type === 'text') {
          const text = 'content' in nextPart && typeof (nextPart as any).content === 'string' ? (nextPart as any).content : ''
          const parsed = parseThinkingContent(text)
          if (parsed.content && parsed.content.trim() !== '') {
            hasContentAfter = true
            break
          }
        } else if (nextPart.type === 'citation_ref') {
          hasContentAfter = true
          break
        }
      }

      const autoExpand = isStreamingMode && !hasContentAfter
      const shouldExpand = userExpanded || autoExpand
      const isStreaming = isStreamingMode && !hasContentAfter

      states.set(i, {
        shouldExpand,
        isStreaming
      })
    }

    return states
  }

  function renderContentParts(parts: ContentPart[], isStreamingMode: boolean = false, messageId: string = ''): RenderedSegment[] {
    if (!parts || parts.length === 0) return []

    const segments: RenderedSegment[] = []
    let currentText = ''
    let thinkingBlockIndex = 0

    const reasoningExpandStates = analyzeReasoningExpandStates(parts, isStreamingMode, messageId)

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      if (!part) continue

      if (part.type === 'text') {
        const content = 'content' in part && typeof (part as any).content === 'string' ? (part as any).content : ''
        if (content.trim() === '') {
          if (content.includes('\n')) {
            continue
          }
          if (currentText && !currentText.endsWith(' ')) {
            currentText += ' '
          }
          continue
        }
        currentText += content
      } else if (part.type === 'reasoning') {
        if (currentText) {
          renderTextWithThinking(currentText, isStreamingMode)
          currentText = ''
        }

        const reasoningContent = 'content' in part && typeof (part as any).content === 'string' ? (part as any).content : ''
        if (reasoningContent) {
          const blockId = messageId ? `${messageId}_reasoning_${thinkingBlockIndex++}` : ''
          const expandState = reasoningExpandStates.get(i)
          const shouldExpand = expandState?.shouldExpand ?? isStreamingMode
          const isStreaming = expandState?.isStreaming ?? isStreamingMode

          segments.push({
            type: 'thinking',
            html: renderThinkingBlock(reasoningContent, shouldExpand, isStreaming, blockId, localizedThinkingLabel())
          })
        }
      } else if (part.type === 'citation_ref') {
        const partAny = part as any

        if (partAny.citation_type === 'web') {
          const title = partAny.title || ''
          const url = partAny.url || ''
          const snippet = partAny.snippet || ''
          const source = partAny.source || ''
          const publishedDate = partAny.published_date || ''
          const favicon = partAny.favicon || ''

          const iconHtml = favicon
            ? `<img class="web-favicon" src="${escapeHtml(favicon)}" width="12" height="12" onerror="this.style.display='none';this.nextElementSibling.style.display='inline'" /><svg class="web-icon" style="display:none" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>`
            : `<svg class="web-icon" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>`
          currentText += `<span class="inline-citation web-citation" data-citation-type="web" data-display-num="${partAny.display_num}" data-title="${escapeHtml(title)}" data-url="${escapeHtml(url)}" data-snippet="${escapeHtml(snippet)}" data-source="${escapeHtml(source)}" data-date="${escapeHtml(publishedDate)}" data-favicon="${escapeHtml(favicon)}">${partAny.display_num}${iconHtml}</span>`
        } else if (partAny.citation_type === 'image') {
          const fileId = partAny.file_id || ''
          const fileName = partAny.file_name || ''
          const imageName = partAny.image_name || ''
          const imageIndex = partAny.image_index ?? ''
          const page = partAny.page ?? ''
          currentText += `<span class="inline-citation image-citation" data-citation-type="image" data-display-num="${partAny.display_num}" data-file-id="${escapeHtml(fileId)}" data-file="${escapeHtml(fileName)}" data-image-name="${escapeHtml(imageName)}" data-image-index="${imageIndex}" data-page="${page}">${partAny.display_num}</span>`
        } else if (partAny.citation_type === 'audio') {
          const segmentId = partAny.segment_id || ''
          const disabledClass = segmentId ? '' : ' disabled'
          currentText += `<span class="inline-citation segment-citation${disabledClass}" data-citation-type="segment" data-display-num="${partAny.display_num}" data-file="${escapeHtml(partAny.file_name || '')}" data-segment-id="${escapeHtml(segmentId)}">${partAny.display_num}</span>`
        } else {
          const segmentId = partAny.segment_id || ''
          const disabledClass = segmentId ? '' : ' disabled'
          currentText += `<span class="inline-citation segment-citation${disabledClass}" data-citation-type="segment" data-display-num="${partAny.display_num}" data-file="${escapeHtml(partAny.file_name || '')}" data-segment-id="${escapeHtml(segmentId)}">${partAny.display_num}</span>`
        }
      } else if (part.type === 'tool_status') {
        if (currentText) {
          renderTextWithThinking(currentText, isStreamingMode)
          currentText = ''
        }

        segments.push({ type: 'tool', html: `<div class="tool-status-item">${escapeHtml(translateText(part.display))}</div>` })
      }
    }

    if (currentText) {
      renderTextWithThinking(currentText, isStreamingMode)
    }

    function renderTextWithThinking(text: string, isStreamingMode: boolean) {
      if (ENABLE_THINK_PARSING) {
        const { thinking, content, isThinkingComplete } = parseThinkingContent(text)

        if (thinking) {
          const blockId = messageId ? `${messageId}_think_${thinkingBlockIndex++}` : ''
          const userExpanded = blockId && userExpandedThinkingBlocks.has(blockId)
          const autoExpand = isStreamingMode && !content && !isThinkingComplete
          const shouldExpand = userExpanded || autoExpand

          segments.push({ type: 'thinking', html: renderThinkingBlock(thinking, shouldExpand, isStreamingMode && !isThinkingComplete, blockId, localizedThinkingLabel()) })
        }

        if (content) {
          segments.push({ type: 'body', html: renderMarkdownWithLatex(processUnresolvedCitations(content)) })
        }
      } else {
        segments.push({ type: 'body', html: renderMarkdownWithLatex(processUnresolvedCitations(text)) })
      }
    }

    return segments
  }

  function getMessageParts(msg: Message): ContentPart[] {
    const parts: ContentPart[] = []

    if (msg.reasoning_content && msg.reasoning_content.trim()) {
      parts.push({ type: 'reasoning', content: msg.reasoning_content })
    }

    if (msg.content_parts && msg.content_parts.length > 0) {
      parts.push(...msg.content_parts)
    } else if (msg.content) {
      parts.push({ type: 'text', content: msg.content })
    }

    const hasToolStatusInParts = parts.some(p => p.type === 'tool_status')

    if (!hasToolStatusInParts && msg.tool_executing && msg.tool_executing.length > 0) {
      for (const tool of msg.tool_executing) {
        parts.push({ type: 'tool_status', display: tool.display })
      }
    }

    return parts
  }

  function isToolOnlyMessage(msg: Message): boolean {
    const parts = getMessageParts(msg)
    if (!parts || parts.length === 0) return false

    let hasToolStatus = false
    for (const part of parts) {
      if (part.type === 'tool_status') {
        if (part.display && part.display.trim() !== '') {
          hasToolStatus = true
        }
        continue
      }
      if (part.type === 'text') {
        const text = part.content || ''
        if (text.trim() !== '') {
          const parsed = parseThinkingContent(text)
          if (parsed.content && parsed.content.trim() !== '') {
            return false
          }
        }
        continue
      }
      return false
    }

    return hasToolStatus
  }

  function parseMessageContent(msg: Message): ParsedMessageContent {
    const hasError = !!msg._error || (msg.content && msg.content.includes('[系统提示：'))

    if (!hasError) {
      return {
        hasError: false,
        hasPartial: false,
        mainContent: msg.content || '',
        systemHint: null
      }
    }

    const content = msg.content || ''
    const systemHintMatch = content.match(/\[系统提示：([^\]]+)\]/)

    if (systemHintMatch) {
      const systemHint = systemHintMatch?.[1] ?? null
      const mainContent = content.replace(/\[系统提示：[^\]]+\]/, '').trim()
      const hasPartial = !mainContent.startsWith('⚠️')

      return {
        hasError: true,
        hasPartial,
        mainContent,
        systemHint
      }
    }

    return {
      hasError: true,
      hasPartial: !!msg.has_partial,
      mainContent: content,
      systemHint: null
    }
  }

  function renderMessageWithError(msg: Message): RenderedSegment[] {
    const parsed = parseMessageContent(msg)

    if (!parsed.hasError) {
      return renderContentParts(getMessageParts(msg), false, msg.id)
    }

    const segments: RenderedSegment[] = []
    const appendBodyHtml = (html: string) => {
      if (!html) return
      const last = segments[segments.length - 1]
      if (last && last.type === 'body') {
        last.html += html
      } else {
        segments.push({ type: 'body', html })
      }
    }

    if (parsed.mainContent) {
      if (parsed.hasPartial) {
        const parts = getMessageParts(msg)
        segments.push(...renderContentParts(parts, false, msg.id))
      } else {
        appendBodyHtml(`<div class="error-placeholder">${escapeHtml(parsed.mainContent)}</div>`)
      }
    }

    if (parsed.systemHint) {
      const icon = parsed.hasPartial ? '⚠️' : '❌'
      appendBodyHtml(`
        <div class="system-hint ${parsed.hasPartial ? 'warning' : 'error'}">
          <span class="hint-icon">${icon}</span>
          <span class="hint-text">${escapeHtml(parsed.systemHint)}</span>
        </div>
      `)
    }

    return segments
  }

  const streamingRendered = computed(() => {
    return renderContentParts(streamingParts.value, true, 'streaming')
  })

  const renderedMessages = computed<Record<string, RenderedSegment[]>>(() => {
    const map: Record<string, RenderedSegment[]> = {}
    for (const msg of messages.value) {
      if (msg.role === 'assistant' && msg.id) {
        map[msg.id] = renderMessageWithError(msg)
      }
    }
    return map
  })

  const emptyRenderedMessage: RenderedSegment[] = []

  function getRenderedMessage(msg: Message): RenderedSegment[] {
    if (!msg.id) return emptyRenderedMessage
    return renderedMessages.value[msg.id] || emptyRenderedMessage
  }

  function getMessageTextContent(msg: Message): string {
    const parts = getMessageParts(msg)
    let text = ''

    for (const part of parts) {
      if (part.type === 'text') {
        text += part.content
      }
    }

    const parsed = parseThinkingContent(text)
    text = parsed.content
    text = text.replace(/\[\[?\d+\]?\]/g, '')
    text = text.replace(/  +/g, ' ').trim()

    return text
  }

  return {
    streamingRendered,
    getRenderedMessage,
    getMessageParts,
    getMessageTextContent,
    isToolOnlyMessage,
    parseMessageContent,
    handleThinkingToggleClick,
  }
}
