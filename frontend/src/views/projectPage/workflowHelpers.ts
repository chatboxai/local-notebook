import { locale, translateText } from '../../i18n'
import type { WorkflowDetail, WorkflowListItem, WorkflowStatus } from '../../services/api'

export type WorkflowPresetKey = 'quick_read' | 'deep_dive' | 'custom'
export type WorkflowSourceClass = 'source-quick-read' | 'source-deep-dive' | 'source-custom'

interface WorkflowPreset {
  key: WorkflowPresetKey
  sourceClass: WorkflowSourceClass
  title: string
  description: string
  hint: string
  promptPlaceholder: string
  promptZh?: string
  promptEn?: string
}

export const WORKFLOW_PRESETS: Record<WorkflowPresetKey, WorkflowPreset> = {
  quick_read: {
    key: 'quick_read',
    sourceClass: 'source-quick-read',
    title: '内容速读',
    description: '快速掌握材料主线与重点',
    hint: '适合先快速了解资料讲了什么、重点在哪里、后续该追问什么。',
    promptPlaceholder: '可补充希望重点关注的人物、主题、章节或输出长度。',
    promptZh: [
      '请基于所选资料生成一份“内容速读”报告，目标是帮助读者在短时间内掌握材料主线。',
      '',
      '请优先覆盖：',
      '1. 材料主题与核心结论。',
      '2. 关键事实、人物/机构、时间线或核心概念。',
      '3. 最值得关注的亮点、异常、争议或空白。',
      '4. 可以继续追问或深入阅读的问题。',
      '',
      '要求：结构紧凑，表达清晰；只写资料支持的内容；所有事实性表述都要保留引用。'
    ].join('\n'),
    promptEn: [
      'Generate a "Quick Read" report from the selected sources. The goal is to help readers grasp the main thread quickly.',
      '',
      'Prioritize:',
      '1. The source theme and core conclusions.',
      '2. Key facts, people/organizations, timeline, or core concepts.',
      '3. The most important highlights, anomalies, disputes, or gaps.',
      '4. Questions worth asking next or areas worth reading more deeply.',
      '',
      'Requirements: keep the structure compact and clear; only include source-supported content; keep citations for all factual statements.'
    ].join('\n'),
  },
  deep_dive: {
    key: 'deep_dive',
    sourceClass: 'source-deep-dive',
    title: '核心详解',
    description: '系统拆解材料中的关键逻辑',
    hint: '适合深入理解资料里的问题、论据、关系、分歧和可执行结论。',
    promptPlaceholder: '可补充希望加深分析的方向、读者背景、输出风格或篇幅。',
    promptZh: [
      '请基于所选资料生成一份“核心详解”报告，目标是系统拆解材料中最重要的问题、论据和关系。',
      '',
      '请优先覆盖：',
      '1. 背景与问题定义。',
      '2. 关键论点及其证据链。',
      '3. 重要概念、机制、因果链或结构关系。',
      '4. 各方观点、分歧、不确定性和潜在反例。',
      '5. 结论、风险与可执行建议。',
      '',
      '要求：层次清楚，分析深入；避免泛泛总结；所有事实性表述都必须基于资料并保留引用。'
    ].join('\n'),
    promptEn: [
      'Generate a "Core Deep Dive" report from the selected sources. The goal is to systematically unpack the most important problems, arguments, and relationships in the material.',
      '',
      'Prioritize:',
      '1. Background and problem definition.',
      '2. Key arguments and their evidence chains.',
      '3. Important concepts, mechanisms, causal chains, or structural relationships.',
      '4. Different viewpoints, disagreements, uncertainties, and possible counterexamples.',
      '5. Conclusions, risks, and actionable recommendations.',
      '',
      'Requirements: keep the structure clear and the analysis deep; avoid generic summary; every factual statement must be grounded in the sources and keep citations.'
    ].join('\n'),
  },
  custom: {
    key: 'custom',
    sourceClass: 'source-custom',
    title: '自定义工作流',
    description: '完全按你的要求规划和生成',
    hint: 'AI 会把你的要求拆成多个环节，每个环节作为 workflow 中的一个 feature 生成。',
    promptPlaceholder: '例如：请基于这些资料生成一份面向投资人的尽调报告，重点分析商业模式、增长证据、竞争格局和风险。',
  },
}

function uiText(text: string): string {
  return translateText(text)
}

export function getWorkflowPresetPrompt(preset: WorkflowPreset): string {
  if (locale.value === 'en' && preset.promptEn) return preset.promptEn
  return preset.promptZh || ''
}

export function buildWorkflowPrompt(preset: WorkflowPreset, extraPrompt: string): string {
  const basePrompt = getWorkflowPresetPrompt(preset).trim()
  const extra = extraPrompt.trim()
  if (!basePrompt) return extra
  if (!extra) return basePrompt
  const extraLabel = locale.value === 'en' ? 'Additional user requirements:' : '用户补充要求：'
  return `${basePrompt}\n\n${extraLabel}\n${extra}`
}

export function formatWorkflowGeneratingMessage(displayName: string): string {
  return locale.value === 'en'
    ? `Generating ${uiText(displayName)}...`
    : `正在生成${displayName}...`
}

