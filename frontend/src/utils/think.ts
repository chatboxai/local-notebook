

export const ENABLE_THINK_PARSING = true

export interface ThinkingParseResult {
  thinking: string | null
  content: string
  isThinkingComplete: boolean
}


export interface ThinkingParseResultMultiple {
  thinkings: string[]
  content: string
  isThinkingComplete: boolean
}


export function parseThinkingContent(text: string): ThinkingParseResult {
  const result = parseThinkingContentMultiple(text)
  return {
    thinking: result.thinkings.length > 0 ? result.thinkings.join('\n\n') : null,
    content: result.content,
    isThinkingComplete: result.isThinkingComplete
  }
}


export function parseThinkingContentMultiple(text: string): ThinkingParseResultMultiple {
  if (!ENABLE_THINK_PARSING || !text) {
    return {
      thinkings: [],
      content: text || '',
      isThinkingComplete: true
    }
  }

  const thinkings: string[] = []
  let content = text
  let isThinkingComplete = true


  const completeThinkRegex = /<think>([\s\S]*?)<\/think>/g
  let match
  while ((match = completeThinkRegex.exec(text)) !== null) {
    if (match[1]) {
      thinkings.push(match[1].trim())
    }
  }


  content = text.replace(/<think>[\s\S]*?<\/think>/g, '')


  const unclosedThinkMatch = content.match(/<think>([\s\S]*)$/)
  if (unclosedThinkMatch) {

    if (unclosedThinkMatch[1]) {
      thinkings.push(unclosedThinkMatch[1].trim())
    }
    content = content.replace(/<think>[\s\S]*$/, '')
    isThinkingComplete = false
  }

  return {
    thinkings,
    content: content.trim(),
    isThinkingComplete
  }
}


export function renderThinkingBlock(
  thinking: string,
  isExpanded: boolean,
  isStreaming: boolean = false,
  blockId: string = '',
  headerLabel: string = '思考过程'
): string {
  if (!thinking) return ''

  const expandedClass = isExpanded ? 'expanded' : 'collapsed'

  const icon = isExpanded
    ? '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>'
    : '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/></svg>'


  let processedThinking = thinking.replace(
    /<span class="inline-citation[^>]*>(\d+)<\/span>/g,
    '{{CITE:$1}}'
  )
  processedThinking = processedThinking.replace(
    /\[citation_(\d+)\]/g,
    (_match, num) => `{{CITE:${num}}}`
  )
  processedThinking = processedThinking.replace(
    /\[citation_(\d+)-citation_(\d+)\]/g,
    (_match, start, end) => {
      const s = parseInt(start), e = parseInt(end)
      return Array.from({ length: e - s + 1 }, (_, i) => `{{CITE:${s + i}}}`).join('')
    }
  )

  const citePlaceholders: string[] = []
  processedThinking = processedThinking.replace(
    /\{\{CITE:(\d+)\}\}/g,
    (_match, num) => {
      const placeholder = `__THINKING_CITE_${citePlaceholders.length}__`
      citePlaceholders.push(num)
      return placeholder
    }
  )

  processedThinking = processedThinking
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br>')

  processedThinking = processedThinking.replace(
    /__THINKING_CITE_(\d+)__/g,
    (_match, idx) => {
      const num = citePlaceholders[parseInt(idx)]
      return `<span class="thinking-citation">${num}</span>`
    }
  )

  const blockIdAttr = blockId ? ` data-thinking-id="${blockId}"` : ''

  return `<div class="thinking-block ${expandedClass}"${blockIdAttr} data-thinking-block>
    <div class="thinking-header" data-thinking-toggle>
      ${icon}
      <span>${headerLabel}</span>
      ${isStreaming ? '<span class="thinking-streaming-dot"></span>' : ''}
    </div>
    <div class="thinking-content">
      ${processedThinking}
    </div>
  </div>`
}
