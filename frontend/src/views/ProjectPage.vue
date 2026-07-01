<template>
  <div class="project-page" :class="{ resizing: isResizing }" @click="closeWorkflowMenu">

    <header class="project-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack" :title="$t('ui.backToHome')">
          <img src="/logo/logo.png" alt="Local Notebook" class="back-logo" />
        </button>
        <div class="project-title-wrapper">
          <input
            v-if="isEditingTitle"
            ref="titleInputRef"
            v-model="editingTitleValue"
            class="project-title-input"
            :style="{ width: titleInputWidth }"
            @blur="handleTitleBlur"
            @keydown.enter="handleTitleEnter"
            @keydown.escape="cancelTitleEdit"
            @compositionstart="isTitleComposing = true"
            @compositionend="isTitleComposing = false"
            @input="updateTitleInputWidth"
          />
          <h1
            v-else
            class="project-title"
            @click="startTitleEdit"
            :title="$t('ui.clickToEditProjectName')"
          >{{ project?.name || 'Untitled' }}</h1>
        </div>
      </div>
      <div class="header-right">
        <LanguageSwitcher />
        <button v-if="canAdmin" class="btn-settings" @click="router.push('/admin')" :title="$t('ui.userManagement')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zM8 11c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5C15 14.17 10.33 13 8 13zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
          </svg>
        </button>
        <button v-if="canAdmin" class="btn-settings" @click="router.push('/settings')" :title="$t('ui.settings')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87a.49.49 0 0 0 .12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32a.49.49 0 0 0-.12-.61l-2.01-1.58zM12 15.6a3.6 3.6 0 1 1 0-7.2 3.6 3.6 0 0 1 0 7.2z"/>
          </svg>
        </button>
        <span class="user-badge">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
          <span>{{ displayUsername }}</span>
        </span>
        <button class="btn-settings" @click="logout" :title="$t('ui.logOut')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M10.09 15.59 11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3h-8v2h8v14h-8v2h8c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z" />
          </svg>
        </button>
      </div>
    </header>


    <div class="project-main">

      <div class="project-body">

        <SourcePanel
          ref="sourcePanelRef"
          :collapsed="leftPanelCollapsed"
          :width="leftPanelWidth"
          :show-preview="showSourcePreview"
          :files="files"
          :sorted-files="sortedFiles"
          :ready-files="readyFiles"
          :selected-file-ids="selectedFileIds"
          :uploading-files="uploadingFiles"
          :hovering-file-id="hoveringFileId"
          :open-menu-file-id="openMenuFileId"
          :is-all-selected="isAllSelected"
          :previewing-file="previewingFile"
          :previewing-file-name="previewingFileName"
          :previewing-file-content="previewingFileContent"
          :preview-summary="previewSummary"
          :summary-expanded="summaryExpanded"
          :is-previewing-image="isPreviewingImage"
          :is-previewing-audio="isPreviewingAudio"
          :is-pdf-file="isPdfFile"
          :supports-raw-view="supportsRawView"
          :view-mode="viewMode"
          :is-raw-view-mode="isRawViewMode"
          :is-loading-content="isLoadingContent"
          :pdf-page-info="pdfPageInfo"
          :visible-parsed-pages="visibleParsedPages"
          :parsed-blocks-by-page="parsedBlocksByPage"
          :highlight-block-ids="highlightBlockIds"
          :audio-preview-url="audioPreviewUrl"
          :audio-transcript-groups="audioTranscriptGroups"
          :audio-speaker-count="audioSpeakerCount"
          :active-audio-block-id="activeAudioBlockId"
          :current-total-pages="currentTotalPages"
          :current-page-num="currentPageNum"
          :jump-to-page-input="jumpToPageInput"
          @toggle-collapse="leftPanelCollapsed = !leftPanelCollapsed"
          @trigger-file-upload="triggerFileUpload"
          @toggle-select-all="toggleSelectAll"
          @open-file-preview="openFilePreview"
          @set-hovering-file="hoveringFileId = $event"
          @toggle-file-menu="toggleFileMenu"
          @rename-file="(fileId, fileName) => openRenameModal('file', fileId, fileName)"
          @delete-file="handleDeleteFile"
          @toggle-file-selection="toggleFileSelection"
          @close-preview="closePreview"
          @update:summary-expanded="summaryExpanded = $event"
          @switch-view-mode="switchViewMode"
          @keyword-click="handleKeywordClick"
          @preview-scroll="handlePreviewScroll"
          @page-change="handlePdfPageChange"
          @pdf-block-click="handlePdfBlockClick"
          @pdf-clear-selection="handlePdfClearSelection"
          @pdf-loading="handlePdfLoading"
          @audio-time-update="handleAudioTimeUpdate"
          @audio-play="handleAudioPlay"
          @seek-audio-to-block="seekAudioToBlock"
          @update:jump-to-page-input="jumpToPageInput = $event"
          @jump-to-page="jumpToPage"
        />

        <div
          class="resizer left-resizer"
          :class="{ hidden: leftPanelCollapsed }"
          @mousedown="startResizeLeft"
        >
          <div class="resizer-line"></div>
        </div>

        <CollapsedSourceRail
          v-if="leftPanelCollapsed"
          :file-count="files.length"
          @expand="leftPanelCollapsed = false"
          @trigger-file-upload="triggerFileUpload"
        />

      <ChatPanel
        ref="chatPanelRef"
        :title="displaySessionTitle"
        :is-editing-title="isEditingSessionTitle"
        :editing-title-value="editingSessionTitleValue"
        :is-streaming="isStreaming"
        :is-title-locked="isCurrentSessionTitleGenerating"
        :messages="messages"
        :has-ready-files="hasReadyFiles"
        :localized-greeting="localizedGreeting"
        :is-loading-more-messages="isLoadingMoreMessages"
        :has-more-messages="hasMoreMessages"
        :is-messages-scrollable="isMessagesScrollable"
        :is-export-selection-mode="isExportSelectionMode"
        :selected-user-message-ids="selectedUserMessageIds"
        :is-exporting-messages="isExportingMessages"
        :editing-message-id="editingMessageId"
        :editing-content="editingContent"
        :streaming-parts-count="streamingParts.length"
        :streaming-rendered="streamingRendered"
        :is-thinking="isThinking"
        :show-scroll-to-bottom="showScrollToBottom"
        :scroll-btn-bottom="scrollBtnBottom"
        :input-message="inputMessage"
        :web-search-configured="webSearchConfigured"
        :source-count="readyFiles.length"
        :has-current-session="Boolean(currentSession)"
        :copy-toast-visible="copyToastVisible"
        :copy-toast-message="copyToastMessage"
        :is-tool-only-message="isToolOnlyMessage"
        :is-message-in-selected-conversation="isMessageInSelectedConversation"
        :is-pre-compact-message="isPreCompactMessage"
        :parse-message-content="parseMessageContent"
        :get-rendered-message="getRenderedMessage"
        :should-show-message-actions="shouldShowMessageActions"
        :is-last-assistant-message="isLastAssistantMessage"
        :format-message-time="formatMessageTime"
        @update:editing-title-value="editingSessionTitleValue = $event"
        @start-title-edit="startSessionTitleEdit"
        @save-title-edit="saveSessionTitle"
        @cancel-title-edit="cancelSessionTitleEdit"
        @create-session="handleCreateNewSession"
        @open-history="showSessionHistory = true"
        @messages-scroll="handleMessagesScroll"
        @web-citation-hover="handleWebCitationHover"
        @web-citation-leave="handleWebCitationLeave"
        @chat-area-click="handleChatAreaClick"
        @trigger-upload="triggerFileUpload"
        @toggle-conversation-selection="toggleConversationSelection"
        @update:editing-content="editingContent = $event"
        @submit-edit-message="submitEditMessage"
        @cancel-edit-message="cancelEditMessage"
        @auto-resize-edit-textarea="autoResizeEditTextarea"
        @start-edit-message="startEditMessage"
        @copy-user-message="copyUserMessage"
        @copy-message-as-text="copyMessageAsText"
        @copy-message-as-markdown="copyMessageAsMarkdown"
        @regenerate-message="regenerateMessage"
        @enter-export-mode-with-selection="enterExportModeWithSelection"
        @force-scroll-to-bottom="forceScrollToBottom"
        @toggle-select-all-user-messages="toggleSelectAllUserMessages"
        @toggle-export-selection-mode="toggleExportSelectionMode"
        @export-selected-messages="handleExportSelectedMessages"
        @update:input-message="inputMessage = $event"
        @send-enter="handleSendEnter"
        @composition-start="isComposing = true"
        @composition-end="isComposing = false"
        @auto-resize-textarea="autoResizeTextarea"
        @send-message="sendMessage"
        @stop-streaming="stopStreaming"
      />


      <div
        class="resizer right-resizer"
        :class="{ hidden: rightPanelCollapsed }"
        @mousedown="startResizeRight"
      >
        <div class="resizer-line"></div>
      </div>

      <ProjectRightPanel
        v-model:right-panel-collapsed="rightPanelCollapsed"
        v-model:toolbox-mode="toolboxMode"
        :right-panel-width="rightPanelWidth"
        :show-feature-detail="showFeatureDetail"
        :show-workflow-detail="showWorkflowDetail"
        :current-workflow="currentWorkflow"
        :workflow-features="workflowFeatures"
        :active-workflow-citation-num="activeWorkflowCitationNum"
        :active-workflow-feature-id="activeWorkflowFeatureId"
        :active-feature="activeFeature"
        :active-feature-citation-num="activeFeatureCitationNum"
        :transition-name="transitionName"
        :has-ready-files="hasReadyFiles"
        :features="features"
        :workflows="workflows"
        :highlighted-feature-id="highlightedFeatureId"
        :highlighted-workflow-id="highlightedWorkflowId"
        :format-time="formatTime"
        :format-workflow-elapsed="formatWorkflowElapsed"
        @close-workflow-detail="closeWorkflowDetail"
        @cancel-workflow="handleCancelWorkflow"
        @delete-workflow="handleDeleteWorkflow"
        @workflow-title-update="handleWorkflowTitleUpdate"
        @workflow-citation-click="handleWorkflowCitationClick"
        @clear-workflow-citation="clearWorkflowCitation"
        @workflow-step-regenerate="handleWorkflowStepRegenerate"
        @show-toast="showToast"
        @close-feature-detail="closeFeatureDetail"
        @feature-citation-click="handleFeatureCitationClick"
        @clear-feature-citation="clearFeatureCitation"
        @feature-rename="handleFeatureDetailRename"
        @open-tool-config="openToolConfig"
        @view-feature-detail="handleFeatureClick"
        @delete-feature="handleDeleteFeature"
        @open-workflow-config="openWorkflowConfig"
        @view-workflow-detail="viewWorkflowDetail"
      />
      </div>


      <footer class="project-footer">
        {{ $t('ui.xiaoluoMayMakeMistakesSoPleaseVerifyImportant') }}
      </footer>
    </div>


    <ConfirmDialog
      v-model:visible="confirmDialog.visible"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      :type="confirmDialog.type"
      :confirm-text="confirmDialog.confirmText"
      :cancel-text="confirmDialog.cancelText"
      @confirm="confirmDialog.onConfirm"
      @cancel="confirmDialog.onCancel"
    />


    <FeatureConfigModal
      v-model:visible="featureConfigDialog.visible"
      :title="featureConfigDialog.title"
      :message="featureConfigDialog.message"
      :files="files"
      :selected-file-ids="featureConfigDialog.selectedFileIds"
      :initial-prompt="featureConfigDialog.prompt"
      :confirm-text="featureConfigDialog.confirmText"
      :cancel-text="featureConfigDialog.cancelText"
      @confirm="handleFeatureConfigConfirm"
      @cancel="closeFeatureConfigDialog"
    />


    <UploadSourceModal
      :visible="showUploadModal"
      :current-file-count="files.length"
      :max-file-count="sourceMaxFileCount"
      :is-uploading="isUploading"
      @close="showUploadModal = false"
      @upload-files="handleUploadFiles"
      @insert-text="handleInsertText"
    />

    <ToolConfigModal
      :visible="toolConfigModal.visible"
      :tool-type="toolConfigModal.toolType"
      :tool-title="toolConfigModal.toolTitle"
      :description="toolConfigModal.description"
      :hint="toolConfigModal.hint"
      :builtin-prompt="toolConfigModal.builtinPrompt"
      :prompt-placeholder="toolConfigModal.promptPlaceholder"
      :hide-prompt="toolConfigModal.hidePrompt"
      :files="files"
      :selected-file-ids="selectedFileIds"
      @close="closeToolConfig"
      @confirm="handleToolConfigConfirm"
    />


    <WorkflowConfigModal
      :visible="workflowConfigModal.visible"
      :modal-title="t(activeWorkflowPreset.titleKey)"
      :description="t(activeWorkflowPreset.descriptionKey)"
      :hint="t(activeWorkflowPreset.hintKey)"
      :builtin-prompt="activeWorkflowPresetPrompt"
      :prompt-placeholder="t(activeWorkflowPreset.promptPlaceholderKey)"
      :preset-key="workflowConfigModal.presetKey"
      :files="files"
      :selected-file-ids="selectedFileIds"
      @close="closeWorkflowConfig"
      @confirm="handleWorkflowConfigConfirm"
    />


    <ImageGenerationModal
      :visible="imageGenerationModal.visible"
      :mode="imageGenerationModal.mode"
      :files="imageFilesForGeneration"
      @close="closeImageGenerationModal"
      @confirm="handleImageGenerationConfirm"
    />


    <VideoGenerationModal
      :visible="videoGenerationModal.visible"
      :mode="videoGenerationModal.mode"
      :files="videoFilesForGeneration"
      @close="closeVideoGenerationModal"
      @confirm="handleVideoGenerationConfirm"
    />


    <RenameModal
      v-model:visible="renameModal.visible"
      :title="renameModal.type === 'file' ? t('ui.renameFile') : t('ui.rename')"
      :placeholder="renameModal.type === 'file' ? t('ui.enterANewFileName') : t('ui.editTitlePlaceholder')"
      :initial-value="renameModal.name"
      :saving="renameModal.saving"
      @confirm="handleRenameConfirm"
    />


    <ConfirmDialog
      v-model:visible="finalizeConfirmVisible"
      type="warning"
      :title="t('ui.confirmFinalization')"
      :message="t('ui.markThisWorkflowAsFinalAfterFinalizationThe')"
      :confirm-text="t('ui.confirmFinalization')"
      :cancel-text="t('ui.cancel')"
      @confirm="executeFinalizeWorkflow"
    />


    <WebCitationTooltip
      :visible="webCitationTooltip.visible"
      :x="webCitationTooltip.x"
      :y="webCitationTooltip.y"
      :title="webCitationTooltip.title"
      :url="webCitationTooltip.url"
      :snippet="webCitationTooltip.snippet"
      :source="webCitationTooltip.source"
      :date="webCitationTooltip.date"
      :favicon="webCitationTooltip.favicon"
      @close="webCitationTooltip.visible = false"
    />


    <SessionHistoryPanel
      :visible="showSessionHistory"
      :sessions="sessions"
      :current-session-id="currentSession?.id || null"
      @close="showSessionHistory = false"
      @select="handleSwitchSession"
      @delete="handleDeleteSession"
    />


    <SourceBlockCopyPanel
      :visible="copyPanelVisible"
      :block="selectedPdfBlock"
      :position="copyPanelPosition"
      @copy="copySelectedBlockText"
      @close="clearSelectedBlock"
    />


    <Toast :visible="toastVisible" :message="toastMessage" :type="toastType" />

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import 'katex/dist/katex.min.css'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import FeatureConfigModal from '../components/common/FeatureConfigModal.vue'
import UploadSourceModal from '../components/common/UploadSourceModal.vue'
import ToolConfigModal from '../components/common/ToolConfigModal.vue'
import WorkflowConfigModal from '../components/common/WorkflowConfigModal.vue'
import ImageGenerationModal from '../components/common/ImageGenerationModal.vue'
import VideoGenerationModal from '../components/common/VideoGenerationModal.vue'
import ProjectRightPanel from '../components/project/ProjectRightPanel.vue'
import ChatPanel from '../components/project/chat/ChatPanel.vue'
import CollapsedSourceRail from '../components/project/source/CollapsedSourceRail.vue'
import SourceBlockCopyPanel from '../components/project/source/SourceBlockCopyPanel.vue'
import SourcePanel from '../components/project/source/SourcePanel.vue'
import SessionHistoryPanel from '../components/SessionHistoryPanel.vue'
import LanguageSwitcher from '../components/common/LanguageSwitcher.vue'
import { useChatScroll } from '../composables/useChatScroll'
import { useMessageRendering } from '../composables/useMessageRendering'
import { usePanelResize } from '../composables/usePanelResize'
import { useMessageExportSelection } from '../composables/useMessageExportSelection'
import { clearTokens, getDisplayUsername, isAdmin } from '../services/auth'
import {
  getProject,
  getSessions,
  createSession,
  getSession,
  deleteSession,
  updateSessionTitle,
  generateSessionTitle,
  checkPreflight,
  chatStream,
  editMessageAndRegenerate,
  type AgentRole,
  type CitationRef,
  type FeatureStartedData,
  type WorkflowStartedData,
  updateProject,
  type WorkflowContentFeature,
} from '../services/api'
import type { Project, Session, Message, ContentPart, ToolExecuting, ToolStatusPart, ToolSummaryActivityPart, ToolSummaryPart, FeatureCitationRefPart } from '../types'
import RenameModal from '../components/common/RenameModal.vue'
import WebCitationTooltip from '../components/common/WebCitationTooltip.vue'
import Toast from '../components/common/Toast.vue'
import { t } from '../i18n'
import { formatMessageTimestamp, formatRelativeTime } from '../utils/format'
import { useProjectFeatures } from './projectPage/useProjectFeatures'
import { useProjectSourceFiles } from './projectPage/useProjectSourceFiles'
import { useProjectWorkflows } from './projectPage/useProjectWorkflows'
import { useSourcePreview } from './projectPage/useSourcePreview'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
type ToolboxMode = 'tools' | 'oneclick'
const toolboxModeStorageKey = `project:${projectId}:toolboxMode`
const displayUsername = computed(() => getDisplayUsername() || t('ui.defaultUser'))
const canAdmin = computed(() => isAdmin())