export function formatWorkflowStepRegeneratedMessage(stepName: string): string {
  return locale.value === 'en'
    ? `Regenerated: ${stepName}`
    : `已重新生成：${stepName}`
}

function getWorkflowRawDisplayName(workflow: WorkflowListItem | WorkflowDetail): string {
  return (workflow.title || workflow.display_name || '').trim()
}

export function isWorkflowPresetKey(value: string): value is WorkflowPresetKey {
  return value === 'quick_read' || value === 'deep_dive' || value === 'custom'
}

export function getWorkflowPresetKey(workflow: WorkflowListItem | WorkflowDetail): WorkflowPresetKey {
  const workflowType = (workflow.workflow_type || '').trim()
  if (workflowType === 'quick_read' || workflowType === 'deep_dive') return workflowType

  const rawName = getWorkflowRawDisplayName(workflow).toLowerCase()
  if (
    rawName.includes('quick read') ||
    rawName.includes('内容速读') ||
    rawName.includes('“quick read”') ||
    rawName.includes('"quick read"')
  ) {
    return 'quick_read'
  }
  if (
    rawName.includes('core deep dive') ||
    rawName.includes('核心详解') ||
    rawName.includes('“core deep dive”') ||
    rawName.includes('"core deep dive"')
  ) {
    return 'deep_dive'
  }
  if (isWorkflowPresetKey(workflowType)) return workflowType
  return 'custom'
}

function getWorkflowSourcePreset(workflow: WorkflowListItem | WorkflowDetail): WorkflowPreset {
  return WORKFLOW_PRESETS[getWorkflowPresetKey(workflow)]
}

export function getWorkflowDisplayName(workflow: WorkflowListItem | WorkflowDetail): string {
  const displayName = getWorkflowRawDisplayName(workflow)
  if (!displayName && isWorkflowActiveStatus(workflow.status)) {
    return uiText('正在生成标题...')
  }
  if (!displayName || isWorkflowPresetKey(displayName)) {
    return uiText(WORKFLOW_PRESETS[getWorkflowPresetKey(workflow)].title)
  }
  return displayName
}

export function getWorkflowSourceClass(workflow: WorkflowListItem | WorkflowDetail): WorkflowSourceClass {
  return getWorkflowSourcePreset(workflow).sourceClass
}

export function getWorkflowSourceLabel(workflow: WorkflowListItem | WorkflowDetail): string {
  return uiText(getWorkflowSourcePreset(workflow).title)
}

export function hasEditableWorkflowTitle(workflow: WorkflowListItem | WorkflowDetail): boolean {
  const title = (workflow.title || '').trim()
  return Boolean(title && title !== 'custom')
}

export function getWorkflowStatusText(status: WorkflowStatus): string {
  const map: Record<WorkflowStatus, string> = {
    pending: '等待中',
    processing: '生成中',
    cancelling: '取消中',
    completed: '已完成',
    failed: '失败',
    partial: '部分完成',
    cancelled: '已取消'
  }
  return uiText(map[status] || status)
}

export function isWorkflowActiveStatus(status: WorkflowStatus): boolean {
  return status === 'pending' || status === 'processing' || status === 'cancelling'
}

export function isWorkflowCancellable(status: WorkflowStatus): boolean {
  return status === 'pending' || status === 'processing' || status === 'cancelling'
}

function isWorkflowPlanning(workflow: WorkflowListItem | WorkflowDetail): boolean {
  return workflow.status === 'processing' && (workflow.progress?.total ?? 0) === 0
}

export function getWorkflowDisplayStatusText(workflow: WorkflowListItem | WorkflowDetail): string {
  if (isWorkflowPlanning(workflow)) return uiText('规划中')
  return getWorkflowStatusText(workflow.status)
}

export function getWorkflowStatusClass(status: WorkflowStatus): string {
  const map: Record<WorkflowStatus, string> = {
    pending: 'status-pending',
    processing: 'status-processing',
    cancelling: 'status-cancelling',
    completed: 'status-completed',
    failed: 'status-failed',
    partial: 'status-partial',
    cancelled: 'status-cancelled'
  }
  return map[status] || ''
}

export function formatWorkflowProgress(workflow: WorkflowListItem | WorkflowDetail): string {
  const completed = workflow.progress?.completed ?? 0
  const total = workflow.progress?.total ?? 0
  const completedLabel = total > 0 || completed > 0 ? String(completed) : '...'
  const totalLabel = total > 0 ? String(total) : '...'
  return `${completedLabel}/${totalLabel}`
}

export function formatWorkflowElapsed(isoString: string, nowMs: number): string {
  const startedAt = new Date(isoString)
  const elapsedMs = Math.max(0, nowMs - startedAt.getTime())
  const elapsedSeconds = Math.floor(elapsedMs / 1000)
  const hours = Math.floor(elapsedSeconds / 3600)
  const minutes = Math.floor((elapsedSeconds % 3600) / 60)
  const seconds = elapsedSeconds % 60

  if (locale.value === 'en') {
    if (hours > 0) return `${hours}h ${minutes}m`
    if (minutes > 0) return `${minutes}m ${seconds}s`
    return `${seconds}s`
  }

  if (hours > 0) return `${hours}小时${minutes}分钟`
  if (minutes > 0) return `${minutes}分钟${seconds}秒`
  return `${seconds}秒`
}
