import { computed, reactive, ref, type ComputedRef, type Ref } from 'vue'
import {
  cancelWorkflow,
  createWorkflow,
  deleteWorkflow,
  finalizeWorkflow,
  getProjectWorkflows,
  getWorkflowContent,
  getWorkflowDetail,
  getWorkflowStepConfig,
  getWorkflowsStatusBatch,
  regenerateWorkflowStep,
  renameWorkflow,
  type WorkflowCitation,
  type WorkflowContentFeature,
  type WorkflowDetail,
  type WorkflowListItem,
} from '@/services/api'
import { getModelOutputLanguage, translateText } from '@/i18n'
import {
  buildWorkflowPrompt,
  formatWorkflowElapsed as formatWorkflowElapsedText,
  formatWorkflowGeneratingMessage,
  formatWorkflowStepRegeneratedMessage,
  getWorkflowDisplayName,
  getWorkflowPresetPrompt,
  hasEditableWorkflowTitle,
  isWorkflowActiveStatus,
  WORKFLOW_PRESETS,
  type WorkflowPresetKey,
} from './workflowHelpers'

type ToastType = 'success' | 'error' | 'info' | 'warning'

interface ConfirmOptions {
  title: string
  message: string
  type?: 'info' | 'warning' | 'danger'
  confirmText?: string
  cancelText?: string
}

interface UseProjectWorkflowsOptions {
  projectId: string
  hasReadyFiles: ComputedRef<boolean>
  rightPanelWidth: Ref<number>
  rightPanelWidthBeforeReport: Ref<number | null>
  reportMinWidth: number
  showToast: (message: string, type?: ToastType, duration?: number) => void
  showConfirm: (options: ConfirmOptions) => Promise<boolean>
  openRenameModal: (type: 'workflow', id: string, name: string) => void
}

function uiText(text: string): string {
  return translateText(text)
}