const project = ref<Project | null>(null)
const sessions = ref<Session[]>([])
const currentSession = ref<Session | null>(null)
const messages = ref<Message[]>([])

const leftPanelCollapsed = ref(false)
const rightPanelCollapsed = ref(false)
const leftPanelWidth = ref(400)
const rightPanelWidth = ref(500)

let handleDeletedSourceFile: ((fileId: string) => void) | null = null

const {
  files,
  sortedFiles,
  readyFiles,
  hasReadyFiles,
  selectedFileIds,
  hoveringFileId,
  openMenuFileId,
  showUploadModal,
  isUploading,
  uploadingFiles,
  isAllSelected,
  maxFileCount: sourceMaxFileCount,
  loadFiles,
  toggleFileSelection,
  toggleSelectAll,
  triggerFileUpload,
  handleUploadFiles,
  handleInsertText,
  stopFilePolling,
  handleDeleteFile,
  renameFile,
  toggleFileMenu,
  handleClickOutside,
} = useProjectSourceFiles({
  projectId,
  showToast,
  showConfirm,
  onFileDeleted: (fileId) => handleDeletedSourceFile?.(fileId),
})

const {
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
} = useSourcePreview({
  files,
  leftPanelWidth,
  copyTextToClipboard,
  showToast,
})

handleDeletedSourceFile = handleSourceFileDeleted
void sourcePanelRef


const totalMessages = ref(0)
const messagesOffset = ref(0)
const hasMoreMessages = ref(false)
const isLoadingMoreMessages = ref(false)
const MESSAGES_PAGE_SIZE = 50
const isStreaming = ref(false)


const {
  isExportSelectionMode,
  selectedUserMessageIds,
  isExportingMessages,
  toggleExportSelectionMode,
  enterExportModeWithSelection,
  isMessageInSelectedConversation,
  toggleConversationSelection,
  toggleSelectAllUserMessages,
  handleExportSelectedMessages,
} = useMessageExportSelection({
  messages,
  currentSession,
  isStreaming,
  showToast,
})

const isEditingTitle = ref(false)
const editingTitleValue = ref('')
const titleInputRef = ref<HTMLInputElement | null>(null)
const isTitleComposing = ref(false)
const titleInputWidth = ref('120px')


const isEditingSessionTitle = ref(false)
const editingSessionTitleValue = ref('')
const generatingSessionTitleId = ref<string | null>(null)
const PLACEHOLDER_SESSION_TITLES = new Set(['', '新对话', 'New chat'])

function isPlaceholderSessionTitle(title?: string | null): boolean {
  return PLACEHOLDER_SESSION_TITLES.has((title || '').trim())
}

const isCurrentSessionTitleGenerating = computed(() => {
  if (!currentSession.value) return false
  return generatingSessionTitleId.value === currentSession.value.id ||
    currentSession.value.title_generation_status === 'generating'
})

