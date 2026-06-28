<template>
  <div class="project-page" :class="{ resizing: isResizing }" @click="closeWorkflowMenu">

    <header class="project-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack" title="返回首页">
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
            title="点击编辑项目名称"
          >{{ project?.name || 'Untitled' }}</h1>
        </div>
      </div>
      <div class="header-right">
        <LanguageSwitcher />
        <button v-if="canAdmin" class="btn-settings" @click="router.push('/admin')" title="用户管理">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zM8 11c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5C15 14.17 10.33 13 8 13zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
          </svg>
        </button>
        <button v-if="canAdmin" class="btn-settings" @click="router.push('/settings')" title="设置">
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
        <button class="btn-settings" @click="logout" title="退出登录">
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
        :title="currentSession?.title || '新对话'"
        :is-editing-title="isEditingSessionTitle"
        :editing-title-value="editingSessionTitleValue"
        :is-streaming="isStreaming"
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
        :enable-web-search="enableWebSearch"
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
        @update:enable-web-search="enableWebSearch = $event"
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
        :workflows="workflows"
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
        @open-workflow-config="openWorkflowConfig"
        @view-workflow-detail="viewWorkflowDetail"
      />
      </div>


      <footer class="project-footer">
        小洛提供的内容未必准确，因此请仔细核查回答内容。
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
      :hide-prompt="toolConfigModal.hidePrompt"
      :files="files"
      :selected-file-ids="selectedFileIds"
      @close="closeToolConfig"
      @confirm="handleToolConfigConfirm"
    />


    <WorkflowConfigModal
      :visible="workflowConfigModal.visible"
      :modal-title="activeWorkflowPreset.title"
      :description="activeWorkflowPreset.description"
      :hint="activeWorkflowPreset.hint"
      :builtin-prompt="activeWorkflowPresetPrompt"
      :prompt-placeholder="activeWorkflowPreset.promptPlaceholder"
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
      :title="renameModal.type === 'file' ? '重命名文件' : '重命名'"
      :placeholder="renameModal.type === 'file' ? '输入新的文件名' : '输入新的标题'"
      :initial-value="renameModal.name"
      :saving="renameModal.saving"
      @confirm="handleRenameConfirm"
    />


    <ConfirmDialog
      v-model:visible="finalizeConfirmVisible"
      type="warning"
      :title="uiText('确认定稿')"
      :message="uiText('确认将此工作流标记为“定稿”吗？\n\n定稿后内容将不可修改，且会作为后续生成的重要参考。')"
      :confirm-text="uiText('确认定稿')"
      :cancel-text="uiText('取消')"
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
  chatStream,
  editMessageAndRegenerate,
  type AgentRole,
  type CitationRef,
  updateProject,
  type WorkflowContentFeature,
} from '../services/api'
import type { Project, Session, Message, ContentPart, ToolExecuting, ToolStatusPart, FeatureCitationRefPart } from '../types'
import RenameModal from '../components/common/RenameModal.vue'
import WebCitationTooltip from '../components/common/WebCitationTooltip.vue'
import Toast from '../components/common/Toast.vue'
import { locale, translateText } from '../i18n'
import { formatMessageTimestamp, formatRelativeTime } from '../utils/format'
import { useProjectFeatures } from './projectPage/useProjectFeatures'
import { useProjectSourceFiles } from './projectPage/useProjectSourceFiles'
import { useProjectWorkflows } from './projectPage/useProjectWorkflows'
import { useSourcePreview } from './projectPage/useSourcePreview'


function uiText(text: string): string {
  return translateText(text)
}

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const displayUsername = computed(() => getDisplayUsername() || '用户')
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


const showSessionHistory = ref(false)


const GREETINGS = [
  { zh: '小洛在此，您请讲', en: 'Xiaoluo is here. Go ahead.' },
  { zh: '今天想聊点什么呀？', en: 'What would you like to talk about today?' },
  { zh: '嗨，你来啦', en: 'Hi, you are here.' },
] as const
const randomGreeting = ref<(typeof GREETINGS)[number]>(
  GREETINGS[Math.floor(Math.random() * GREETINGS.length)] ?? GREETINGS[0],
)
const localizedGreeting = computed(() => randomGreeting.value[locale.value])


