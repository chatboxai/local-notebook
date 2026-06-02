
import DiffMatchPatch from 'diff-match-patch'

export interface DiffPart {
  type: 'keep' | 'delete' | 'insert'
  text: string
}


export function computeDiff(oldText: string, newText: string): DiffPart[] {
  const dmp = new DiffMatchPatch()
  const diffs = dmp.diff_main(oldText, newText)
  dmp.diff_cleanupSemantic(diffs)

  return diffs.map(([op, text]) => ({
    type: op === -1 ? 'delete' : op === 1 ? 'insert' : 'keep',
    text
  }))
}


export function extractTextFromContentParts(contentParts: Array<{ type: string; content?: string }>): string {
  if (!contentParts) return ''
  return contentParts
    .filter(part => part.type === 'text')
    .map(part => part.content || '')
    .join('')
}