const displaySessionTitle = computed(() => {
  if (isCurrentSessionTitleGenerating.value) return t('ui.generatingTitle2')
  return currentSession.value?.title || t('ui.newChat')
})

function shouldGenerateTitleForCurrentTurn(): boolean {
  if (!currentSession.value || isCurrentSessionTitleGenerating.value) return false
  return totalMessages.value === 0 &&
    messages.value.length === 0 &&
    isPlaceholderSessionTitle(currentSession.value.title)
}

function getSelectedSessionTitleFileNames(): string[] {
  if (selectedFileIds.value.length === 0) return []

  const selectedIds = new Set(selectedFileIds.value)
  return files.value
    .filter(file => selectedIds.has(file.id))
    .map(file => file.file_name)
    .filter(Boolean)
}

function updateSessionTitleState(
  sessionId: string,
  title?: string | null,
  status?: Session['title_generation_status']
) {
  if (currentSession.value?.id === sessionId) {
    if (title) currentSession.value.title = title
    if (status !== undefined) currentSession.value.title_generation_status = status
  }

  const idx = sessions.value.findIndex(s => s.id === sessionId)
  if (idx !== -1 && sessions.value[idx]) {
    if (title) sessions.value[idx]!.title = title
    if (status !== undefined) sessions.value[idx]!.title_generation_status = status
  }
}

async function generateTitleForSession(sessionId: string, question: string, fileNames: string[]) {
  if (generatingSessionTitleId.value === sessionId) return

  generatingSessionTitleId.value = sessionId
  isEditingSessionTitle.value = false
  editingSessionTitleValue.value = ''
  updateSessionTitleState(sessionId, null, 'generating')

  try {
    const result = await generateSessionTitle(sessionId, {
      question,
      file_names: fileNames,
    })
    updateSessionTitleState(
      sessionId,
      result.title,
      result.title_generation_status || (result.generated ? 'generated' : 'idle')
    )
  } catch (error) {
    console.warn('Failed to generate session title:', error)
    updateSessionTitleState(sessionId, null, 'failed')
  } finally {
    if (generatingSessionTitleId.value === sessionId) {
      generatingSessionTitleId.value = null
    }
  }
}


const showSessionHistory = ref(false)


const GREETING_KEYS = [
  'ui.xiaoluoIsHereGoAhead',
  'ui.whatWouldYouLikeToTalkAboutToday',
  'ui.hiYouAreHere',
] as const
const randomGreetingKey = ref<(typeof GREETING_KEYS)[number]>(
  GREETING_KEYS[Math.floor(Math.random() * GREETING_KEYS.length)] ?? GREETING_KEYS[0],
)
const localizedGreeting = computed(() => t(randomGreetingKey.value))


const inputMessage = ref('')
const webSearchConfigured = ref(false)
const agentRole = ref<AgentRole>('default')
const isThinking = ref(false)
let thinkingTimer: ReturnType<typeof setTimeout> | null = null
const streamingParts = ref<ContentPart[]>([])
const streamingElapsedMs = ref(0)
let streamStartedAtMs: number | null = null
let streamElapsedTimer: ReturnType<typeof setInterval> | null = null
let currentStreamAbort: (() => void) | null = null
const pendingStopTempId = ref<string | null>(null)
const pendingStopSessionId = ref<string | null>(null)
const pendingEditTempId = ref<string | null>(null)
const pendingEditSessionId = ref<string | null>(null)


const editingMessageId = ref<string | null>(null)
const editingContent = ref('')
const chatPanelRef = ref<InstanceType<typeof ChatPanel> | null>(null)
const editTextareaRef = computed<HTMLTextAreaElement[]>(() => chatPanelRef.value?.editTextareaElements ?? [])

const isComposing = ref(false)

const messagesRef = computed<HTMLDivElement | null>(() => chatPanelRef.value?.messagesElement ?? null)
const textareaRef = computed<HTMLTextAreaElement | null>(() => chatPanelRef.value?.textareaElement ?? null)
const inputWrapperRef = computed<HTMLDivElement | null>(() => chatPanelRef.value?.inputWrapperElement ?? null)

const {
  isMessagesScrollable,
  isUserScrolling,
  showScrollToBottom,
  scrollBtnBottom,
  autoResizeTextarea,
  resetTextareaHeight,
  scrollToBottom,
  forceScrollToBottom,
  handleMessagesScroll,
} = useChatScroll({
  messages,
  streamingParts,
  messagesRef,
  textareaRef,
  inputWrapperRef,
  hasMoreMessages,
  isLoadingMoreMessages,
  loadOlderMessages,
})

const {
  streamingRendered,
  getRenderedMessage,
  getMessageTextContent,
  isToolOnlyMessage,
  parseMessageContent,
  handleThinkingToggleClick,
} = useMessageRendering({
  messages,
  streamingParts,
  streamingElapsedMs,
})


const webCitationTooltip = reactive({
  visible: false,
  x: 0,
  y: 0,
  title: '',
  url: '',
  snippet: '',
  source: '',
  date: '',
  favicon: ''
})


const activeChatCitationNum = ref<number | null>(null)
const activeFeatureCitationNum = ref<number | null>(null)
const REPORT_MIN_WIDTH = 700
const rightPanelWidthBeforeReport = ref<number | null>(null)


const {
  features,
  activeFeature,
  showFeatureDetail,
  pollingFeatureIds,
  toolConfigModal,
  imageGenerationModal,
  imageFilesForGeneration,
  videoGenerationModal,
  videoFilesForGeneration,
  loadFeatures,
  startFeaturePolling,
  stopFeaturePolling,
  openToolConfig,
  closeToolConfig,
  handleToolConfigConfirm,
  closeImageGenerationModal,
  handleImageGenerationConfirm,
  closeVideoGenerationModal,
  handleVideoGenerationConfirm,
  closeFeatureDetail,
  renameFeatureTitle,
  handleFeatureDetailRename,
  handleFeatureClick,
  handleDeleteFeature,
} = useProjectFeatures({
  projectId,
  files,
  readyFiles,
  hasReadyFiles,
  rightPanelWidth,
  rightPanelWidthBeforeReport,
  reportMinWidth: REPORT_MIN_WIDTH,
  showToast,
  openRenameModal,
})


const {
  workflowConfigModal,
  activeWorkflowPreset,
  activeWorkflowPresetPrompt,
  workflows,
  currentWorkflow,
  workflowFeatures,
  showWorkflowDetail,
  activeWorkflowCitationNum,
  activeWorkflowFeatureId,
  featureConfigDialog,
  finalizeConfirmVisible,
  openWorkflowConfig,
  closeWorkflowConfig,
  handleWorkflowConfigConfirm,
  stopWorkflowPolling,
  startWorkflowPolling,
  startWorkflowElapsedTimer,
  stopWorkflowElapsedTimer,
  loadWorkflows,
  viewWorkflowDetail,
  refreshWorkflowDetail,
  closeWorkflowMenu,
  closeFeatureConfigDialog,
  handleWorkflowStepRegenerate,
  handleFeatureConfigConfirm,
  closeWorkflowDetail,
  clearWorkflowCitation: clearWorkflowCitationState,
  handleDeleteWorkflow,
  handleCancelWorkflow,
  executeFinalizeWorkflow,
  renameWorkflowTitle,
  handleWorkflowTitleUpdate,
  handleWorkflowVisibilityChange,
  formatWorkflowElapsed,
} = useProjectWorkflows({
  projectId,
  hasReadyFiles,
  rightPanelWidth,
  rightPanelWidthBeforeReport,
  reportMinWidth: REPORT_MIN_WIDTH,
  showToast,
  showConfirm,
  openRenameModal,
})


const renameModal = reactive({
  visible: false,
  type: 'file' as 'file' | 'feature' | 'workflow',
  id: '',
  name: '',
  saving: false
})


async function handleFeatureCitationClick(part: FeatureCitationRefPart) {

  activeChatCitationNum.value = null
  activeWorkflowCitationNum.value = null
  activeFeatureCitationNum.value = part.display_num


  const citationMeta = activeFeature.value?.citations?.[part.citation_id]
  const citationType = citationMeta?.type


  if (citationType === 'image' || citationType === 'pdf_image') {
    const fileId = citationMeta?.file_id

    if (fileId) {
      await openImageCitationSource({
        fileId,
        fileName: citationMeta?.file_name || '',
        imageName: citationMeta?.image_name,
        imageIndex: citationMeta?.image_index,
        page: citationMeta?.page
      })
    }
    return
  }


  const segmentId = part.segment_id || citationMeta?.segment_id
  if (!segmentId) return


  const fileIdFromSegment = segmentId.split('_s_')[0]!


  const file = files.value.find(f => f.id === fileIdFromSegment)

  if (file) {

    await openFilePreview(fileIdFromSegment, segmentId)
  }
}


function clearFeatureCitation() {
  activeFeatureCitationNum.value = null
  clearSourceHighlights()
}


function clearWorkflowCitation() {
  clearWorkflowCitationState()
  clearSourceHighlights()
}


const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error' | 'info' | 'warning'>('success')
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(message: string, type: 'success' | 'error' | 'info' | 'warning' = 'success', duration = 3000) {
  toastMessage.value = message
  toastType.value = type
  toastVisible.value = true
  if (toastTimer) {
    clearTimeout(toastTimer)
  }
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, duration)
}

async function copyTextToClipboard(text: string) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return
    }
  } catch (error) {
    console.warn('Clipboard API failed, falling back to execCommand:', error)
  }

  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.top = '0'
  textarea.style.left = '0'
  textarea.style.width = '1px'
  textarea.style.height = '1px'
  textarea.style.opacity = '0'
  textarea.style.pointerEvents = 'none'

  const selection = document.getSelection()
  const selectedRange = selection && selection.rangeCount > 0
    ? selection.getRangeAt(0)
    : null

  document.body.appendChild(textarea)
  textarea.focus()
  textarea.select()
  textarea.setSelectionRange(0, textarea.value.length)

  const copied = document.execCommand('copy')
  document.body.removeChild(textarea)

  if (selectedRange && selection) {
    selection.removeAllRanges()
    selection.addRange(selectedRange)
  }

  if (!copied) {
    throw new Error('Fallback copy command was not accepted')
  }
}


watch(activeChatCitationNum, (newNum, oldNum) => {

  if (oldNum !== null) {
    const oldElements = document.querySelectorAll(`.assistant-content .inline-citation[data-display-num="${oldNum}"]`)
    oldElements.forEach(el => el.classList.remove('active'))
  }

  if (newNum !== null) {
    const newElements = document.querySelectorAll(`.assistant-content .inline-citation[data-display-num="${newNum}"]`)
    newElements.forEach(el => el.classList.add('active'))
  }
})