export function useProjectWorkflows({
  projectId,
  hasReadyFiles,
  rightPanelWidth,
  rightPanelWidthBeforeReport,
  reportMinWidth,
  showToast,
  showConfirm,
  openRenameModal,
}: UseProjectWorkflowsOptions) {
  const workflowConfigModal = reactive({
    visible: false,
    presetKey: 'custom' as WorkflowPresetKey,
  })

  const activeWorkflowPreset = computed(() => WORKFLOW_PRESETS[workflowConfigModal.presetKey])
  const activeWorkflowPresetPrompt = computed(() => getWorkflowPresetPrompt(activeWorkflowPreset.value))

  const workflows = ref<WorkflowListItem[]>([])
  const currentWorkflow = ref<WorkflowDetail | null>(null)
  const workflowPollingTimer = ref<number | null>(null)
  const workflowElapsedTick = ref(Date.now())
  const workflowLoading = ref(false)
  const isLoadingWorkflows = ref(false)
  const workflowFeatures = ref<WorkflowContentFeature[]>([])
  const workflowCitations = ref<Record<string, WorkflowCitation>>({})
  const showWorkflowDetail = ref(false)
  const workflowMenuId = ref<string | null>(null)
  const activeWorkflowCitationNum = ref<number | null>(null)
  const activeWorkflowFeatureId = ref<string | null>(null)

  const featureConfigDialog = reactive({
    visible: false,
    title: '',
    message: '',
    confirmText: '重新生成',
    cancelText: '取消',
    stepIndex: null as number | null,
    prompt: '',
    selectedFileIds: [] as string[]
  })

  const finalizeConfirmVisible = ref(false)
  const workflowToFinalizeId = ref<string | null>(null)

  let pollErrorCount = 0
  const MAX_POLL_ERRORS = 5
  let workflowElapsedTimer: ReturnType<typeof setInterval> | null = null

  function toggleWorkflowMenu(workflowId: string, event: Event) {
    event.stopPropagation()
    workflowMenuId.value = workflowMenuId.value === workflowId ? null : workflowId
  }

  function handleRenameWorkflow(workflow: WorkflowListItem) {
    workflowMenuId.value = null
    if (!hasEditableWorkflowTitle(workflow)) return
    openRenameModal('workflow', workflow.id, getWorkflowDisplayName(workflow))
  }

  function closeWorkflowMenu() {
    workflowMenuId.value = null
  }

  function openWorkflowConfig(presetKey: WorkflowPresetKey = 'custom') {
    if (!hasReadyFiles.value) return
    workflowConfigModal.presetKey = presetKey
    workflowConfigModal.visible = true
  }

  function closeWorkflowConfig() {
    workflowConfigModal.visible = false
    workflowConfigModal.presetKey = 'custom'
  }

  async function handleWorkflowConfigConfirm(title: string, prompt: string, fileIds: string[]) {
    const preset = activeWorkflowPreset.value
    const finalPrompt = buildWorkflowPrompt(preset, prompt)
    closeWorkflowConfig()
    await handleOneclickWorkflow(title, finalPrompt, fileIds, preset.title, preset.key)
  }

  async function handleOneclickWorkflow(
    title: string,
    prompt: string,
    fileIds: string[],
    displayName: string,
    presetKey: WorkflowPresetKey,
  ) {
    if (fileIds.length === 0) return

    try {
      const resp = await createWorkflow(projectId, title, {
        prompt,
        file_ids: fileIds,
        preset_key: presetKey,
        output_language: getModelOutputLanguage(),
      })

      await loadWorkflows()

      if (resp?.workflow_id) {
        startWorkflowPolling(resp.workflow_id)
      }

      showToast(formatWorkflowGeneratingMessage(displayName), 'success')
    } catch (error) {
      console.error('创建工作流失败:', error)
      showToast(uiText('创建任务失败，请稍后重试'), 'error')
    }
  }

  function startWorkflowPolling(workflowId: string) {
    stopWorkflowPolling()

    pollWorkflowStatus(workflowId)

    workflowPollingTimer.value = window.setInterval(() => {
      pollWorkflowStatus(workflowId)
    }, 3000)
  }

  function stopWorkflowPolling() {
    if (workflowPollingTimer.value) {
      clearInterval(workflowPollingTimer.value)
      workflowPollingTimer.value = null
    }
  }

  function startWorkflowElapsedTimer() {
    if (workflowElapsedTimer) return

    workflowElapsedTimer = setInterval(() => {
      workflowElapsedTick.value = Date.now()
    }, 1000)
  }

  function stopWorkflowElapsedTimer() {
    if (workflowElapsedTimer) {
      clearInterval(workflowElapsedTimer)
      workflowElapsedTimer = null
    }
  }

  async function pollWorkflowStatus(workflowId: string) {
    try {
      const response = await getWorkflowsStatusBatch([workflowId])
      const status = response.workflows[workflowId]

      if (!status) {
        console.error('工作流状态未返回:', workflowId)
        pollErrorCount++
        if (pollErrorCount >= MAX_POLL_ERRORS) {
          stopWorkflowPolling()
          workflowLoading.value = false
          showToast(uiText('状态获取失败，请刷新页面'), 'error')
        }
        return
      }

      pollErrorCount = 0

      const shouldRefreshDetail = showWorkflowDetail.value &&
        currentWorkflow.value?.id === workflowId

      if (currentWorkflow.value?.id === workflowId) {
        currentWorkflow.value.status = status.status
      }

      if (isWorkflowActiveStatus(status.status)) {
        await loadWorkflows()
        if (shouldRefreshDetail) {
          await refreshWorkflowDetail(workflowId)
        }
        return
      }

      stopWorkflowPolling()
      workflowLoading.value = false

      await loadWorkflows()
      if (shouldRefreshDetail) {
        await refreshWorkflowDetail(workflowId)
      }

      if (status.status === 'completed') {
        showToast(uiText('生成完成'), 'success')
      } else if (status.status === 'partial') {
        showToast(uiText('部分内容生成完成'), 'info')
      } else if (status.status === 'failed') {
        showToast(uiText('生成失败，请重试'), 'error')
      } else if (status.status === 'cancelled') {
        showToast(uiText('已停止生成'), 'info')
      }
    } catch (error) {
      console.error('获取工作流状态失败:', error)
      pollErrorCount++
      if (pollErrorCount >= MAX_POLL_ERRORS) {
        stopWorkflowPolling()
        workflowLoading.value = false
        showToast(uiText('网络连接不稳定，请刷新页面重试'), 'error')
      }
    }
  }

  async function loadWorkflows() {
    try {
      const res = await getProjectWorkflows(projectId)
      workflows.value = res.workflows

      const inProgress = workflows.value.find(w => isWorkflowActiveStatus(w.status))
      if (inProgress && !workflowPollingTimer.value) {
        startWorkflowPolling(inProgress.id)
      }
    } catch (error) {
      console.error('加载报告列表失败:', error)
    }
  }

  async function viewWorkflowDetail(workflowId: string) {
    try {
      const [detail, content] = await Promise.all([
        getWorkflowDetail(workflowId),
        getWorkflowContent(workflowId)
      ])

      currentWorkflow.value = detail

      workflowFeatures.value = content.features
      workflowCitations.value = content.citations

      if (rightPanelWidth.value < reportMinWidth) {
        rightPanelWidthBeforeReport.value = rightPanelWidth.value
        rightPanelWidth.value = reportMinWidth
      }
      showWorkflowDetail.value = true
    } catch (error) {
      console.error('获取工作流详情失败:', error)
      showToast(uiText('获取详情失败'), 'error')
    }
  }

  async function refreshWorkflowDetail(workflowId: string) {
    const [detail, content] = await Promise.all([
      getWorkflowDetail(workflowId),
      getWorkflowContent(workflowId)
    ])

    currentWorkflow.value = detail
    workflowFeatures.value = content.features
    workflowCitations.value = content.citations
  }

  function openFeatureConfigDialog(stepIndex: number, dialogTitle: string, prompt: string, fileIds: string[]) {
    featureConfigDialog.title = dialogTitle
    featureConfigDialog.message = uiText('确定要重新生成该步骤吗？')
    featureConfigDialog.confirmText = uiText('重新生成')
    featureConfigDialog.cancelText = uiText('取消')
    featureConfigDialog.stepIndex = stepIndex
    featureConfigDialog.prompt = prompt
    featureConfigDialog.selectedFileIds = fileIds
    featureConfigDialog.visible = true
  }

  function closeFeatureConfigDialog() {
    featureConfigDialog.visible = false
    featureConfigDialog.title = ''
    featureConfigDialog.message = ''
    featureConfigDialog.stepIndex = null
    featureConfigDialog.prompt = ''
    featureConfigDialog.selectedFileIds = []
  }

  function resolveStepDisplayName(configStepName: string | undefined, fallbackDisplayName: string | undefined): string {
    if (fallbackDisplayName && fallbackDisplayName.trim()) return fallbackDisplayName
    if (configStepName && /[^\x00-\x7F]/.test(configStepName)) return configStepName
    return uiText('该步骤')
  }

  async function handleWorkflowStepRegenerate(stepIndex: number) {
    if (!currentWorkflow.value) return

    const workflowId = currentWorkflow.value.id
    const workflowTitle = getWorkflowDisplayName(currentWorkflow.value)
    const step = currentWorkflow.value.steps?.find(s => s.step_index === stepIndex)
    const fallbackStepName = step?.display_name

    try {
      const config = await getWorkflowStepConfig(workflowId, stepIndex)
      const stepName = resolveStepDisplayName(config.step_name, fallbackStepName)
      const dialogTitle = `${workflowTitle} - ${stepName}`
      const prompt = config.custom_config?.prompt || ''
      const fileIds = Array.isArray(config.custom_config?.file_ids) ? config.custom_config!.file_ids : []

      openFeatureConfigDialog(stepIndex, dialogTitle, prompt, fileIds)
    } catch (error: any) {
      const status = error?.response?.status
      if (status === 404) {
        showToast(uiText('该步骤不存在，无法重新生成'), 'error')
      } else {
        showToast(uiText('获取步骤配置失败，请稍后重试'), 'error')
      }

      const dialogTitle = `${workflowTitle} - ${resolveStepDisplayName(undefined, fallbackStepName)}`
      openFeatureConfigDialog(stepIndex, dialogTitle, '', [])
    }
  }

  async function handleFeatureConfigConfirm(prompt: string, fileIds: string[]) {
    if (!currentWorkflow.value || featureConfigDialog.stepIndex === null) return

    const workflowId = currentWorkflow.value.id
    const stepIndex = featureConfigDialog.stepIndex

    closeFeatureConfigDialog()

    try {
      const customConfig = {
        prompt: prompt || undefined,
        file_ids: fileIds && fileIds.length > 0 ? fileIds : undefined
      }
      const result = await regenerateWorkflowStep(workflowId, stepIndex, customConfig)
      showToast(formatWorkflowStepRegeneratedMessage(result.step_name), 'success')
      await loadWorkflows()
      await refreshWorkflowDetail(workflowId)
    } catch (error) {
      console.error('重新生成步骤失败:', error)
      showToast(uiText('重新生成失败，请稍后重试'), 'error')
    }
  }

  function closeWorkflowDetail() {
    showWorkflowDetail.value = false
    currentWorkflow.value = null
    workflowFeatures.value = []
    workflowCitations.value = {}
    activeWorkflowCitationNum.value = null
    activeWorkflowFeatureId.value = null
    if (rightPanelWidthBeforeReport.value !== null) {
      rightPanelWidth.value = rightPanelWidthBeforeReport.value
      rightPanelWidthBeforeReport.value = null
    }
  }

  function clearWorkflowCitation() {
    activeWorkflowCitationNum.value = null
    activeWorkflowFeatureId.value = null
  }

  async function handleDeleteWorkflow(workflowId: string) {
    const confirmed = await showConfirm({
      title: uiText('确认删除'),
      message: uiText('确定要删除这个生成记录吗？'),
      type: 'danger'
    })
    if (!confirmed) return

    try {
      await deleteWorkflow(workflowId)
      if (currentWorkflow.value?.id === workflowId) {
        currentWorkflow.value = null
      }
      await loadWorkflows()
      showToast(uiText('已删除'), 'success')
    } catch (error) {
      console.error('删除工作流失败:', error)
      showToast(uiText('删除失败'), 'error')
    }
  }

  async function handleCancelWorkflow(workflowId: string) {
    try {
      const status = await cancelWorkflow(workflowId)
      const workflow = workflows.value.find(w => w.id === workflowId)
      if (workflow) {
        workflow.status = status.status
        workflow.progress = status.progress
      }
      if (currentWorkflow.value?.id === workflowId) {
        currentWorkflow.value.status = status.status
        currentWorkflow.value.progress = status.progress
        await refreshWorkflowDetail(workflowId)
      }

      await loadWorkflows()
      if (isWorkflowActiveStatus(status.status)) {
        startWorkflowPolling(workflowId)
        showToast(uiText('正在停止生成'), 'info')
      } else {
        stopWorkflowPolling()
        showToast(uiText('已停止生成'), 'info')
      }
    } catch (error) {
      console.error('停止工作流失败:', error)
      showToast(uiText('停止生成失败，请稍后重试'), 'error')
    }
  }

  function handleFinalizeWorkflow(id: string) {
    workflowToFinalizeId.value = id
    finalizeConfirmVisible.value = true
  }

  async function executeFinalizeWorkflow() {
    if (!workflowToFinalizeId.value) return

    const id = workflowToFinalizeId.value
    try {
      const result = await finalizeWorkflow(id)
      if (result.success) {
        const workflow = workflows.value.find(w => w.id === id)
        if (workflow) {
          workflow.is_finalized = true
        }
        if (currentWorkflow.value?.id === id) {
          currentWorkflow.value.is_finalized = true
        }
        showToast(uiText('已成功定稿'), 'success')
        await loadWorkflows()
      }
    } catch (error) {
      console.error('Finalize failed:', error)
      showToast(uiText('定稿失败'), 'error')
    } finally {
      finalizeConfirmVisible.value = false
      workflowToFinalizeId.value = null
    }
  }

  async function renameWorkflowTitle(id: string, title: string) {
    await renameWorkflow(id, title)
    const workflow = workflows.value.find(w => w.id === id)
    if (workflow) {
      workflow.title = title
    }
    if (currentWorkflow.value?.id === id) {
      currentWorkflow.value.title = title
    }
  }

  async function handleWorkflowTitleUpdate(id: string, title: string) {
    try {
      await renameWorkflowTitle(id, title)
    } catch (error) {
      console.error('Failed to update workflow title:', error)
      showToast(uiText('重命名失败'), 'error')
    }
  }

  function handleWorkflowVisibilityChange() {
    workflowElapsedTick.value = Date.now()

    const processingWorkflow = workflows.value.find(wf => isWorkflowActiveStatus(wf.status))
    if (processingWorkflow && !workflowPollingTimer.value) {
      workflowLoading.value = true
    }
  }

  function formatWorkflowElapsed(isoString: string): string {
    return formatWorkflowElapsedText(isoString, workflowElapsedTick.value)
  }

  return {
    workflowConfigModal,
    activeWorkflowPreset,
    activeWorkflowPresetPrompt,
    workflows,
    currentWorkflow,
    workflowPollingTimer,
    workflowElapsedTick,
    workflowLoading,
    isLoadingWorkflows,
    workflowFeatures,
    workflowCitations,
    showWorkflowDetail,
    workflowMenuId,
    activeWorkflowCitationNum,
    activeWorkflowFeatureId,
    featureConfigDialog,
    finalizeConfirmVisible,
    workflowToFinalizeId,
    toggleWorkflowMenu,
    handleRenameWorkflow,
    closeWorkflowMenu,
    openWorkflowConfig,
    closeWorkflowConfig,
    handleWorkflowConfigConfirm,
    handleOneclickWorkflow,
    startWorkflowPolling,
    stopWorkflowPolling,
    startWorkflowElapsedTimer,
    stopWorkflowElapsedTimer,
    loadWorkflows,
    viewWorkflowDetail,
    refreshWorkflowDetail,
    openFeatureConfigDialog,
    closeFeatureConfigDialog,
    handleWorkflowStepRegenerate,
    handleFeatureConfigConfirm,
    closeWorkflowDetail,
    clearWorkflowCitation,
    handleDeleteWorkflow,
    handleCancelWorkflow,
    handleFinalizeWorkflow,
    executeFinalizeWorkflow,
    renameWorkflowTitle,
    handleWorkflowTitleUpdate,
    handleWorkflowVisibilityChange,
    formatWorkflowElapsed,
  }
}