const inputMessage = ref('')
const enableWebSearch = ref(localStorage.getItem('enableWebSearch') === 'true')
const agentRole = ref<AgentRole>('default')
const isThinking = ref(false)
let thinkingTimer: ReturnType<typeof setTimeout> | null = null
const streamingParts = ref<ContentPart[]>([])
let currentStreamAbort: (() => void) | null = null
const pendingStopTempId = ref<string | null>(null)
const pendingStopSessionId = ref<string | null>(null)
const pendingEditTempId = ref<string | null>(null)
const pendingEditSessionId = ref<string | null>(null)


const editingMessageId = ref<string | null>(null)
const editingContent = ref('')
const chatPanelRef = ref<InstanceType<typeof ChatPanel> | null>(null)
const editTextareaRef = computed<HTMLTextAreaElement[]>(() => chatPanelRef.value?.editTextareaElements ?? [])


watch(enableWebSearch, (val) => {
  localStorage.setItem('enableWebSearch', val ? 'true' : 'false')
})


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
  activeFeature,
  showFeatureDetail,
  toolConfigModal,
  imageGenerationModal,
  imageFilesForGeneration,
  videoGenerationModal,
  videoFilesForGeneration,
  loadFeatures,
  stopFeaturePolling,
  closeToolConfig,
  handleToolConfigConfirm,
  closeImageGenerationModal,
  handleImageGenerationConfirm,
  closeVideoGenerationModal,
  handleVideoGenerationConfirm,
  closeFeatureDetail,
  renameFeatureTitle,
  handleFeatureDetailRename,
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


const toolboxMode = ref<'tools' | 'oneclick'>('oneclick')


const transitionName = ref('slide-left')