const clickedCitationElement = ref<HTMLElement | null>(null)
const clickedCitationTop = ref<number>(0)


function getInitialToolboxMode(): ToolboxMode {
  const cached = localStorage.getItem(toolboxModeStorageKey)
  return cached === 'tools' || cached === 'oneclick' ? cached : 'oneclick'
}

const toolboxMode = ref<ToolboxMode>(getInitialToolboxMode())
const highlightedFeatureId = ref<string | null>(null)
const highlightedWorkflowId = ref<string | null>(null)
let highlightTimer: ReturnType<typeof setTimeout> | null = null


const transitionName = ref('slide-left')
const COMPACTING_CHAT_HISTORY_KEY = 'ui.compactingChatHistory'

function toToolStatusPart(tool: ToolExecuting): ToolStatusPart {
  return {
    type: 'tool_status',
    display: tool.display,
    display_key: tool.display_key || tool.displayKey,
    display_params: tool.display_params || tool.displayParams,
  }
}

function highlightGeneratedTask(type: 'feature' | 'workflow', id: string) {
  if (highlightTimer) {
    clearTimeout(highlightTimer)
    highlightTimer = null
  }
  highlightedFeatureId.value = type === 'feature' ? id : null
  highlightedWorkflowId.value = type === 'workflow' ? id : null
  highlightTimer = setTimeout(() => {
    highlightedFeatureId.value = null
    highlightedWorkflowId.value = null
    highlightTimer = null
  }, 8000)
}

async function handleFeatureStarted(data: FeatureStartedData) {
  toolboxMode.value = 'tools'
  rightPanelCollapsed.value = false
  await loadFeatures()
  if (data.feature_id) {
    pollingFeatureIds.value.add(data.feature_id)
    startFeaturePolling()
    highlightGeneratedTask('feature', data.feature_id)
  }
}

async function handleWorkflowStarted(data: WorkflowStartedData) {
  toolboxMode.value = 'oneclick'
  rightPanelCollapsed.value = false
  await loadWorkflows()
  if (data.workflow_id) {
    startWorkflowPolling(data.workflow_id)
    highlightGeneratedTask('workflow', data.workflow_id)
  }
}

function handleToolExecutingSideEffects(tool: ToolExecuting) {
  if (tool.name === 'create_feature_generation') {
    toolboxMode.value = 'tools'
    rightPanelCollapsed.value = false
    loadFeatures()
    return
  }

  if (tool.name === 'create_workflow_generation') {
    toolboxMode.value = 'oneclick'
    rightPanelCollapsed.value = false
    loadWorkflows()
    return
  }

  if (tool.name === 'regenerate_generation_step') {
    setTimeout(() => {
      loadWorkflows()
      if (currentWorkflow.value) {
        const workflowId = currentWorkflow.value.id
        refreshWorkflowDetail(workflowId)
      }
    }, 500)
  }
}

function isCompactingToolStatus(part: ContentPart): boolean {
  if (part.type !== 'tool_status') return false
  const displayKey = part.display_key || part.displayKey
  return displayKey === COMPACTING_CHAT_HISTORY_KEY || part.display === t(COMPACTING_CHAT_HISTORY_KEY)
}

function appendTextPart(content: string) {
  const lastPart = streamingParts.value[streamingParts.value.length - 1]
  if (lastPart && lastPart.type === 'text') {
    lastPart.content += content
  } else {
    streamingParts.value.push({ type: 'text', content })
  }
}

function appendReasoningPart(content: string) {
  const lastPart = streamingParts.value[streamingParts.value.length - 1]
  if (lastPart && lastPart.type === 'reasoning') {
    lastPart.content += content
  } else {
    streamingParts.value.push({ type: 'reasoning', content })
  }
}

function appendReasoningCitationMarker(citation: CitationRef) {
  appendReasoningPart(`{{CITE:${citation.display_num}}}`)
}

function appendToolExecutingParts(tools: ToolExecuting[]) {
  for (const tool of tools) {
    streamingParts.value.push(toToolStatusPart(tool))
    handleToolExecutingSideEffects(tool)
  }
}

function startStreamingTurn() {
  streamStartedAtMs = Date.now()
  streamingElapsedMs.value = 1
  if (streamElapsedTimer) {
    clearInterval(streamElapsedTimer)
  }
  streamElapsedTimer = setInterval(() => {
    streamingElapsedMs.value = finishStreamingTurnElapsedMs()
  }, 1000)
}

function finishStreamingTurnElapsedMs(): number {
  if (!streamStartedAtMs) return 0
  return Math.max(0, Date.now() - streamStartedAtMs)
}

function clearStreamingTurn() {
  streamStartedAtMs = null
  streamingElapsedMs.value = 0
  if (streamElapsedTimer) {
    clearInterval(streamElapsedTimer)
    streamElapsedTimer = null
  }
}

function summarizeCompletedToolActivity(parts: ContentPart[], elapsedMs: number): ContentPart[] {
  const activityParts: ToolSummaryActivityPart[] = []
  const summarizedParts: ContentPart[] = []
  let summaryIndex = -1

  for (const part of parts) {
    if (part.type === 'tool_status' || part.type === 'reasoning') {
      activityParts.push(part)
      if (summaryIndex === -1) {
        summaryIndex = summarizedParts.length
        summarizedParts.push({
          type: 'tool_summary',
          elapsed_ms: elapsedMs,
          activities: [],
        } satisfies ToolSummaryPart)
      }
      continue
    }

    summarizedParts.push(part)
  }

  if (summaryIndex === -1 || activityParts.length === 0) {
    return [...parts]
  }

  summarizedParts[summaryIndex] = {
    type: 'tool_summary',
    elapsed_ms: elapsedMs,
    activities: activityParts,
  }

  return summarizedParts
}

watch(() => toolboxMode.value, (newVal, oldVal) => {
  localStorage.setItem(toolboxModeStorageKey, newVal)

  if (newVal === 'tools' && oldVal === 'oneclick') {
    transitionName.value = 'slide-right'
  } else if (newVal === 'oneclick' && oldVal === 'tools') {
    transitionName.value = 'slide-left'
  }
})


const isResizing = ref(false)
const resizingSide = ref<'left' | 'right' | null>(null)


const { startResize: startResizeLeft } = usePanelResize({
  width: leftPanelWidth,
  isResizing,
  resizingSide,
  side: 'left',
  getConstraints: () => ({
    minWidth: isPreviewMode.value ? 500 : 200,
    maxWidth: isPreviewMode.value ? 900 : 600
  })
})

const { startResize: startResizeRight } = usePanelResize({
  width: rightPanelWidth,
  isResizing,
  resizingSide,
  side: 'right',
  getConstraints: () => ({
    minWidth: 280,
    maxWidth: (showFeatureDetail.value || showWorkflowDetail.value) ? 900 : 600
  })
})


const confirmDialog = reactive({
  visible: false,
  title: '',
  message: '',
  type: 'warning' as 'info' | 'warning' | 'danger',
  confirmText: t('ui.ok'),
  cancelText: t('ui.cancel'),
  onConfirm: () => {},
  onCancel: () => {}
})

function showConfirm(options: {
  title: string
  message: string
  type?: 'info' | 'warning' | 'danger'
  confirmText?: string
  cancelText?: string
}): Promise<boolean> {
  return new Promise((resolve) => {
    confirmDialog.title = options.title
    confirmDialog.message = options.message
    confirmDialog.type = options.type || 'warning'
    confirmDialog.confirmText = options.confirmText || t('ui.ok')
    confirmDialog.cancelText = options.cancelText || t('ui.cancel')
    confirmDialog.onConfirm = () => resolve(true)
    confirmDialog.onCancel = () => resolve(false)
    confirmDialog.visible = true
  })
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    handleWorkflowVisibilityChange()
  }
}

onMounted(async () => {
  await loadProject()
  await loadToolCapabilities()
  await loadFiles()
  await loadOrCreateSession()

  await loadFeatures()

  await loadWorkflows()

  document.addEventListener('click', handleClickOutside)

  document.addEventListener('click', handleCitationClickEvent)

  document.addEventListener('visibilitychange', handleVisibilityChange)

  startWorkflowElapsedTimer()
})


onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('click', handleCitationClickEvent)
  document.removeEventListener('visibilitychange', handleVisibilityChange)

  stopFilePolling()
  stopFeaturePolling()
  stopWorkflowPolling()
  stopWorkflowElapsedTimer()
  clearStreamingTurn()
  if (highlightTimer) {
    clearTimeout(highlightTimer)
    highlightTimer = null
  }
})

async function handleCitationClickEvent(event: MouseEvent) {
  const target = event.target as HTMLElement

  if (handleThinkingToggleClick(target)) {
    return
  }


  const citationEl = target.classList.contains('inline-citation')
    ? target
    : target.closest('.inline-citation') as HTMLElement | null
  if (citationEl) {


    const isInChatArea = citationEl.closest('.chat-messages') !== null
    if (!isInChatArea) return

    const citationType = citationEl.dataset.citationType

    if (citationType === 'web') {

      const url = citationEl.dataset.url
      if (url) {
        window.open(url, '_blank', 'noopener,noreferrer')
      }
    } else if (citationType === 'image') {

      const fileId = citationEl.dataset.fileId || ''
      const fileName = citationEl.dataset.file || ''
      const imageName = citationEl.dataset.imageName || ''
      const imageIndexStr = citationEl.dataset.imageIndex || ''
      const pageStr = citationEl.dataset.page || ''

      if (fileId) {
        await openImageCitationSource({
          fileId,
          fileName,
          imageName: imageName || undefined,
          imageIndex: parseOptionalInt(imageIndexStr),
          page: parseOptionalInt(pageStr)
        })
      }
    } else {

      const segmentId = citationEl.dataset.segmentId
      const displayNum = parseInt(citationEl.dataset.displayNum || citationEl.textContent || '0', 10)

      if (segmentId) {

        activeFeatureCitationNum.value = null
        activeWorkflowCitationNum.value = null
        activeChatCitationNum.value = displayNum


        const parts = segmentId.split('_s_')
        const fileId = parts[0]

        if (fileId) {

          const willExpand = !isPreviewMode.value && leftPanelWidth.value < previewMinWidth

          if (willExpand) {

            clickedCitationElement.value = citationEl
            clickedCitationTop.value = citationEl.getBoundingClientRect().top
            startPositionTracking()
          }

          await openFilePreview(fileId, segmentId)

          if (willExpand) {

            setTimeout(() => {
              stopPositionTracking()
            }, 250)
          }
        }
      }
    }
  }
}


