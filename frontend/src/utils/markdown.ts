

import { marked } from 'marked'
import katex from 'katex'
import { escapeHtml } from './format'


marked.setOptions({
  breaks: true,
  gfm: true
})

type ProtectedItem = {
  placeholder: string
  content: string
}

function protectItem(
  protectedItems: ProtectedItem[],
  content: string,
  prefix = 'HTML'
): string {
  const placeholder = `%%${prefix}_${protectedItems.length}%%`
  protectedItems.push({ placeholder, content })
  return placeholder
}

function renderLatex(latex: string, displayMode: boolean, fallback: string): string {
  try {
    return katex.renderToString(latex.trim(), { displayMode, throwOnError: false })
  } catch {
    return escapeHtml(fallback)
  }
}

function protectLatex(text: string, protectedItems: ProtectedItem[]): string {
  text = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, latex) => {
    return protectItem(
      protectedItems,
      renderLatex(latex, true, `$$${latex}$$`),
      'LATEX_BLOCK'
    )
  })

  return text.replace(/(^|[^\\$])\$([^\s\d$\n](?:[^$\n]*?[^\s$])?)\$(?!\$)/g, (_, prefix, latex) => {
    return prefix + protectItem(
      protectedItems,
      renderLatex(latex, false, `$${latex}$`),
      'LATEX_INLINE'
    )
  })
}

function restoreProtectedItems(html: string, protectedItems: ProtectedItem[]): string {
  for (const { placeholder, content } of protectedItems) {
    html = html.split(placeholder).join(content)
  }
  return html
}


export function renderMarkdownWithLatex(text: string): string {

  const protectedItems: ProtectedItem[] = []


  text = text.replace(/<span\s+class="inline-citation[^"]*"[^>]*>[\s\S]*?<\/span>/g, (match) => {
    return protectItem(protectedItems, match, 'CITATION')
  })

  text = protectLatex(text, protectedItems)

  let html = marked(text) as string

  return restoreProtectedItems(html, protectedItems)
}

export function renderLatexOnly(text: string): string {
  if (!text) return ''

  let html = escapeHtml(text)

  html = html.replace(/\$\$([^$]+)\$\$/g, (_, latex) => {
    try {
      return katex.renderToString(latex.trim(), { displayMode: true, throwOnError: false })
    } catch {
      return `$$${latex}$$`
    }
  })

  html = html.replace(/\$([^$\n]+)\$/g, (_, latex) => {
    try {
      return katex.renderToString(latex.trim(), { displayMode: false, throwOnError: false })
    } catch {
      return `$${latex}$`
    }
  })

  return html
}

export function renderSummary(summary: string): string {
  if (!summary) return ''
  return renderMarkdownWithLatex(summary)
}

export function parseInlineMarkdown(text: string): string {
  if (!text) return ''

  const protectedItems: ProtectedItem[] = []

  let processedText = text
    .replace(/\\n/g, '\n')

  processedText = protectLatex(processedText, protectedItems)

  processedText = processedText.replace(
    /\[citation_(\d+)\]/g,
    '<sup class="inline-citation">$1</sup>'
  )

  processedText = processedText.replace(
    /\[citation:[^\]]+\]/g,
    '<span class="inline-citation segment-citation disabled unresolved" data-citation-type="segment"></span>'
  )

  processedText = processedText.replace(
    /#([\u4e00-\u9fa5a-zA-Z0-9_]+)/g,
    '<span class="hashtag">#$1</span>'
  )

  let html = marked.parseInline(processedText) as string

  html = html.replace(/\n/g, '<br>')

  return restoreProtectedItems(html, protectedItems)
}
