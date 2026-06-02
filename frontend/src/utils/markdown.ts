

import { marked } from 'marked'
import katex from 'katex'
import { escapeHtml } from './format'


marked.setOptions({
  breaks: true,
  gfm: true
})


export function renderMarkdownWithLatex(text: string): string {

  const protectedItems: { placeholder: string; content: string }[] = []
  let placeholderIndex = 0


  text = text.replace(/<span\s+class="inline-citation[^"]*"[^>]*>[\s\S]*?<\/span>/g, (match) => {
    const placeholder = `%%CITATION_${placeholderIndex++}%%`
    protectedItems.push({ placeholder, content: match })
    return placeholder
  })

  text = text.replace(/\$\$([^$]+)\$\$/g, (_, latex) => {
    const placeholder = `%%LATEX_BLOCK_${placeholderIndex++}%%`
    try {
      const rendered = katex.renderToString(latex.trim(), { displayMode: true, throwOnError: false })
      protectedItems.push({ placeholder, content: rendered })
    } catch {
      protectedItems.push({ placeholder, content: `$$${latex}$$` })
    }
    return placeholder
  })

  text = text.replace(/\$([^$\n]+)\$/g, (_, latex) => {
    const placeholder = `%%LATEX_INLINE_${placeholderIndex++}%%`
    try {
      const rendered = katex.renderToString(latex.trim(), { displayMode: false, throwOnError: false })
      protectedItems.push({ placeholder, content: rendered })
    } catch {
      protectedItems.push({ placeholder, content: `$${latex}$` })
    }
    return placeholder
  })

  let html = marked(text) as string

  for (const { placeholder, content } of protectedItems) {
    html = html.replace(placeholder, content)
  }

  return html
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

  let processedText = text
    .replace(/\\n/g, '\n')

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

  return html
}