function clearCitationHighlight() {
  activeChatCitationNum.value = null
  activeFeatureCitationNum.value = null
  activeWorkflowCitationNum.value = null
  activeWorkflowFeatureId.value = null

  clearSourceHighlights()
}


function handleChatAreaClick(event: MouseEvent) {
  const target = event.target as HTMLElement

  if (target.closest('.inline-citation')) {
    return
  }

  clearCitationHighlight()

  clearSelectedBlock()
}


function handleWebCitationHover(event: MouseEvent) {
  const target = event.target as HTMLElement
  const citationEl = target.classList.contains('web-citation')
    ? target
    : target.closest('.web-citation') as HTMLElement | null

  if (citationEl && citationEl.dataset.citationType === 'web') {
    const rect = citationEl.getBoundingClientRect()
    webCitationTooltip.x = rect.left + rect.width / 2
    webCitationTooltip.y = rect.top
    webCitationTooltip.title = citationEl.dataset.title || ''
    webCitationTooltip.url = citationEl.dataset.url || ''
    webCitationTooltip.snippet = citationEl.dataset.snippet || ''
    webCitationTooltip.source = citationEl.dataset.source || ''
    webCitationTooltip.date = citationEl.dataset.date || ''
    webCitationTooltip.favicon = citationEl.dataset.favicon || ''
    webCitationTooltip.visible = true
  }
}

function handleWebCitationLeave(event: MouseEvent) {
  const relatedTarget = event.relatedTarget as HTMLElement | null

  if (relatedTarget?.closest('.web-citation-tooltip')) return

  if (relatedTarget?.closest('.web-citation')) return
  webCitationTooltip.visible = false
}


let positionTrackingId: number | null = null

function startPositionTracking() {
  const track = () => {
    if (!clickedCitationElement.value || !messagesRef.value) {
      stopPositionTracking()
      return
    }

    const currentTop = clickedCitationElement.value.getBoundingClientRect().top
    const diff = currentTop - clickedCitationTop.value

    if (Math.abs(diff) > 0.5) {
      messagesRef.value.scrollTop += diff
    }

    positionTrackingId = requestAnimationFrame(track)
  }

  positionTrackingId = requestAnimationFrame(track)
}

function stopPositionTracking() {
  if (positionTrackingId !== null) {
    cancelAnimationFrame(positionTrackingId)
    positionTrackingId = null
  }
  clickedCitationElement.value = null
  clickedCitationTop.value = 0
}

async function loadProject() {
  try {
    const data = await getProject(projectId)
    project.value = data
  } catch (error) {
    console.error('Failed to load project:', error)
  }
}

async function loadToolCapabilities() {
  try {
    const preflight = await checkPreflight()
    webSearchConfigured.value = !!preflight.web_search_ready
  } catch (error) {
    console.error('Failed to load tool capabilities:', error)
    webSearchConfigured.value = false
  }
}

async function loadOrCreateSession() {
  try {
    const response = await getSessions(projectId)
    sessions.value = response.sessions

    if (response.sessions.length > 0 && response.sessions[0]) {
      const session = await getSession(response.sessions[0].id, MESSAGES_PAGE_SIZE, 0)
      currentSession.value = session
      messages.value = session.messages || []


      totalMessages.value = session.total_messages || 0
      messagesOffset.value = session.raw_fetched ?? session.messages?.length ?? 0
      hasMoreMessages.value = messagesOffset.value < totalMessages.value
    } else {
      const newSession = await createSession(projectId)
      currentSession.value = newSession
      messages.value = []

      totalMessages.value = 0
      messagesOffset.value = 0
      hasMoreMessages.value = false
    }
  } catch (error) {
    console.error('Failed to load session:', error)
  }
}


async function loadOlderMessages() {
  if (!currentSession.value || isLoadingMoreMessages.value || !hasMoreMessages.value) {
    return
  }

  isLoadingMoreMessages.value = true

  try {
    const session = await getSession(
      currentSession.value.id,
      MESSAGES_PAGE_SIZE,
      messagesOffset.value
    )

    const olderMessages = session.messages || []
    if (olderMessages.length > 0) {

      const existingIds = new Set(messages.value.map(m => m.id))


      const newMessages = olderMessages.filter(m => !existingIds.has(m.id))

      if (newMessages.length > 0) {

        const container = messagesRef.value
        const previousScrollHeight = container?.scrollHeight || 0


        messages.value = [...newMessages, ...messages.value]


        await nextTick()
        if (container) {
          const newScrollHeight = container.scrollHeight
          container.scrollTop = newScrollHeight - previousScrollHeight
        }


        messagesOffset.value += session.raw_fetched ?? olderMessages.length
        hasMoreMessages.value = messagesOffset.value < totalMessages.value
      } else {

        hasMoreMessages.value = false
      }
    } else {
      hasMoreMessages.value = false
    }
  } catch (error) {
    console.error('Failed to load older messages:', error)
  } finally {
    isLoadingMoreMessages.value = false
  }
}

function handleKeywordClick(keyword: string) {
  if (!currentSession.value || isStreaming.value) return


  inputMessage.value = t('ui.researchKeywordPrompt', { keyword })
  nextTick(() => {
    sendMessage()
  })
}


function handleSendEnter() {
  if (isComposing.value) return
  sendMessage()
}

function applySessionMessageToTemp(tempId: string, serverMessage: Message) {
  const idx = messages.value.findIndex(m => m.id === tempId)
  if (idx === -1) return
  messages.value[idx] = {
    ...messages.value[idx],
    ...serverMessage,
    id: serverMessage.id || tempId,
    pending_id_sync: false,
  }
}

function isTempMessageId(id?: string) {
  return !!id && /^\d+$/.test(id)
}


function isPreCompactMessage(index: number): boolean {
  const dividerIndex = messages.value.findIndex(m => m.role === 'compact_divider')
  if (dividerIndex === -1) return false
  return index < dividerIndex
}


async function syncAllPendingMessageIds() {
  console.log('🔄 [syncAllPendingMessageIds] 开始同步...')

  if (!currentSession.value) {
    console.log('⚠️ [syncAllPendingMessageIds] 没有当前会话，跳过')
    return
  }


  const pendingUsers = messages.value.filter(m => m.role === 'user' && (isTempMessageId(m.id) || m.pending_id_sync))
  console.log(`🔍 [syncAllPendingMessageIds] 需要同步的 user 消息:`, pendingUsers.map(m => ({ id: m.id, pending: m.pending_id_sync })))

  if (pendingUsers.length === 0) {
    console.log('✅ [syncAllPendingMessageIds] 没有需要同步的消息，跳过')
    return
  }

  try {
    console.log('📡 [syncAllPendingMessageIds] 调用 brief 接口...')

    const session = await getSession(currentSession.value.id, 20, 0, true)
    console.log('📥 [syncAllPendingMessageIds] brief 接口返回:', session.messages?.length, '条消息')
    const remoteMessages = session.messages || []


    const localUsers = messages.value.filter(m => m.role === 'user')
    const remoteUsers = remoteMessages.filter(m => m.role === 'user' && !isTempMessageId(m.id))


    for (const local of pendingUsers) {
      const positionIndex = localUsers.findIndex(m => m.id === local.id)
      if (positionIndex >= 0 && positionIndex < remoteUsers.length) {
        const remote = remoteUsers[positionIndex]
        if (remote) {
          console.log(`✅ [sync] 同步 user ID (位置 ${positionIndex + 1}): ${local.id} -> ${remote.id}`)
          local.id = remote.id
          local.pending_id_sync = false
        }
      } else {
        console.warn(`⚠️ [sync] 位置不匹配，本地位置: ${positionIndex}, 远程数量: ${remoteUsers.length}`)
      }
    }

  } catch (error) {
    console.error('Failed to sync message ids:', error)
  }
}

async function syncPendingStopMessageIds() {
  await syncAllPendingMessageIds()
  pendingStopTempId.value = null
  pendingStopSessionId.value = null
}

async function syncEditMessageIds() {
  await syncAllPendingMessageIds()
  pendingEditTempId.value = null
  pendingEditSessionId.value = null
}

function stopStreaming() {
  console.log('⏹️ [stopStreaming] 停止生成...')

  if (!isStreaming.value) {
    console.log('⚠️ [stopStreaming] 没有正在进行的流式生成，跳过')
    return
  }

  if (currentStreamAbort) {
    currentStreamAbort()
    currentStreamAbort = null
  }

  if (thinkingTimer) {
    clearTimeout(thinkingTimer)
    thinkingTimer = null
  }

  isThinking.value = false
  clearStreamingTurn()

  if (streamingParts.value.length > 0 && currentSession.value) {
    const tempId = Date.now().toString()
    messages.value.push({
      id: tempId,
      session_id: currentSession.value.id,
      role: 'assistant',
      content_parts: [...streamingParts.value],
      created_at: new Date().toISOString(),
      agent_role: agentRole.value,
      pending_id_sync: true
    })
    pendingStopTempId.value = tempId
    pendingStopSessionId.value = currentSession.value.id
    console.log('📝 [stopStreaming] 创建了临时 assistant 消息:', tempId)
  }

  streamingParts.value = []
  isStreaming.value = false


  console.log('🔄 [stopStreaming] 调用 syncPendingStopMessageIds...')
  syncPendingStopMessageIds()
}

