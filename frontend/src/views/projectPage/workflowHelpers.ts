import { locale, t } from '../../i18n'
import type { WorkflowDetail, WorkflowListItem, WorkflowStatus } from '../../services/api'

export type WorkflowPresetKey = 'quick_read' | 'deep_dive' | 'custom'
export type WorkflowSourceClass = 'source-quick-read' | 'source-deep-dive' | 'source-custom'

interface WorkflowPreset {
  key: WorkflowPresetKey
  sourceClass: WorkflowSourceClass
  titleKey: string
  descriptionKey: string
  hintKey: string
  promptPlaceholderKey: string
  promptKey?: string
}

export const WORKFLOW_PRESETS: Record<WorkflowPresetKey, WorkflowPreset> = {
  quick_read: {
    key: 'quick_read',
    sourceClass: 'source-quick-read',
    titleKey: 'ui.quickRead',
    descriptionKey: 'ui.quicklyGraspTheMainThreadAndKeyPoints',
    hintKey: 'ui.bestForQuicklyUnderstandingWhatTheSourcesSay',
    promptPlaceholderKey: 'ui.optionallyAddPeopleThemesSectionsOrLengthRequirements',
    promptKey: 'workflowPrompts.quickRead',
  },
  deep_dive: {
    key: 'deep_dive',
    sourceClass: 'source-deep-dive',
    titleKey: 'ui.coreDeepDive',
    descriptionKey: 'ui.systematicallyUnpackTheKeyLogicInTheMaterial',
    hintKey: 'ui.bestForDeeplyUnderstandingTheProblemsArgumentsRelationships',
    promptPlaceholderKey: 'ui.optionallyAddAnalysisDirectionsAudienceBackgroundOutputStyle',
    promptKey: 'workflowPrompts.deepDive',
  },
  custom: {
    key: 'custom',
    sourceClass: 'source-custom',
    titleKey: 'ui.customWorkflow',
    descriptionKey: 'ui.planAndGenerateFullyFromYourInstructions',
    hintKey: 'ui.aiWillSplitYourInstructionsIntoMultipleStages',
    promptPlaceholderKey: 'ui.exampleBasedOnTheseMaterialsGenerateAnInvestor',
  },
}

export function getWorkflowPresetPrompt(preset: WorkflowPreset): string {
  return preset.promptKey ? t(preset.promptKey) : ''
}

export function buildWorkflowPrompt(preset: WorkflowPreset, extraPrompt: string): string {
  const basePrompt = getWorkflowPresetPrompt(preset).trim()
  const extra = extraPrompt.trim()
  if (!basePrompt) return extra
  if (!extra) return basePrompt
  const extraLabel = t('ui.additionalUserRequirementsLabel')
  return `${basePrompt}\n\n${extraLabel}\n${extra}`
}

export function formatWorkflowGeneratingMessage(displayName: string): string {
  return t('ui.generatingWorkflow', { name: displayName })
}

export function formatWorkflowStepRegeneratedMessage(stepName: string): string {
  return t('ui.workflowStepRegenerated', { name: stepName })
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
    rawName.includes('“quick read”') ||
    rawName.includes('"quick read"')
  ) {
    return 'quick_read'
  }
  if (
    rawName.includes('core deep dive') ||
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
    return t('ui.generatingTitle2')
  }
  if (!displayName || isWorkflowPresetKey(displayName)) {
    return t(WORKFLOW_PRESETS[getWorkflowPresetKey(workflow)].titleKey)
  }
  return displayName
}

export function getWorkflowSourceClass(workflow: WorkflowListItem | WorkflowDetail): WorkflowSourceClass {
  return getWorkflowSourcePreset(workflow).sourceClass
}

export function getWorkflowSourceLabel(workflow: WorkflowListItem | WorkflowDetail): string {
  return t(getWorkflowSourcePreset(workflow).titleKey)
}

export function hasEditableWorkflowTitle(workflow: WorkflowListItem | WorkflowDetail): boolean {
  const title = (workflow.title || '').trim()
  return Boolean(title && title !== 'custom')
}

export function getWorkflowStatusText(status: WorkflowStatus): string {
  const map: Record<WorkflowStatus, string> = {
    pending: t('ui.waiting'),
    processing: t('ui.generating2'),
    cancelling: t('ui.cancelling'),
    completed: t('ui.completed'),
    failed: t('ui.failed'),
    partial: t('ui.partiallyCompleted'),
    cancelled: t('ui.cancelled')
  }
  return map[status] || status
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
  if (isWorkflowPlanning(workflow)) return t('ui.planning')
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

  if (hours > 0) return t('ui.elapsedHoursMinutes', { hours, minutes })
  if (minutes > 0) return t('ui.elapsedMinutesSeconds', { minutes, seconds })
  return t('ui.elapsedSeconds', { seconds })
}