watch(() => toolboxMode.value, (newVal, oldVal) => {
  if (newVal === 'tools' && oldVal === 'oneclick') {
    transitionName.value = 'slide-left'
  } else if (newVal === 'oneclick' && oldVal === 'tools') {
    transitionName.value = 'slide-right'
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
  confirmText: '确定',
  cancelText: '取消',
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
    confirmDialog.confirmText = options.confirmText || uiText('确定')
    confirmDialog.cancelText = options.cancelText || uiText('取消')
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


  inputMessage.value = `请你根据已有的文档内容，研究「${keyword}」`
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
    pending_id_sync: false,  // server message 不含此字段,spread 不会覆盖,必须显式清除
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

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  resetTextareaHeight()


  isUserScrolling.value = false
  showScrollToBottom.value = false


  messages.value.push({
    id: Date.now().toString(),
    session_id: currentSession.value.id,
    role: 'user',
    content: userMessage,
    created_at: new Date().toISOString(),
    pending_id_sync: true
  })

  isStreaming.value = true
  isThinking.value = false
  streamingParts.value = []


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

  currentStreamAbort = chatStream(
    currentSession.value.id,
    userMessage,
    fileIds,
    {
      onContent: (content: string) => {

        resetThinkingTimer()

        const lastPart = streamingParts.value[streamingParts.value.length - 1]
        if (lastPart && lastPart.type === 'text') {
          lastPart.content += content
        } else {
          streamingParts.value.push({ type: 'text', content })
        }
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


        const lastPart = streamingParts.value[streamingParts.value.length - 1]
        if (lastPart && lastPart.type === 'reasoning') {
          lastPart.content += content
        } else {
          streamingParts.value.push({ type: 'reasoning', content })
        }
      },
      onReasoningCitationRef: (citation) => {

        const marker = `{{CITE:${citation.display_num}}}`
        const lastPart = streamingParts.value[streamingParts.value.length - 1]
        if (lastPart && lastPart.type === 'reasoning') {
          lastPart.content += marker
        } else {
          streamingParts.value.push({ type: 'reasoning', content: marker })
        }
      },
      onToolExecuting: (tools: ToolExecuting[]) => {

        for (const tool of tools) {
          streamingParts.value.push({
            type: 'tool_status',
            display: tool.display
          } as ToolStatusPart)


          if (tool.name === 'create_generation_task') {
            const category = tool.arguments?.category

            loadWorkflows()
            if (category === 'feature') {
              toolboxMode.value = 'tools'
            } else {
              toolboxMode.value = 'oneclick'
            }
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
      },
      onCitations: () => {

      },
      onCompacting: () => {
        streamingParts.value.push({
          type: 'tool_status',
          display: '正在压缩对话历史...'
        })
      },
      onCompactDone: () => {

        streamingParts.value = streamingParts.value.filter(
          p => !(p.type === 'tool_status' && p.display === '正在压缩对话历史...')
        )
        streamingParts.value.push({
          type: 'text',
          content: '\n\n── 对话历史已压缩 ──\n\n'
        })
      },
      onCompactFailed: (message: string) => {
        streamingParts.value = streamingParts.value.filter(
          p => !(p.type === 'tool_status' && p.display === '正在压缩对话历史...')
        )
        console.warn('Compact failed:', message)
      },
      onDone: (doneData) => {

        clearThinkingTimer()
        messages.value.push({
          id: Date.now().toString(),
          session_id: currentSession.value!.id,
          role: 'assistant',
          content_parts: [...streamingParts.value],
          created_at: new Date().toISOString(),
          agent_role: doneData.agentRole || agentRole.value,
          pending_id_sync: true
        })
        streamingParts.value = []
        isStreaming.value = false
        currentStreamAbort = null


        if (doneData.sessionUpdated?.title && currentSession.value) {
          if (doneData.sessionUpdated.title !== currentSession.value.title) {
            currentSession.value.title = doneData.sessionUpdated.title

            const idx = sessions.value.findIndex(s => s.id === currentSession.value!.id)
            if (idx !== -1 && sessions.value[idx]) {
              sessions.value[idx]!.title = doneData.sessionUpdated.title
            }
          }
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
    enableWebSearch.value,
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
    showCopyToast('已复制为纯文本')
  } catch (err) {
    console.error('复制失败:', err)
    showCopyToast('复制失败')
  }
}

async function copyMessageAsMarkdown(msg: Message) {
  const markdown = getMessageTextContent(msg)

  try {
    await copyTextToClipboard(markdown)
    showCopyToast('已复制为 Markdown')
  } catch (err) {
    console.error('复制失败:', err)
    showCopyToast('复制失败')
  }
}

async function copyUserMessage(msg: Message) {
  try {
    await copyTextToClipboard(msg.content || '')
    showCopyToast('已复制')
  } catch (err) {
    console.error('复制失败:', err)
    showCopyToast('复制失败')
  }
}

function startEditMessage(msg: Message) {
  if (isStreaming.value) return

  if (isTempMessageId(msg.id) || msg.pending_id_sync) {
    showToast('网络同步中，请稍后再试', 'warning')
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
    showToast('消息同步中，请刷新页面后重试', 'error')
    isStreaming.value = false
    isThinking.value = false
    editingMessageId.value = msg.id
    editingContent.value = newContent
    return
  }

  currentStreamAbort = editMessageAndRegenerate(
    currentSession.value.id,
    targetMessage.id,
    newContent,
    selectedFileIds.value.length > 0 ? selectedFileIds.value : undefined,
    {
      onContent: (content: string) => {
        clearLocalThinkingTimer()
        startLocalThinkingTimer()
        const lastPart = streamingParts.value[streamingParts.value.length - 1]
        if (lastPart && lastPart.type === 'text') {
          lastPart.content += content
        } else {
          streamingParts.value.push({ type: 'text', content })
        }
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
        const lastPart = streamingParts.value[streamingParts.value.length - 1]
        if (lastPart && lastPart.type === 'reasoning') {
          lastPart.content += content
        } else {
          streamingParts.value.push({ type: 'reasoning', content })
        }
      },
      onReasoningCitationRef: (citation) => {
        const marker = `{{CITE:${citation.display_num}}}`
        const lastPart = streamingParts.value[streamingParts.value.length - 1]
        if (lastPart && lastPart.type === 'reasoning') {
          lastPart.content += marker
        } else {
          streamingParts.value.push({ type: 'reasoning', content: marker })
        }
      },
      onToolExecuting: (tools) => {
        for (const tool of tools) {
          streamingParts.value.push({
            type: 'tool_status',
            display: tool.display
          } as any)

          if (tool.name === 'create_generation_task') {
            const category = tool.arguments?.category
            loadWorkflows()
            if (category === 'feature') {
              toolboxMode.value = 'tools'
            } else {
              toolboxMode.value = 'oneclick'
            }
          }
        }
      },
      onDone: (doneData) => {
        clearLocalThinkingTimer()
        const tempId = Date.now().toString()
        messages.value.push({
          id: tempId,
          session_id: currentSession.value!.id,
          role: 'assistant',
          content_parts: [...streamingParts.value],
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

        const lastUser = messages.value.slice().reverse().find(m => m.role === 'user')
        if (lastUser && isTempMessageId(lastUser.id)) {
          syncEditMessageIds()
        }

        syncAllPendingMessageIds()
      },
      onMessageIds: (userMessageId: string, assistantMessageId: string) => {
        if (targetMessage) {
          targetMessage.id = userMessageId
          targetMessage.pending_id_sync = false  // 清除可能残留的同步标记,否则下次再编辑该消息会被 startEditMessage 拦截
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
    enableWebSearch.value,
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
    showToast('消息同步中，请刷新页面后重试', 'error')
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
        const lastPart = streamingParts.value[streamingParts.value.length - 1]
        if (lastPart && lastPart.type === 'text') {
          lastPart.content += content
        } else {
          streamingParts.value.push({ type: 'text', content })
        }
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
        const lastPart = streamingParts.value[streamingParts.value.length - 1]
        if (lastPart && lastPart.type === 'reasoning') {
          lastPart.content += content
        } else {
          streamingParts.value.push({ type: 'reasoning', content })
        }
      },
      onReasoningCitationRef: (citation) => {
        const marker = `{{CITE:${citation.display_num}}}`
        const lastPart = streamingParts.value[streamingParts.value.length - 1]
        if (lastPart && lastPart.type === 'reasoning') {
          lastPart.content += marker
        } else {
          streamingParts.value.push({ type: 'reasoning', content: marker })
        }
      },
      onToolExecuting: (tools) => {
        for (const tool of tools) {
          streamingParts.value.push({
            type: 'tool_status',
            display: tool.display
          } as any)

          if (tool.name === 'create_generation_task') {
            const category = tool.arguments?.category
            loadWorkflows()
            if (category === 'feature') {
              toolboxMode.value = 'tools'
            } else {
              toolboxMode.value = 'oneclick'
            }
          }
        }
      },
      onDone: (doneData) => {
        clearLocalThinkingTimer()
        messages.value.push({
          id: Date.now().toString(),
          session_id: currentSession.value!.id,
          role: 'assistant',
          content_parts: [...streamingParts.value],
          created_at: new Date().toISOString(),
          agent_role: doneData.agentRole || agentRole.value,
          pending_id_sync: true
        })
        streamingParts.value = []
        isStreaming.value = false
        isThinking.value = false
        currentStreamAbort = null
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

        syncAllPendingMessageIds()
      },
      onMessageIds: (userMessageId: string, assistantMessageId: string) => {
        if (userMessage) {
          userMessage.id = userMessageId
          userMessage.pending_id_sync = false  // 清除可能残留的同步标记,否则下次再编辑该消息会被 startEditMessage 拦截
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
    enableWebSearch.value,
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
  const displayTitle = title || '新对话'
  const confirmed = await showConfirm({
    title: '删除对话',
    message: `确定要删除"${displayTitle}"吗？此操作无法撤销。`,
    type: 'danger',
    confirmText: '删除',
    cancelText: '取消'
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