async function sendMessage() {
  if (!inputMessage.value.trim() || !currentSession.value || isStreaming.value) return

  const sessionIdForTurn = currentSession.value.id
  const shouldGenerateTitleAfterSend = shouldGenerateTitleForCurrentTurn()
  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  resetTextareaHeight()


  isUserScrolling.value = false
  showScrollToBottom.value = false


  messages.value.push({
    id: Date.now().toString(),
    session_id: sessionIdForTurn,
    role: 'user',
    content: userMessage,
    created_at: new Date().toISOString(),
    pending_id_sync: true
  })

  isStreaming.value = true
  isThinking.value = false
  streamingParts.value = []
  startStreamingTurn()


  const startThinkingTimer = () => {
    if (thinkingTimer) clearTimeout(thinkingTimer)
    thinkingTimer = setTimeout(() => {
      isThinking.value = true
    }, 2000)
  }


  const resetThinkingTimer = () => {
    isThinking.value = false
    startThinkingTimer()
  }


  const clearThinkingTimer = () => {
    if (thinkingTimer) {
      clearTimeout(thinkingTimer)
      thinkingTimer = null
    }
    isThinking.value = false
  }


  startThinkingTimer()

  const fileIds = selectedFileIds.value.length > 0 ? selectedFileIds.value : undefined
  const titleFileNames = getSelectedSessionTitleFileNames()

  if (shouldGenerateTitleAfterSend) {
    void generateTitleForSession(sessionIdForTurn, userMessage, titleFileNames)
  }

  currentStreamAbort = chatStream(
    sessionIdForTurn,
    userMessage,
    fileIds,
    {
      onContent: (content: string) => {

        resetThinkingTimer()
        appendTextPart(content)
      },
      onCitationRef: (citation: CitationRef) => {

        if (citation.type === 'web') {

          streamingParts.value.push({
            type: 'citation_ref',
            citation_type: 'web',
            display_num: citation.display_num,
            title: citation.title,
            url: citation.url,
            snippet: citation.snippet,
            source: citation.source,
            published_date: citation.published_date,
            favicon: citation.favicon || ''
          } as any)
        } else if (citation.type === 'image') {

          streamingParts.value.push({
            type: 'citation_ref',
            citation_type: 'image',
            display_num: citation.display_num,
            file_name: citation.file_name,
            file_id: citation.file_id,

            image_name: citation.image_name,
            image_index: citation.image_index,
            page: citation.page
          } as any)
        } else if (citation.type === 'audio') {

          streamingParts.value.push({
            type: 'citation_ref',
            display_num: citation.display_num,
            file_name: citation.file_name,
            segment_id: citation.segment_id,
            summary: citation.summary
          } as any)
        } else {

          streamingParts.value.push({
            type: 'citation_ref',
            display_num: citation.display_num,
            file_name: citation.file_name,
            segment_id: citation.segment_id,
            summary: citation.summary
          } as any)
        }
      },
      onReasoning: (content: string) => {
        appendReasoningPart(content)
      },
      onReasoningCitationRef: (citation) => {
        appendReasoningCitationMarker(citation)
      },
      onToolExecuting: (tools: ToolExecuting[]) => {
        appendToolExecutingParts(tools)
      },
      onWorkflowStarted: handleWorkflowStarted,
      onFeatureStarted: handleFeatureStarted,
      onCitations: () => {

      },
      onCompacting: () => {
        streamingParts.value.push({
          type: 'tool_status',
          display: t(COMPACTING_CHAT_HISTORY_KEY),
          display_key: COMPACTING_CHAT_HISTORY_KEY,
        })
      },
      onCompactDone: () => {

        streamingParts.value = streamingParts.value.filter(
          p => !isCompactingToolStatus(p)
        )
        streamingParts.value.push({
          type: 'text',
          content: `\n\n${t('ui.compactDivider')}\n\n`
        })
      },
      onCompactFailed: (message: string) => {
        streamingParts.value = streamingParts.value.filter(
          p => !isCompactingToolStatus(p)
        )
        console.warn('Compact failed:', message)
      },
      onDone: (doneData) => {

        clearThinkingTimer()
        const contentParts = summarizeCompletedToolActivity(
          streamingParts.value,
          finishStreamingTurnElapsedMs()
        )
        messages.value.push({
          id: Date.now().toString(),
          session_id: currentSession.value!.id,
          role: 'assistant',
          content_parts: contentParts,
          created_at: new Date().toISOString(),
          agent_role: doneData.agentRole || agentRole.value,
          pending_id_sync: true
        })
        streamingParts.value = []
        isStreaming.value = false
        currentStreamAbort = null
        clearStreamingTurn()


        if (doneData.sessionUpdated?.title) {
          updateSessionTitleState(sessionIdForTurn, doneData.sessionUpdated.title)
        }

      },
      onError: (error: string, hasPartial?: boolean) => {

        clearThinkingTimer()
        console.error('Stream error:', error)


        if (!hasPartial) {
          streamingParts.value = []
        }


        messages.value.push({
          id: Date.now().toString(),
          session_id: currentSession.value!.id,
          role: 'assistant',
          content_parts: hasPartial ? [...streamingParts.value] : undefined,
          content: hasPartial ? undefined : `Generation failed: ${error}`,
          _error: error,
          has_partial: hasPartial,
          created_at: new Date().toISOString()
        })

        streamingParts.value = []
        isStreaming.value = false
        currentStreamAbort = null
        clearStreamingTurn()


        syncAllPendingMessageIds()
      },
      onMessageIds: (userMessageId: string, assistantMessageId: string) => {

        for (let i = messages.value.length - 1; i >= 0; i--) {
          const msg = messages.value[i]
          if (msg && msg.role === 'user' && msg.session_id === currentSession.value?.id) {

            if (msg.id && /^\d+$/.test(msg.id)) {
              msg.id = userMessageId
              msg.pending_id_sync = false
              console.log(`✅ [sendMessage] 更新 user message ID: ${userMessageId}`)
              break
            }
          }
        }


        for (let i = messages.value.length - 1; i >= 0; i--) {
          const msg = messages.value[i]
          if (msg && msg.role === 'assistant' && msg.session_id === currentSession.value?.id) {

            if (msg.id && /^\d+$/.test(msg.id)) {
              msg.id = assistantMessageId
              msg.pending_id_sync = false
              console.log(`✅ [sendMessage] 更新 assistant message ID: ${assistantMessageId}`)
              break
            }
          }
        }

        if (pendingStopTempId.value && isTempMessageId(pendingStopTempId.value)) {
          applySessionMessageToTemp(pendingStopTempId.value, {
            id: assistantMessageId,
            session_id: currentSession.value!.id,
            role: 'assistant',
            created_at: new Date().toISOString()
          })
          pendingStopTempId.value = null
          pendingStopSessionId.value = null
        }
      }
    },
    webSearchConfigured.value,
    agentRole.value
  )
}


const copyToastVisible = ref(false)
const copyToastMessage = ref('')
let copyToastTimer: ReturnType<typeof setTimeout> | null = null

function showCopyToast(message: string) {
  copyToastMessage.value = message
  copyToastVisible.value = true
  if (copyToastTimer) clearTimeout(copyToastTimer)
  copyToastTimer = setTimeout(() => {
    copyToastVisible.value = false
  }, 2000)
}


async function copyMessageAsText(msg: Message) {
  const markdown = getMessageTextContent(msg)

  let plainText = markdown

    .replace(/^#{1,6}\s+/gm, '')

    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/__(.+?)__/g, '$1')
    .replace(/_(.+?)_/g, '$1')

    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/^[\s]*[-*+]\s+/gm, '')
    .replace(/^[\s]*\d+\.\s+/gm, '')
    .replace(/^>\s*/gm, '')
    .replace(/```[\s\S]*?```/g, (match) => {
      return match.replace(/```\w*\n?/g, '').replace(/```$/g, '')
    })
    .replace(/\n{3,}/g, '\n\n')
    .trim()

  try {
    await copyTextToClipboard(plainText)
    showCopyToast(t('ui.copiedAsPlainText'))
  } catch (err) {
    console.error('复制失败:', err)
    showCopyToast(t('ui.copyFailed'))
  }
}

async function copyMessageAsMarkdown(msg: Message) {
  const markdown = getMessageTextContent(msg)

  try {
    await copyTextToClipboard(markdown)
    showCopyToast(t('ui.copiedAsMarkdown'))
  } catch (err) {
    console.error('复制失败:', err)
    showCopyToast(t('ui.copyFailed'))
  }
}

async function copyUserMessage(msg: Message) {
  try {
    await copyTextToClipboard(msg.content || '')
    showCopyToast(t('ui.copied2'))
  } catch (err) {
    console.error('复制失败:', err)
    showCopyToast(t('ui.copyFailed'))
  }
}

function startEditMessage(msg: Message) {
  if (isStreaming.value) return

  if (isTempMessageId(msg.id) || msg.pending_id_sync) {
    showToast(t('ui.networkSyncingTryLater'), 'warning')
    return
  }

  editingMessageId.value = msg.id
  editingContent.value = msg.content || ''
  nextTick(() => {
    autoResizeEditTextarea()
    editTextareaRef.value[0]?.focus()
  })
}

function autoResizeEditTextarea() {
  const textarea = editTextareaRef.value[0]
  if (!textarea) return

  const minHeight = 60
  const maxHeight = 300

  textarea.style.overflowY = 'hidden'
  textarea.style.height = minHeight + 'px'

  const scrollHeight = textarea.scrollHeight
  const newHeight = Math.max(minHeight, Math.min(scrollHeight, maxHeight))

  textarea.style.height = newHeight + 'px'

  if (scrollHeight > maxHeight) {
    textarea.style.overflowY = 'auto'
  }
}

function cancelEditMessage() {
  editingMessageId.value = null
  editingContent.value = ''
}

async function submitEditMessage(msg: Message) {
  if (!editingContent.value.trim() || isStreaming.value || !currentSession.value) return

  const newContent = editingContent.value.trim()
  const messageIndex = messages.value.findIndex(m => m.id === msg.id)
  if (messageIndex === -1) return

  const targetMessage = messages.value[messageIndex]
  if (!targetMessage) return

  targetMessage.content = newContent
  targetMessage.content_parts = undefined

  streamingParts.value = []
  isThinking.value = false

  messages.value = messages.value.slice(0, messageIndex + 1)

  editingMessageId.value = null
  editingContent.value = ''

  isStreaming.value = true

  const startLocalThinkingTimer = () => {
    if (thinkingTimer) clearTimeout(thinkingTimer)
    thinkingTimer = setTimeout(() => {
      isThinking.value = true
    }, 2000)
  }

  const clearLocalThinkingTimer = () => {
    if (thinkingTimer) {
      clearTimeout(thinkingTimer)
      thinkingTimer = null
    }
    isThinking.value = false
  }

  startLocalThinkingTimer()

  scrollToBottom()

  if (isTempMessageId(targetMessage.id) || targetMessage.pending_id_sync) {
    showToast(t('ui.messageSyncingRefreshAndRetry'), 'error')
    isStreaming.value = false
    isThinking.value = false
    editingMessageId.value = msg.id
    editingContent.value = newContent
    return
  }

  startStreamingTurn()

  currentStreamAbort = editMessageAndRegenerate(
    currentSession.value.id,
    targetMessage.id,
    newContent,
    selectedFileIds.value.length > 0 ? selectedFileIds.value : undefined,
    {
      onContent: (content: string) => {
        clearLocalThinkingTimer()
        startLocalThinkingTimer()
        appendTextPart(content)
      },
      onCitationRef: (citation) => {
        if (citation.type === 'web') {
          streamingParts.value.push({
            type: 'citation_ref',
            citation_type: 'web',
            display_num: citation.display_num,
            title: citation.title,
            url: citation.url,
            snippet: citation.snippet,
            source: citation.source,
            published_date: citation.published_date,
            favicon: citation.favicon
          } as any)
        } else if (citation.type === 'image') {
          streamingParts.value.push({
            type: 'citation_ref',
            citation_type: 'image',
            display_num: citation.display_num,
            file_id: citation.file_id,
            file_name: citation.file_name,
            image_name: citation.image_name,
            image_index: citation.image_index,
            page: citation.page
          } as any)
        } else if (citation.type === 'audio') {
          streamingParts.value.push({
            type: 'citation_ref',
            display_num: citation.display_num,
            file_name: citation.file_name,
            segment_id: citation.segment_id,
            summary: citation.summary
          } as any)
        } else {
          streamingParts.value.push({
            type: 'citation_ref',
            display_num: citation.display_num,
            file_name: citation.file_name,
            segment_id: citation.segment_id,
            summary: citation.summary
          } as any)
        }
      },
      onReasoning: (content: string) => {
        appendReasoningPart(content)
      },
      onReasoningCitationRef: (citation) => {
        appendReasoningCitationMarker(citation)
      },
      onToolExecuting: (tools) => {
        appendToolExecutingParts(tools)
      },
      onWorkflowStarted: handleWorkflowStarted,
      onFeatureStarted: handleFeatureStarted,
      onDone: (doneData) => {
        clearLocalThinkingTimer()
        const tempId = Date.now().toString()
        const contentParts = summarizeCompletedToolActivity(
          streamingParts.value,
          finishStreamingTurnElapsedMs()
        )
        messages.value.push({
          id: tempId,
          session_id: currentSession.value!.id,
          role: 'assistant',
          content_parts: contentParts,
          created_at: new Date().toISOString(),
          agent_role: doneData.agentRole || agentRole.value,
          pending_id_sync: true
        })
        pendingEditTempId.value = tempId
        pendingEditSessionId.value = currentSession.value!.id
        streamingParts.value = []
        isStreaming.value = false
        isThinking.value = false
        currentStreamAbort = null
        clearStreamingTurn()

        const lastUser = messages.value.slice().reverse().find(m => m.role === 'user')
        if (lastUser && isTempMessageId(lastUser.id)) {
          syncEditMessageIds()
        }
      },
      onError: (error: string, hasPartial?: boolean) => {
        clearLocalThinkingTimer()
        console.error('编辑消息失败:', error)

        if (!hasPartial) {
          streamingParts.value = []
        }

        isStreaming.value = false
        isThinking.value = false

        const tempId = Date.now().toString()
        messages.value.push({
          id: tempId,
          session_id: currentSession.value!.id,
          role: 'assistant',
          content_parts: hasPartial ? [...streamingParts.value] : undefined,
          content: hasPartial ? undefined : `Generation failed: ${error}`,
          _error: error,
          has_partial: hasPartial,
          created_at: new Date().toISOString()
        })
        pendingEditTempId.value = tempId
        pendingEditSessionId.value = currentSession.value!.id

        streamingParts.value = []
        currentStreamAbort = null
        clearStreamingTurn()

        const lastUser = messages.value.slice().reverse().find(m => m.role === 'user')
        if (lastUser && isTempMessageId(lastUser.id)) {
          syncEditMessageIds()
        }

        syncAllPendingMessageIds()
      },
      onMessageIds: (userMessageId: string, assistantMessageId: string) => {
        if (targetMessage) {
          targetMessage.id = userMessageId
          targetMessage.pending_id_sync = false
          console.log(`✅ [submitEditMessage] 更新被编辑的 user message ID: ${targetMessage.id} -> ${userMessageId}`)
        }

        for (let i = messages.value.length - 1; i >= 0; i--) {
          const msg = messages.value[i]
          if (msg && msg.role === 'assistant' && msg.session_id === currentSession.value?.id) {
            if (msg.id && /^\d+$/.test(msg.id)) {
              msg.id = assistantMessageId
              msg.pending_id_sync = false
              console.log(`✅ [submitEditMessage] 更新 assistant message ID: ${assistantMessageId}`)
              break
            }
          }
        }

        if (pendingEditTempId.value && isTempMessageId(pendingEditTempId.value)) {
          applySessionMessageToTemp(pendingEditTempId.value, {
            id: assistantMessageId,
            session_id: currentSession.value!.id,
            role: 'assistant',
            created_at: new Date().toISOString()
          })
          pendingEditTempId.value = null
          pendingEditSessionId.value = null
        }
      }
    },
    webSearchConfigured.value,
    agentRole.value
  )
}

function isLastAssistantMessage(index: number): boolean {
  for (let i = index + 1; i < messages.value.length; i++) {
    if (messages.value[i]?.role === 'assistant') {
      return false
    }
  }
  return messages.value[index]?.role === 'assistant'
}

function shouldShowMessageActions(index: number): boolean {
  const msg = messages.value[index]
  if (!msg || msg.role !== 'assistant') return false

  if (index === messages.value.length - 1) return true

  const nextMsg = messages.value[index + 1]
  if (nextMsg?.role === 'user') return true

  return false
}

async function regenerateMessage(assistantIndex: number) {
  if (isStreaming.value || !currentSession.value) return

  let userMessage: Message | null = null
  let userIndex = -1
  for (let i = assistantIndex - 1; i >= 0; i--) {
    if (messages.value[i]?.role === 'user') {
      userMessage = messages.value[i]!
      userIndex = i
      break
    }
  }

  if (!userMessage || userIndex < 0) {
    console.error('找不到对应的用户消息')
    return
  }

  if (isTempMessageId(userMessage.id) || userMessage.pending_id_sync) {
    showToast(t('ui.messageSyncingRefreshAndRetry'), 'error')
    return
  }

  streamingParts.value = []
  isThinking.value = false

  messages.value = messages.value.slice(0, userIndex + 1)

  isStreaming.value = true

  const startLocalThinkingTimer = () => {
    if (thinkingTimer) clearTimeout(thinkingTimer)
    thinkingTimer = setTimeout(() => {
      isThinking.value = true
    }, 2000)
  }

  const clearLocalThinkingTimer = () => {
    if (thinkingTimer) {
      clearTimeout(thinkingTimer)
      thinkingTimer = null
    }
    isThinking.value = false
  }

  startLocalThinkingTimer()

  scrollToBottom()

  startStreamingTurn()

  console.log(`📤 [regenerateMessage] 调用 API，user ID: ${userMessage.id}, 是否临时ID: ${isTempMessageId(userMessage.id)}`)
  currentStreamAbort = editMessageAndRegenerate(
    currentSession.value.id,
    userMessage.id,
    userMessage.content || '',
    selectedFileIds.value.length > 0 ? selectedFileIds.value : undefined,
    {
      onContent: (content: string) => {
        clearLocalThinkingTimer()
        startLocalThinkingTimer()
        appendTextPart(content)
      },
      onCitationRef: (citation) => {
        if (citation.type === 'web') {
          streamingParts.value.push({
            type: 'citation_ref',
            citation_type: 'web',
            display_num: citation.display_num,
            title: citation.title,
            url: citation.url,
            snippet: citation.snippet,
            source: citation.source,
            published_date: citation.published_date,
            favicon: citation.favicon
          } as any)
        } else if (citation.type === 'image') {
          streamingParts.value.push({
            type: 'citation_ref',
            citation_type: 'image',
            display_num: citation.display_num,
            file_id: citation.file_id,
            file_name: citation.file_name
          } as any)
        } else if (citation.type === 'audio') {
          streamingParts.value.push({
            type: 'citation_ref',
            display_num: citation.display_num,
            file_name: citation.file_name,
            segment_id: citation.segment_id,
            summary: citation.summary
          } as any)
        } else {
          streamingParts.value.push({
            type: 'citation_ref',
            display_num: citation.display_num,
            file_name: citation.file_name,
            segment_id: citation.segment_id,
            summary: citation.summary
          } as any)
        }
      },
      onReasoning: (content: string) => {
        appendReasoningPart(content)
      },
      onReasoningCitationRef: (citation) => {
        appendReasoningCitationMarker(citation)
      },
      onToolExecuting: (tools) => {
        appendToolExecutingParts(tools)
      },
      onWorkflowStarted: handleWorkflowStarted,
      onFeatureStarted: handleFeatureStarted,
      onDone: (doneData) => {
        clearLocalThinkingTimer()
        const contentParts = summarizeCompletedToolActivity(
          streamingParts.value,
          finishStreamingTurnElapsedMs()
        )
        messages.value.push({
          id: Date.now().toString(),
          session_id: currentSession.value!.id,
          role: 'assistant',
          content_parts: contentParts,
          created_at: new Date().toISOString(),
          agent_role: doneData.agentRole || agentRole.value,
          pending_id_sync: true
        })
        streamingParts.value = []
        isStreaming.value = false
        isThinking.value = false
        currentStreamAbort = null
        clearStreamingTurn()
      },
      onError: (error: string, hasPartial?: boolean) => {
        clearLocalThinkingTimer()
        console.error('重新生成失败:', error)

        if (!hasPartial) {
          streamingParts.value = []
        }

        isStreaming.value = false
        isThinking.value = false

        messages.value.push({
          id: Date.now().toString(),
          session_id: currentSession.value!.id,
          role: 'assistant',
          content_parts: hasPartial ? [...streamingParts.value] : undefined,
          content: hasPartial ? undefined : `Generation failed: ${error}`,
          _error: error,
          has_partial: hasPartial,
          created_at: new Date().toISOString()
        })

        streamingParts.value = []
        currentStreamAbort = null
        clearStreamingTurn()

        syncAllPendingMessageIds()
      },
      onMessageIds: (userMessageId: string, assistantMessageId: string) => {
        if (userMessage) {
          userMessage.id = userMessageId
          userMessage.pending_id_sync = false
          console.log(`✅ [regenerateMessage] 更新 user message ID: ${userMessageId}`)
        }

        for (let i = messages.value.length - 1; i >= 0; i--) {
          const msg = messages.value[i]
          if (msg && msg.role === 'assistant' && msg.session_id === currentSession.value?.id) {
            if (msg.id && /^\d+$/.test(msg.id)) {
              msg.id = assistantMessageId
              msg.pending_id_sync = false
              console.log(`✅ [regenerateMessage] 更新 assistant message ID: ${assistantMessageId}`)
              break
            }
          }
        }
      }
    },
    webSearchConfigured.value,
    agentRole.value
  )
}

function goBack() {
  router.push('/')
}

function logout() {
  clearTokens()
  router.push('/login')
}

function calculateTitleWidth(text: string): string {
  let width = 0
  for (const char of text) {
    if (/[\u4e00-\u9fa5]/.test(char)) {
      width += 16
    } else {
      width += 10
    }
  }
  width += 32
  return Math.max(150, Math.min(width, 600)) + 'px'
}

function updateTitleInputWidth() {
  titleInputWidth.value = calculateTitleWidth(editingTitleValue.value)
}

function startTitleEdit() {
  if (!project.value) return
  editingTitleValue.value = project.value.name
  titleInputWidth.value = calculateTitleWidth(project.value.name)
  isEditingTitle.value = true
  nextTick(() => {
    titleInputRef.value?.focus()
    titleInputRef.value?.select()
  })
}

function cancelTitleEdit() {
  isEditingTitle.value = false
  editingTitleValue.value = ''
}

function handleTitleEnter() {
  if (isTitleComposing.value) return
  titleInputRef.value?.blur()
}

async function handleTitleBlur() {
  if (!project.value) {
    cancelTitleEdit()
    return
  }

  const newName = editingTitleValue.value.trim()
  const oldName = project.value.name

  if (!newName || newName === oldName) {
    cancelTitleEdit()
    return
  }

  try {
    const updated = await updateProject(project.value.id, { name: newName })
    project.value = { ...project.value, ...updated }
  } catch (error) {
    console.error('Failed to rename project:', error)
  }

  isEditingTitle.value = false
  editingTitleValue.value = ''
}

function openRenameModal(type: 'file' | 'feature' | 'workflow', id: string, name: string) {
  openMenuFileId.value = null
  renameModal.visible = true
  renameModal.type = type
  renameModal.id = id
  renameModal.name = name
  renameModal.saving = false
}

function closeRenameModal() {
  renameModal.visible = false
}

async function handleRenameConfirm(newName: string) {
  if (newName === renameModal.name) {
    closeRenameModal()
    return
  }

  renameModal.saving = true

  try {
    if (renameModal.type === 'file') {
      await renameFile(renameModal.id, newName)
    } else if (renameModal.type === 'workflow') {
      await renameWorkflowTitle(renameModal.id, newName)
    } else {
      await renameFeatureTitle(renameModal.id, newName)
    }
    closeRenameModal()
  } catch (error) {
    console.error('Failed to rename:', error)
    renameModal.saving = false
  }
}


async function handleCreateNewSession() {
  if (isStreaming.value) return

  try {
    const result = await createSession(projectId)
    currentSession.value = result
    messages.value = []
    streamingParts.value = []
    totalMessages.value = 0
    messagesOffset.value = 0
    hasMoreMessages.value = false
    const response = await getSessions(projectId)
    sessions.value = response.sessions
  } catch (error) {
    console.error('Failed to create new session:', error)
  }
}

async function handleSwitchSession(sessionId: string) {
  if (sessionId === currentSession.value?.id) {
    showSessionHistory.value = false
    return
  }

  isExportSelectionMode.value = false
  selectedUserMessageIds.value = []

  try {
    const session = await getSession(sessionId, MESSAGES_PAGE_SIZE, 0)
    currentSession.value = session
    messages.value = session.messages || []
    totalMessages.value = session.total_messages || 0
    messagesOffset.value = session.raw_fetched ?? session.messages?.length ?? 0
    hasMoreMessages.value = messagesOffset.value < totalMessages.value
    streamingParts.value = []
    showSessionHistory.value = false
    nextTick(() => forceScrollToBottom())
  } catch (error) {
    console.error('Failed to switch session:', error)
  }
}

async function handleDeleteSession(sessionId: string, title: string) {
  const displayTitle = title || t('ui.newChat')
  const confirmed = await showConfirm({
    title: t('ui.deleteChat'),
    message: t('ui.deleteChatMessage', { title: displayTitle }),
    type: 'danger',
    confirmText: t('ui.delete'),
    cancelText: t('ui.cancel')
  })
  if (!confirmed) return

  try {
    await deleteSession(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)

    if (currentSession.value?.id === sessionId) {
      if (sessions.value.length > 0) {
        await handleSwitchSession(sessions.value[0]!.id)
      } else {
        await handleCreateNewSession()
      }
    }
  } catch (error) {
    console.error('Failed to delete session:', error)
  }
}

function startSessionTitleEdit() {
  if (!currentSession.value) return
  editingSessionTitleValue.value = currentSession.value.title || ''
  isEditingSessionTitle.value = true
}

function cancelSessionTitleEdit() {
  isEditingSessionTitle.value = false
  editingSessionTitleValue.value = ''
}

async function saveSessionTitle() {
  if (!currentSession.value) {
    isEditingSessionTitle.value = false
    return
  }

  const newTitle = editingSessionTitleValue.value.trim()
  if (!newTitle || newTitle === currentSession.value.title) {
    isEditingSessionTitle.value = false
    return
  }

  try {
    const updated = await updateSessionTitle(currentSession.value.id, newTitle)
    currentSession.value.title = updated.title
    const idx = sessions.value.findIndex(s => s.id === currentSession.value!.id)
    if (idx !== -1 && sessions.value[idx]) {
      sessions.value[idx]!.title = updated.title
    }
  } catch (error) {
    console.error('Failed to update session title:', error)
  } finally {
    isEditingSessionTitle.value = false
  }
}

async function handleWorkflowCitationClick(part: FeatureCitationRefPart, feature: WorkflowContentFeature) {
  activeChatCitationNum.value = null
  activeFeatureCitationNum.value = null
  activeWorkflowCitationNum.value = part.display_num
  activeWorkflowFeatureId.value = feature.id

  const citationMeta = feature.citations?.[part.citation_id]
  const citationType = citationMeta?.type

  if (citationType === 'image' || citationType === 'pdf_image') {
    const fileId = citationMeta?.file_id

    if (fileId) {
      await openImageCitationSource({
        fileId,
        fileName: citationMeta?.file_name || '',
        imageName: citationMeta?.image_name,
        imageIndex: citationMeta?.image_index,
        page: citationMeta?.page
      })
    }
    return
  }

  const segmentId = part.segment_id || citationMeta?.segment_id
  if (!segmentId) {
    console.warn('Citation segment_id not found:', part)
    return
  }

  const fileIdFromSegment = segmentId.split('_s_')[0]!

  const file = files.value.find(f => f.id === fileIdFromSegment)

  if (file) {
    const workflowPanel = document.querySelector('.workflow-detail-panel')
    const citationEl = workflowPanel?.querySelector(
      `.inline-citation.active[data-display-num="${part.display_num}"]`
    ) as HTMLElement | null

    const beforeRect = citationEl?.getBoundingClientRect()

    await openFilePreview(fileIdFromSegment, segmentId)

    await new Promise(resolve => setTimeout(resolve, 250))

    const afterRect = citationEl?.getBoundingClientRect()

    if (beforeRect && afterRect) {
      const deltaY = afterRect.top - beforeRect.top
      if (Math.abs(deltaY) > 50) {
        const contentEl = workflowPanel?.querySelector('.workflow-report-content')
        contentEl?.scrollBy({ top: deltaY, behavior: 'smooth' })
      }
    }
  }
}

function formatTime(isoString: string): string {
  return formatRelativeTime(isoString)
}

function formatMessageTime(isoString: string): string {
  return formatMessageTimestamp(isoString)
}

defineExpose({ titleInputRef })
</script>

<style scoped>
.project-page {
  height: 100vh;
  max-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
  overflow: hidden;
}

.project-page.resizing {
  cursor: col-resize;
  user-select: none;
}


.project-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: var(--bg-page);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  padding: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.back-btn:hover {
  background: var(--bg-hover);
}

.back-logo {
  height: 40px;
  width: auto;
}

.project-title-wrapper {
  display: flex;
  align-items: center;
}

.project-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  cursor: pointer;
  padding: 4px 8px;
  margin: -4px -8px;
  border-radius: 6px;
  transition: background 0.15s;
}

.project-title:hover {
  background: var(--bg-hover);
}

.project-title-input {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  background: var(--bg-white);
  border: 1px solid var(--primary-color);
  border-radius: 6px;
  padding: 4px 8px;
  outline: none;
  box-shadow: 0 0 0 3px var(--primary-light);
  transition: width 0.1s ease;
}

.btn-settings {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.btn-settings:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.user-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: default;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}


.project-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 6px;
}


.project-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  gap: 2px;
  border-radius: 16px;
}


.project-footer {
  text-align: center;
  padding: 2px 2px;
  font-size: 11px;
  color: var(--text-tertiary);
}


.panel-header {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  overflow: visible;
  position: relative;
  z-index: 10;
}

.panel-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.panel-toggle-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 6px;
  color: var(--text-tertiary);
  transition: background 0.15s, color 0.15s;
}

.panel-toggle-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}


.resizer {
  width: 8px;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  transition: background 0.15s;
  flex-shrink: 0;
}

.resizer:hover {
  background: var(--bg-hover);
}

.resizer.hidden {
  display: none;
}

.resizer-line {
  width: 2px;
  height: 40px;
  background: var(--border-color);
  border-radius: 1px;
  transition: background 0.15s, height 0.15s;
}

.resizer:hover .resizer-line {
  background: var(--primary-color);
  height: 60px;
}


.collapsed-sidebar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 6px;
  background: var(--bg-white);
  border-radius: 16px;
  flex-shrink: 0;
}

.collapsed-sidebar.left {

}

.collapsed-sidebar.right {

}

.collapsed-icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  position: relative;
}

.collapsed-icon-btn:hover:not(.disabled) {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.collapsed-icon-btn.disabled {
  color: var(--text-tertiary);
  opacity: 0.6;
  cursor: not-allowed;
}

.icon-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background: var(--primary-color);
  color: white;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-role-toggle {
  display: inline-flex;
  align-items: center;
  background: var(--bg-main);
  border-radius: 14px;
  padding: 2px;
  gap: 2px;
}

.agent-role-toggle .role-btn {
  position: relative;
  padding: 4px 10px;
  font-size: 12px;
  color: var(--text-tertiary);
  background: transparent;
  border-radius: 12px;
  transition: all 0.2s;
  cursor: pointer;
  white-space: nowrap;
}

.agent-role-toggle .role-btn:hover {
  color: var(--text-secondary);
}

.agent-role-toggle .role-btn.active {
  background: var(--bg-white);
  color: var(--primary-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}


.agent-role-toggle .role-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 10px;
  background: var(--text-primary);
  color: white;
  font-size: 12px;
  border-radius: 6px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
  pointer-events: none;
  z-index: 100;
}

.agent-role-toggle .role-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: var(--text-primary);
}

.agent-role-toggle .role-btn:hover .role-tooltip {
  opacity: 1;
  visibility: visible;
}

</style>
