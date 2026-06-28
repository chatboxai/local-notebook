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


      <div v-if="rightPanelCollapsed" class="collapsed-sidebar right">
        <div class="collapsed-icon-btn" @click="rightPanelCollapsed = false" title="展开工具箱面板">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/>
            <path d="M13 7h4v10h-4z" opacity="0.5"/>
          </svg>
        </div>
        <div class="collapsed-icon-btn disabled" title="音频概览 (开发中)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
          </svg>
        </div>
        <div class="collapsed-icon-btn disabled" title="视频概览 (开发中)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z" />
          </svg>
        </div>
        <div class="collapsed-icon-btn disabled" title="思维导图 (开发中)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M22 11V3h-7v3H9V3H2v8h7V8h2v10h4v3h7v-8h-7v3h-2V8h2v3h7zM7 9H4V5h3v4zm10 6h3v4h-3v-4zm0-10h3v4h-3V5z" />
          </svg>
        </div>
        <div class="collapsed-icon-btn disabled" title="报告 (开发中)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
          </svg>
        </div>
        <div class="collapsed-icon-btn disabled" title="闪卡 (开发中)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
          </svg>
        </div>
        <div class="collapsed-icon-btn disabled" title="测验 (开发中)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H7v-2h5v2zm5-4H7v-2h10v2zm0-4H7V7h10v2z" />
          </svg>
        </div>
        <div class="collapsed-icon-btn disabled" title="时间线 (开发中)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z" />
          </svg>
        </div>
        <div class="collapsed-icon-btn disabled" title="摘要 (开发中)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-4 6h-4v2h4v2h-4v2h4v2H9V7h6v2z" />
          </svg>
        </div>
        <div class="collapsed-icon-btn disabled" title="要点 (开发中)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
          </svg>
        </div>
        <div class="collapsed-icon-btn disabled" title="笔记 (开发中)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
          </svg>
        </div>
      </div>


      <aside
        class="studio-panel"
        :class="{ collapsed: rightPanelCollapsed, 'detail-mode': showFeatureDetail || showWorkflowDetail }"
        :style="{
          width: rightPanelCollapsed ? '0px' : rightPanelWidth + 'px',
          maxWidth: (showFeatureDetail || showWorkflowDetail) ? '900px' : '600px'
        }"
      >

        <WorkflowDetailPanel
          v-if="showWorkflowDetail && currentWorkflow"
          :key="currentWorkflow.id"
          :workflow="currentWorkflow"
          :features="workflowFeatures"
          :active-citation-num="activeWorkflowCitationNum"
          :active-feature-id="activeWorkflowFeatureId"
          :edit-mode="workflowEditMode"
          :editing-step-index="editingStepIndex"
          :editing-block-index="editingWorkflowBlockIndex"
          :block-diff-data="workflowBlockDiffData"
          :edit-messages="workflowEditMessages"
          :is-edit-streaming="isWorkflowEditStreaming"
          :edit-streaming-parts="workflowEditStreamingParts"
          :edit-active-citation-num="workflowEditActiveCitationNum"
          :edit-sessions="workflowEditSessions"
          :edit-session-detail="workflowEditSessionDetail"
          :is-loading-edit-history="isLoadingWorkflowEditHistory"
          :is-loading-edit-detail="isLoadingWorkflowEditDetail"
          :edit-current-session-title="workflowEditCurrentSessionTitle"
          @close="closeWorkflowDetail"
          @cancel="handleCancelWorkflow"
          @update-title="handleWorkflowTitleUpdate"
          @citation-click="handleWorkflowCitationClick"
          @clear-citation="clearWorkflowCitation"
          @enter-edit="enterWorkflowEditMode"
          @exit-edit="exitWorkflowEditMode"
          @send-edit-message="handleSendWorkflowEditMessage"
          @edit-citation-click="handleWorkflowEditCitationClick"
          @clear-diff="clearWorkflowBlockDiff"
          @edit-new-session="handleWorkflowEditNewSession"
          @edit-load-sessions="handleWorkflowEditLoadSessions"
          @edit-load-session-detail="handleWorkflowEditLoadSessionDetail"
          @edit-continue-session="handleWorkflowEditContinueSession"
          @edit-change-click="handleWorkflowEditChangeClick"
          @regenerate-step="handleWorkflowStepRegenerate"
          @show-toast="showToast"
        />


        <FeatureDetailPanel
          v-else-if="showFeatureDetail && activeFeature"
          :feature="activeFeature"
          :active-citation-num="activeFeatureCitationNum"
          :editing-block-index="editingBlockIndex"
          :block-diff-data="blockDiffData"
          :edit-mode="featureEditMode"
          :edit-messages="editMessages"
          :is-edit-streaming="isEditStreaming"
          :edit-streaming-parts="editStreamingParts"
          :edit-active-citation-num="featureEditActiveCitationNum"
          :edit-sessions="featureEditSessions"
          :edit-session-detail="featureEditSessionDetail"
          :is-loading-edit-history="isLoadingFeatureEditHistory"
          :is-loading-edit-detail="isLoadingFeatureEditDetail"
          :edit-current-session-title="featureEditCurrentSessionTitle"
          @close="closeFeatureDetail"
          @citation-click="handleFeatureCitationClick"
          @edit-citation-click="handleEditCitationClick"
          @clear-citation="clearFeatureCitation"
          @enter-edit="enterFeatureEditMode"
          @exit-edit="exitFeatureEditMode"
          @rename="handleFeatureDetailRename"
          @send-edit-message="handleSendEditMessage"
          @clear-diff="clearBlockDiff"
          @edit-new-session="handleFeatureEditNewSession"
          @edit-load-sessions="handleFeatureEditLoadSessions"
          @edit-load-session-detail="handleFeatureEditLoadSessionDetail"
          @edit-continue-session="handleFeatureEditContinueSession"
          @edit-change-click="handleFeatureEditChangeClick"
        />


        <template v-else>
          <div class="panel-header">
            <div class="panel-title-wrapper">
              <span
                class="panel-title clickable"
                :class="{ active: toolboxMode === 'tools' }"
                @click="toolboxMode = 'tools'"
              >快捷工具</span>
              <span class="panel-title-divider">/</span>
              <span
                class="panel-title clickable"
                :class="{ active: toolboxMode === 'oneclick' }"
                @click="toolboxMode = 'oneclick'"
              >智能分析</span>
            </div>
            <button class="panel-toggle-btn" @click="rightPanelCollapsed = !rightPanelCollapsed" title="收起面板">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/>
                <path d="M13 7h4v10h-4z" opacity="0.5"/>
              </svg>
            </button>
          </div>


          <div class="studio-content-wrapper">
            <Transition :name="transitionName">

              <div v-if="toolboxMode === 'tools'" class="studio-content" key="tools">

                <div class="studio-tools-fixed">
                  <div class="tool-grid oneclick">
                    <div class="tool-card tool-card--cyan disabled" title="功能开发中">
                      <div class="tool-card-icon">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                      </div>
                      <span class="tool-card-title">智能提取</span>
                    </div>
                    <div class="tool-card tool-card--amber disabled" title="功能开发中">
                      <div class="tool-card-icon">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
                      </div>
                      <span class="tool-card-title">内容分析</span>
                    </div>
                    <div class="tool-card tool-card--indigo disabled" title="功能开发中">
                      <div class="tool-card-icon">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
                      </div>
                      <span class="tool-card-title">数据洞察</span>
                    </div>
                  </div>
                </div>

                <div class="studio-results-scroll">
                  <div class="queue-empty">
                    <p>功能开发中</p>
                  </div>
                </div>
              </div>


              <div v-else class="studio-content" key="oneclick">

                <div class="studio-tools-fixed">
                  <div class="tool-grid oneclick">
                    <div class="tool-card tool-card--blue" :class="{ disabled: !hasReadyFiles }" :title="hasReadyFiles ? uiText('快速掌握材料主线与重点') : uiText('请先上传并处理文件')" @click="openWorkflowConfig('quick_read')">
                      <div class="tool-card-icon">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M4 4h16v2H4V4zm0 4h10v2H4V8zm0 4h16v2H4v-2zm0 4h10v2H4v-2z"/></svg>
                      </div>
                      <span class="tool-card-title">{{ uiText('内容速读') }}</span>
                    </div>
                    <div class="tool-card tool-card--indigo" :class="{ disabled: !hasReadyFiles }" :title="hasReadyFiles ? uiText('系统拆解材料中的关键逻辑') : uiText('请先上传并处理文件')" @click="openWorkflowConfig('deep_dive')">
                      <div class="tool-card-icon">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M9 3h6l1 2h4a1 1 0 0 1 1 1v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a1 1 0 0 1 1-1h4l1-2zm1.24 2-.5 1H5v13h14V7h-4.74l-.5-1h-3.52zM7 10h10v2H7v-2zm0 4h7v2H7v-2z"/></svg>
                      </div>
                      <span class="tool-card-title">{{ uiText('核心详解') }}</span>
                    </div>
                    <div class="tool-card tool-card--custom" :class="{ disabled: !hasReadyFiles }" :title="hasReadyFiles ? uiText('完全按你的要求规划和生成') : uiText('请先上传并处理文件')" @click="openWorkflowConfig('custom')">
                      <div class="tool-card-icon">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M4 21v-7"/>
                          <path d="M4 10V3"/>
                          <path d="M12 21v-9"/>
                          <path d="M12 8V3"/>
                          <path d="M20 21v-5"/>
                          <path d="M20 12V3"/>
                          <path d="M2 14h4"/>
                          <path d="M10 8h4"/>
                          <path d="M18 16h4"/>
                        </svg>
                      </div>
                      <span class="tool-card-title">{{ uiText('自定义工作流') }}</span>
                    </div>
                  </div>
                </div>


            <div class="studio-results-scroll">
              <div class="oneclick-queue">
                <div class="queue-header">
                  <span class="queue-title">{{ uiText('生成结果') }}</span>
                </div>

                <div v-if="workflows.length === 0" class="queue-empty">
                  <p>{{ hasReadyFiles ? uiText('点击上方按钮生成报告') : uiText('上传来源后即可生成报告') }}</p>
                </div>

                <div v-else class="workflow-list">
                  <div
                    v-for="wf in workflows"
                    :key="wf.id"
                    class="workflow-item"
                    @click="viewWorkflowDetail(wf.id)"
                  >
                    <div class="workflow-item-icon icon-default" :class="getWorkflowSourceClass(wf)">
                      <svg v-if="getWorkflowPresetKey(wf) === 'quick_read'" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                        <path d="M4 4h16v2H4V4zm0 4h10v2H4V8zm0 4h16v2H4v-2zm0 4h10v2H4v-2z"/>
                      </svg>
                      <svg v-else-if="getWorkflowPresetKey(wf) === 'deep_dive'" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                        <path d="M9 3h6l1 2h4a1 1 0 0 1 1 1v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a1 1 0 0 1 1-1h4l1-2zm1.24 2-.5 1H5v13h14V7h-4.74l-.5-1h-3.52zM7 10h10v2H7v-2zm0 4h7v2H7v-2z"/>
                      </svg>
                      <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 21v-7"/>
                        <path d="M4 10V3"/>
                        <path d="M12 21v-9"/>
                        <path d="M12 8V3"/>
                        <path d="M20 21v-5"/>
                        <path d="M20 12V3"/>
                        <path d="M2 14h4"/>
                        <path d="M10 8h4"/>
                        <path d="M18 16h4"/>
                      </svg>
                    </div>
                    <div class="workflow-item-info">
                      <div class="workflow-item-title-row">
                        <div class="workflow-item-name">{{ getWorkflowDisplayName(wf) }}</div>
                        <span class="workflow-source-chip" :class="getWorkflowSourceClass(wf)">
                          {{ getWorkflowSourceLabel(wf) }}
                        </span>
                      </div>
                      <div class="workflow-item-status">
                        <span class="workflow-status-badge" :class="getWorkflowStatusClass(wf.status)">
                          {{ getWorkflowDisplayStatusText(wf) }}
                        </span>
                        <span v-if="isWorkflowActiveStatus(wf.status)" class="workflow-item-time">
                          {{ formatWorkflowProgress(wf) }}
                        </span>
                        <span v-if="isWorkflowActiveStatus(wf.status) && wf.created_at" class="workflow-item-time">
                          {{ formatWorkflowElapsed(wf.created_at) }}
                        </span>
                        <span v-else-if="wf.created_at" class="workflow-item-time">{{ formatTime(wf.created_at) }}</span>
                      </div>
                    </div>
                    <button
                      v-if="isWorkflowCancellable(wf.status)"
                      class="workflow-stop-btn"
                      @click.stop="handleCancelWorkflow(wf.id)"
                      :title="uiText('停止生成')"
                    >
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                        <path d="M6 6h12v12H6z"/>
                      </svg>
                    </button>
                    <button v-else class="workflow-delete-btn" @click.stop="handleDeleteWorkflow(wf.id)" :title="uiText('删除')">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
              </div>
            </Transition>
          </div>
        </template>

      </aside>
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
import ImageGenerationModal, { type ImageFile } from '../components/common/ImageGenerationModal.vue'
import VideoGenerationModal, { type VideoFile, type VideoGenerationMode, type VideoGenerationConfig } from '../components/common/VideoGenerationModal.vue'
import FeatureDetailPanel from '../components/project/FeatureDetailPanel.vue'
import WorkflowDetailPanel from '../components/project/WorkflowDetailPanel.vue'
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


  generateFeature,
  getFeature,
  getProjectFeatures,
  getFeaturesStatusBatch,
  updateFeature,
  deleteFeature,
  featureEditChat,
  workflowEditChat,
  getFeatureEditSessions,
  getFeatureEditSessionDetail,
  createWorkflow,
  getProjectWorkflows,
  renameWorkflow,
  cancelWorkflow,
  deleteWorkflow,
  finalizeWorkflow,
  getWorkflowDetail,
  getWorkflowContent,
  getWorkflowsStatusBatch,
  getWorkflowStepConfig,
  regenerateWorkflowStep,
  getWorkflowEditSessions,
  getWorkflowEditSessionDetail,
  type FeatureListItem,
  type WorkflowListItem,
  type WorkflowDetail,
  type WorkflowCitation,
  type WorkflowContentFeature,
  type EditSession,
  type EditSessionMessage,
  type FeatureEditCitationRef,
  type FeatureEditHistoryMessage,
} from '../services/api'
import type { Project, Session, Message, ContentPart, ToolExecuting, ToolStatusPart, Feature, FeatureCitationRefPart } from '../types'
import RenameModal from '../components/common/RenameModal.vue'
import WebCitationTooltip from '../components/common/WebCitationTooltip.vue'
import Toast from '../components/common/Toast.vue'
import { getModelOutputLanguage, locale, translateText } from '../i18n'
import { formatMessageTimestamp, formatRelativeTime } from '../utils/format'
import {
  IMAGE_GENERATION_FILE_TYPES,
  VIDEO_GENERATION_FILE_TYPES,
} from './projectPage/fileHelpers'
import { IMAGE_GENERATION_TYPES, TOOL_TYPES, VIDEO_GENERATION_TYPES } from './projectPage/toolTypes'
import { useProjectSourceFiles } from './projectPage/useProjectSourceFiles'
import { useSourcePreview } from './projectPage/useSourcePreview'
import {
  buildWorkflowPrompt,
  formatWorkflowElapsed as formatWorkflowElapsedText,
  formatWorkflowGeneratingMessage,
  formatWorkflowProgress,
  formatWorkflowStepRegeneratedMessage,
  getWorkflowDisplayName,
  getWorkflowDisplayStatusText,
  getWorkflowPresetKey,
  getWorkflowPresetPrompt,
  getWorkflowSourceClass,
  getWorkflowSourceLabel,
  getWorkflowStatusClass,
  getWorkflowStatusText,
  hasEditableWorkflowTitle,
  isWorkflowActiveStatus,
  isWorkflowCancellable,
  WORKFLOW_PRESETS,
  type WorkflowPresetKey,
} from './projectPage/workflowHelpers'


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


const features = ref<FeatureListItem[]>([])

const activeFeature = ref<Feature | null>(null)

const showFeatureDetail = ref(false)

const featureMenuId = ref<string | null>(null)


const featureEditMode = ref(false)
const editingFeature = ref<Feature | null>(null)


type EditMessageContentPart = { type: 'text'; content: string } | { type: 'citation_ref'; display_num: number; citation_id: string; file_name?: string; segment_id?: string; summary?: string; citation_type?: 'audio' | 'image' | 'web'; time_start?: number; time_end?: number; time_range?: string }
interface EditMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  content_parts?: EditMessageContentPart[]
  tool_executing?: Array<{ name: string; display: string }>
  changes?: Array<{
    block_index: number
    old_content: string
    new_content: string
    success: boolean
    error_message?: string | null
    is_outdated?: boolean
  }>
}
const editMessages = ref<EditMessage[]>([])
const isEditStreaming = ref(false)
const editStreamingParts = ref<ContentPart[]>([])
const editingBlockIndex = ref<number | null>(null)
const featureEditSessionId = ref<string | null>(null)

const featureEditSessions = ref<EditSession[]>([])
const featureEditSessionDetail = ref<{ session: EditSession; messages: EditSessionMessage[] } | null>(null)
const isLoadingFeatureEditHistory = ref(false)
const isLoadingFeatureEditDetail = ref(false)
const featureEditCurrentSessionTitle = ref('')

const blockDiffData = ref<{
  blockIndex: number
  oldContentParts: Array<{ type: 'text' | 'citation_ref'; content?: string; display_num?: number; citation_id?: string; file_name?: string; segment_id?: string; summary?: string }>
  newContentParts: Array<{ type: 'text' | 'citation_ref'; content?: string; display_num?: number; citation_id?: string; file_name?: string; segment_id?: string; summary?: string }>
} | null>(null)


const workflowEditMode = ref(false)
const editingWorkflow = ref<WorkflowDetail | null>(null)
const workflowEditMessages = ref<EditMessage[]>([])
const isWorkflowEditStreaming = ref(false)
const workflowEditStreamingParts = ref<ContentPart[]>([])
const workflowEditSessionId = ref<string | null>(null)

const workflowEditSessions = ref<EditSession[]>([])
const workflowEditSessionDetail = ref<{ session: EditSession; messages: EditSessionMessage[] } | null>(null)
const isLoadingWorkflowEditHistory = ref(false)
const isLoadingWorkflowEditDetail = ref(false)
const workflowEditCurrentSessionTitle = ref('')
const workflowEditCitations = ref<Record<string, WorkflowCitation>>({})
const editingStepIndex = ref<number | null>(null)
const editingWorkflowBlockIndex = ref<number | null>(null)

const workflowBlockDiffData = ref<{
  stepIndex: number
  blockIndex: number
  oldContentParts: Array<{ type: 'text' | 'citation_ref'; content?: string; display_num?: number; citation_id?: string; file_name?: string; segment_id?: string; summary?: string }>
  newContentParts: Array<{ type: 'text' | 'citation_ref'; content?: string; display_num?: number; citation_id?: string; file_name?: string; segment_id?: string; summary?: string }>
} | null>(null)


const renameModal = reactive({
  visible: false,
  type: 'file' as 'file' | 'feature' | 'workflow',
  id: '',
  name: '',
  saving: false
})


const toolConfigModal = reactive({
  visible: false,
  toolType: '',
  toolTitle: '',
  prompt: '',
  hidePrompt: false
})


const imageGenerationModal = reactive({
  visible: false,
  mode: 'text_to_image' as 'text_to_image' | 'reference_to_image'
})


const imageFilesForGeneration = computed<ImageFile[]>(() =>
  files.value
    .filter(f => f.status === 'ready' && IMAGE_GENERATION_FILE_TYPES.includes(f.file_type?.toLowerCase() || ''))
    .map(f => ({
      id: f.id,
      file_name: f.file_name,
      file_type: f.file_type,
      status: f.status
    }))
)


const videoGenerationModal = reactive({
  visible: false,
  mode: 'text_to_video' as VideoGenerationMode
})


const videoFilesForGeneration = computed<VideoFile[]>(() =>
  files.value
    .filter(f => f.status === 'ready' && VIDEO_GENERATION_FILE_TYPES.includes(f.file_type?.toLowerCase() || ''))
    .map(f => ({
      id: f.id,
      file_name: f.file_name,
      file_type: f.file_type,
      status: f.status
    }))
)


const pollingFeatureIds = ref<Set<string>>(new Set())
let featurePollingTimer: ReturnType<typeof setInterval> | null = null


const processingToolTypes = computed(() =>
  features.value
    .filter(f => f.status === 'pending' || f.status === 'processing')
    .map(f => f.feature_type)
)


async function handleFeatureCitationClick(part: FeatureCitationRefPart) {

  activeChatCitationNum.value = null
  activeWorkflowCitationNum.value = null
  featureEditActiveCitationNum.value = null
  workflowEditActiveCitationNum.value = null
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


async function handleEditCitationClick(citationId: string, displayNum: number, segmentId: string) {
  if (!segmentId) {
    console.warn('Edit citation segment_id not provided:', citationId, displayNum)
    return
  }


  activeChatCitationNum.value = null
  activeFeatureCitationNum.value = null
  activeWorkflowCitationNum.value = null
  workflowEditActiveCitationNum.value = null
  featureEditActiveCitationNum.value = displayNum


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
  activeWorkflowCitationNum.value = null
  activeWorkflowFeatureId.value = null
  clearSourceHighlights()
}


const activeChatCitationNum = ref<number | null>(null)
const activeFeatureCitationNum = ref<number | null>(null)
const activeWorkflowCitationNum = ref<number | null>(null)
const workflowMenuId = ref<string | null>(null)


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

const activeWorkflowFeatureId = ref<string | null>(null)
const featureEditActiveCitationNum = ref<number | null>(null)
const workflowEditActiveCitationNum = ref<number | null>(null)


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


let pollErrorCount = 0
const MAX_POLL_ERRORS = 5
let workflowElapsedTimer: ReturnType<typeof setInterval> | null = null


const REPORT_MIN_WIDTH = 700
const rightPanelWidthBeforeReport = ref<number | null>(null)


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

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    workflowElapsedTick.value = Date.now()

    const processingWorkflow = workflows.value.find(wf => isWorkflowActiveStatus(wf.status))
    if (processingWorkflow && !workflowPollingTimer.value) {
      workflowLoading.value = true

    }
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
        featureEditActiveCitationNum.value = null
        workflowEditActiveCitationNum.value = null
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
  featureEditActiveCitationNum.value = null
  workflowEditActiveCitationNum.value = null

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
      await renameWorkflow(renameModal.id, newName)
      const workflow = workflows.value.find(w => w.id === renameModal.id)
      if (workflow) workflow.title = newName
      if (currentWorkflow.value?.id === renameModal.id) {
        currentWorkflow.value.title = newName
      }
    } else {
      await updateFeature(renameModal.id, { title: newName })
      const feature = features.value.find(f => f.id === renameModal.id)
      if (feature) feature.title = newName
      if (activeFeature.value?.id === renameModal.id) {
        activeFeature.value.title = newName
      }
    }
    closeRenameModal()
  } catch (error) {
    console.error('Failed to rename:', error)
    renameModal.saving = false
  }
}

function handleRenameFeature(feature: FeatureListItem) {
  openRenameModal('feature', feature.id, feature.title || '')
}

async function handleFeatureDetailRename(newTitle: string) {
  if (!activeFeature.value) return

  try {
    const id = activeFeature.value.id
    await updateFeature(id, { title: newTitle })

    if (activeFeature.value) activeFeature.value.title = newTitle

    const feature = features.value.find(f => f.id === id)
    if (feature) feature.title = newTitle

    showToast('重命名成功', 'success')
  } catch (error) {
    console.error('Failed to rename feature:', error)
    showToast('重命名失败', 'error')
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

async function loadFeatures() {
}

function startFeaturePolling() {
  if (featurePollingTimer) return

  featurePollingTimer = setInterval(async () => {
    if (pollingFeatureIds.value.size === 0) {
      stopFeaturePolling()
      return
    }

    try {
      const featureIds = Array.from(pollingFeatureIds.value)
      const result = await getFeaturesStatusBatch(featureIds)

      let hasCompleted = false

      for (const [featureId, statusInfo] of Object.entries(result.features)) {
        const index = features.value.findIndex(f => f.id === featureId)
        if (index !== -1) {
          const existingFeature = features.value[index]!
          features.value[index] = {
            ...existingFeature,
            status: statusInfo.status as FeatureListItem['status'],
            error_message: statusInfo.error_message,
            display_name: statusInfo.display_name ?? existingFeature.display_name,
            prompt: statusInfo.prompt ?? existingFeature.prompt,
            title: statusInfo.title ?? existingFeature.title
          }
        }

        if (statusInfo.status === 'completed' || statusInfo.status === 'failed') {
          pollingFeatureIds.value.delete(featureId)
          hasCompleted = true
        }
      }

      if (hasCompleted) {
        const { features: featureList } = await getProjectFeatures(projectId)
        features.value = featureList
      }

      if (pollingFeatureIds.value.size === 0) {
        stopFeaturePolling()
      }
    } catch (error) {
      console.error('Failed to poll features:', error)
    }
  }, 3000)
}

function stopFeaturePolling() {
  if (featurePollingTimer) {
    clearInterval(featurePollingTimer)
    featurePollingTimer = null
  }
}

function openToolConfig(tool: typeof TOOL_TYPES[0]) {
  if (!hasReadyFiles.value) return

  if (IMAGE_GENERATION_TYPES.includes(tool.type)) {
    imageGenerationModal.mode = tool.type as 'text_to_image' | 'reference_to_image'
    imageGenerationModal.visible = true
    return
  }

  if (VIDEO_GENERATION_TYPES.includes(tool.type)) {
    videoGenerationModal.mode = tool.type as VideoGenerationMode
    videoGenerationModal.visible = true
    return
  }

  toolConfigModal.toolType = tool.type
  toolConfigModal.toolTitle = tool.title
  toolConfigModal.prompt = ''
  toolConfigModal.hidePrompt = false
  toolConfigModal.visible = true
}

function closeToolConfig() {
  toolConfigModal.visible = false
  toolConfigModal.toolType = ''
  toolConfigModal.toolTitle = ''
  toolConfigModal.prompt = ''
}

async function handleToolConfigConfirm(toolType: string, prompt: string, fileIds: string[]) {
  closeToolConfig()
  await handleToolClick(toolType, prompt, fileIds)
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

    // 若有进行中的任务且当前没有轮询，则开始轮询
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

    if (rightPanelWidth.value < REPORT_MIN_WIDTH) {
      rightPanelWidthBeforeReport.value = rightPanelWidth.value
      rightPanelWidth.value = REPORT_MIN_WIDTH
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

async function handleWorkflowCitationClick(part: FeatureCitationRefPart, feature: WorkflowContentFeature) {
  activeChatCitationNum.value = null
  activeFeatureCitationNum.value = null
  featureEditActiveCitationNum.value = null
  workflowEditActiveCitationNum.value = null
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

const finalizeConfirmVisible = ref(false)
const workflowToFinalizeId = ref<string | null>(null)

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

async function handleWorkflowTitleUpdate(id: string, title: string) {
  try {
    await renameWorkflow(id, title)
    const workflow = workflows.value.find(w => w.id === id)
    if (workflow) {
      workflow.title = title
    }
    if (currentWorkflow.value?.id === id) {
      currentWorkflow.value.title = title
    }
  } catch (error) {
    console.error('Failed to update workflow title:', error)
    showToast(uiText('重命名失败'), 'error')
  }
}

function formatWorkflowElapsed(isoString: string): string {
  return formatWorkflowElapsedText(isoString, workflowElapsedTick.value)
}

function formatTime(isoString: string): string {
  return formatRelativeTime(isoString)
}

function formatMessageTime(isoString: string): string {
  return formatMessageTimestamp(isoString)
}

function closeImageGenerationModal() {
  imageGenerationModal.visible = false
}

async function handleImageGenerationConfirm(config: { prompt: string; fileIds: string[]; aspectRatio: string }) {
  const toolType = imageGenerationModal.mode
  closeImageGenerationModal()

  try {
    const { feature_id } = await generateFeature(projectId, toolType, {
      prompt: config.prompt,
      file_ids: config.fileIds,
      aspect_ratio: config.aspectRatio
    })

    const toolConfig = TOOL_TYPES.find(t => t.type === toolType)
    features.value.unshift({
      id: feature_id,
      feature_type: toolType,
      display_name: toolConfig?.title || toolType,
      title: null,
      prompt: config.prompt || null,
      status: 'pending',
      error_message: null,
      created_at: new Date().toISOString(),
      started_at: null,
      finished_at: null
    })

    pollingFeatureIds.value.add(feature_id)
    startFeaturePolling()
  } catch (error) {
    console.error('Failed to generate image:', error)
  }
}

function closeVideoGenerationModal() {
  videoGenerationModal.visible = false
}

async function handleVideoGenerationConfirm(mode: VideoGenerationMode, config: VideoGenerationConfig) {
  closeVideoGenerationModal()

  try {
    const { feature_id } = await generateFeature(projectId, mode, {
      prompt: config.prompt,
      file_ids: config.fileIds,
      duration: config.duration,
      aspect_ratio: config.aspectRatio,
      resolution: config.resolution,
      bgm: config.bgm
    })

    const toolConfig = TOOL_TYPES.find(t => t.type === mode)
    features.value.unshift({
      id: feature_id,
      feature_type: mode,
      display_name: toolConfig?.title || mode,
      title: null,
      prompt: config.prompt || null,
      status: 'pending',
      error_message: null,
      created_at: new Date().toISOString(),
      started_at: null,
      finished_at: null
    })

    pollingFeatureIds.value.add(feature_id)
    startFeaturePolling()
  } catch (error) {
    console.error('Failed to generate video:', error)
  }
}

async function handleToolClick(toolType: string, customPrompt?: string, fileIds?: string[]) {
  if (!hasReadyFiles.value) return

  try {
    const readyFileIds = fileIds && fileIds.length > 0 ? fileIds : readyFiles.value.map(f => f.id)

    const { feature_id } = await generateFeature(projectId, toolType, {
      prompt: customPrompt || '',
      file_ids: readyFileIds
    })

    const toolConfig = TOOL_TYPES.find(t => t.type === toolType)
    features.value.unshift({
      id: feature_id,
      feature_type: toolType,
      display_name: toolConfig?.title || toolType,
      title: null,
      prompt: customPrompt || null,
      status: 'pending',
      error_message: null,
      created_at: new Date().toISOString(),
      started_at: null,
      finished_at: null
    })

    pollingFeatureIds.value.add(feature_id)
    startFeaturePolling()
  } catch (error) {
    console.error('Failed to generate feature:', error)
  }
}

async function handleFeatureClick(featureItem: FeatureListItem) {
  if (featureItem.status === 'pending' || featureItem.status === 'processing') {
    return
  }

  if (featureItem.status === 'failed') {
    return
  }

  try {
    const feature = await getFeature(featureItem.id)
    activeFeature.value = feature

    if (rightPanelWidth.value < REPORT_MIN_WIDTH) {
      rightPanelWidthBeforeReport.value = rightPanelWidth.value
      rightPanelWidth.value = REPORT_MIN_WIDTH
    }
    showFeatureDetail.value = true
  } catch (error) {
    console.error('Failed to load feature detail:', error)
  }
}

function closeFeatureDetail() {
  if (featureEditMode.value) {
    exitFeatureEditMode()
  }
  showFeatureDetail.value = false
  activeFeature.value = null
  if (rightPanelWidthBeforeReport.value !== null) {
    rightPanelWidth.value = rightPanelWidthBeforeReport.value
    rightPanelWidthBeforeReport.value = null
  }
}


function clearBlockDiff() {
  blockDiffData.value = null
}

function enterFeatureEditMode() {
  if (!activeFeature.value) return

  featureEditMode.value = true
  editingFeature.value = activeFeature.value
  editMessages.value = []
  isEditStreaming.value = false
  editStreamingParts.value = []
  editingBlockIndex.value = null
  featureEditSessionId.value = null
  blockDiffData.value = null
}

async function exitFeatureEditMode() {
  const featureId = editingFeature.value?.id

  featureEditMode.value = false
  editingFeature.value = null
  editMessages.value = []
  isEditStreaming.value = false
  editStreamingParts.value = []
  editingBlockIndex.value = null
  featureEditSessionId.value = null
  featureEditActiveCitationNum.value = null

  if (featureId && activeFeature.value?.id === featureId) {
    try {
      const updatedFeature = await getFeature(featureId)
      activeFeature.value = updatedFeature
    } catch (error) {
      console.error('Failed to refresh feature after edit:', error)
    }
  }
}

async function handleSendEditMessage(message: string) {
  if (!message || !editingFeature.value || isEditStreaming.value) return

  const collectedChanges: Array<{
    block_index: number
    old_content: string
    new_content: string
    success: boolean
    error_message?: string
  }> = []

  const userMessageId = Date.now().toString()
  editMessages.value.push({
    id: userMessageId,
    role: 'user',
    content: message
  })

  isEditStreaming.value = true
  editStreamingParts.value = []
  editingBlockIndex.value = null

  const assistantMessageId = (Date.now() + 1).toString()
  editMessages.value.push({
    id: assistantMessageId,
    role: 'assistant',
    content: ''
  })

  function getTextFromParts(parts: ContentPart[]): string {
    return parts
      .filter(p => p.type === 'text')
      .map(p => p.content || '')
      .join('')
  }

  try {
    await featureEditChat(
      editingFeature.value.id,
      message,
      {
        onStart: () => {
        },
        onText: (text: string) => {
          const lastPart = editStreamingParts.value[editStreamingParts.value.length - 1]
          if (lastPart && lastPart.type === 'text') {
            lastPart.content = (lastPart.content || '') + text
          } else {
            editStreamingParts.value.push({ type: 'text', content: text })
          }
          const lastMsg = editMessages.value[editMessages.value.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.content = getTextFromParts(editStreamingParts.value)
          }
        },
        onCitationRef: (citation) => {
          editStreamingParts.value.push({
            type: 'citation_ref',
            display_num: citation.display_num,
            file_name: citation.file_name || '',
            segment_id: citation.segment_id || '',
            summary: citation.summary || ''
          } as unknown as ContentPart)
        },
        onToolExecuting: (tools: ToolExecuting[]) => {
          for (const tool of tools) {
            editStreamingParts.value.push({
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
          }
        },
        onEditPreview: (data) => {
          editingBlockIndex.value = data.block_index

          if (data.old_content_parts && data.new_content_parts) {
            blockDiffData.value = {
              blockIndex: data.block_index,
              oldContentParts: data.old_content_parts,
              newContentParts: data.new_content_parts
            }
          }
        },
        onEditApplied: (data) => {
          editingBlockIndex.value = null

          const oldContent = blockDiffData.value?.blockIndex === data.block_index
            ? blockDiffData.value.oldContentParts.map(p => p.type === 'text' ? p.content || '' : `[${p.display_num}]`).join('')
            : ''
          collectedChanges.push({
            block_index: data.block_index,
            old_content: oldContent,
            new_content: data.new_content || '',
            success: data.success,
            error_message: data.error
          })

          if (data.success && data.block && activeFeature.value) {
            activeFeature.value.blocks[data.block_index] = data.block
          } else if (!data.success && data.error) {
            console.error('Edit applied failed:', data.error)
          }
        },
        onDone: (data) => {
          featureEditSessionId.value = data.session_id
          isEditStreaming.value = false
          editStreamingParts.value = []

          const messages = data.history
            .filter(msg => msg.content?.trim() || (msg.content_parts && msg.content_parts.length > 0))
            .map((msg, index) => ({
              id: `history-${Date.now()}-${index}`,
              role: msg.role,
              content: msg.content || '',
              content_parts: msg.content_parts,
              tool_executing: msg.tool_executing,
              changes: undefined as typeof collectedChanges | undefined
            }))

          if (collectedChanges.length > 0) {
            const lastAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant')
            if (lastAssistantMsg) {
              lastAssistantMsg.changes = [...collectedChanges]
            }
          }

          editMessages.value = messages
        },
        onError: (error: string) => {
          console.error('Feature edit error:', error)
          isEditStreaming.value = false
          editStreamingParts.value = []
          const lastMsg = editMessages.value[editMessages.value.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.content = `错误: ${error}`
          }
        }
      },
      featureEditSessionId.value
    )
  } catch (error) {
    console.error('Feature edit chat failed:', error)
    isEditStreaming.value = false
    editStreamingParts.value = []
    const lastMsg = editMessages.value[editMessages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content = `请求失败: ${error instanceof Error ? error.message : '未知错误'}`
    }
  }
}


function handleFeatureEditNewSession() {
  featureEditSessionId.value = null
  editMessages.value = []
  featureEditCurrentSessionTitle.value = ''
}

async function handleFeatureEditLoadSessions() {
  if (!activeFeature.value?.id) return

  isLoadingFeatureEditHistory.value = true
  try {
    const response = await getFeatureEditSessions(activeFeature.value.id)
    featureEditSessions.value = response.sessions
  } catch (error) {
    console.error('Failed to load feature edit sessions:', error)
  } finally {
    isLoadingFeatureEditHistory.value = false
  }
}

async function handleFeatureEditLoadSessionDetail(sessionId: string) {
  if (!activeFeature.value?.id) return

  isLoadingFeatureEditDetail.value = true
  try {
    const response = await getFeatureEditSessionDetail(activeFeature.value.id, sessionId)
    featureEditSessionDetail.value = {
      session: response.session,
      messages: response.messages
    }
  } catch (error) {
    console.error('Failed to load feature edit session detail:', error)
  } finally {
    isLoadingFeatureEditDetail.value = false
  }
}

function handleFeatureEditContinueSession(sessionId: string) {
  if (!featureEditSessionDetail.value) return

  featureEditSessionId.value = sessionId
  editMessages.value = featureEditSessionDetail.value.messages
    .filter(msg => msg.role !== 'tool')
    .map(msg => ({
      id: msg.id,
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
      content_parts: msg.content_parts as EditMessage['content_parts'],
      tool_executing: msg.tool_executing,
      changes: msg.changes
    }))
  const firstUserMsg = featureEditSessionDetail.value.messages.find(m => m.role === 'user')
  featureEditCurrentSessionTitle.value = firstUserMsg?.content.slice(0, 20) || ''
}

function handleFeatureEditChangeClick(change: { block_index: number; old_content: string; new_content: string }) {
  blockDiffData.value = {
    blockIndex: change.block_index,
    oldContentParts: [{ type: 'text' as const, content: change.old_content }],
    newContentParts: [{ type: 'text' as const, content: change.new_content }]
  }
}


function enterWorkflowEditMode() {
  if (!currentWorkflow.value) return

  workflowEditMode.value = true
  editingWorkflow.value = currentWorkflow.value
  workflowEditMessages.value = []
  isWorkflowEditStreaming.value = false
  workflowEditStreamingParts.value = []
  workflowEditSessionId.value = null
  editingStepIndex.value = null
  editingWorkflowBlockIndex.value = null
  workflowBlockDiffData.value = null
}

function exitWorkflowEditMode() {
  workflowEditMode.value = false
  editingWorkflow.value = null
  workflowEditMessages.value = []
  isWorkflowEditStreaming.value = false
  workflowEditStreamingParts.value = []
  workflowEditSessionId.value = null
  editingStepIndex.value = null
  editingWorkflowBlockIndex.value = null
  workflowBlockDiffData.value = null
  workflowEditActiveCitationNum.value = null
}

function clearWorkflowBlockDiff() {
  workflowBlockDiffData.value = null
}

async function handleWorkflowEditCitationClick(citationId: string, displayNum: number, segmentId: string) {
  if (!segmentId) {
    console.warn('Workflow edit citation segment_id not provided:', citationId, displayNum)
    return
  }

  activeChatCitationNum.value = null
  activeFeatureCitationNum.value = null
  activeWorkflowCitationNum.value = null
  featureEditActiveCitationNum.value = null
  workflowEditActiveCitationNum.value = displayNum

  const fileIdFromSegment = segmentId.split('_s_')[0]!

  const file = files.value.find(f => f.id === fileIdFromSegment)

  if (file) {
    await openFilePreview(fileIdFromSegment, segmentId)
  }
}

async function handleSendWorkflowEditMessage(message: string) {
  if (!message || !currentWorkflow.value || isWorkflowEditStreaming.value) return

  const collectedChanges: Array<{
    block_index: number
    old_content: string
    new_content: string
    step_index: number
    step_name: string
    success: boolean
    error_message?: string
  }> = []

  const userMessageId = Date.now().toString()
  workflowEditMessages.value.push({
    id: userMessageId,
    role: 'user',
    content: message
  })

  isWorkflowEditStreaming.value = true
  workflowEditStreamingParts.value = []
  editingStepIndex.value = null
  editingWorkflowBlockIndex.value = null

  const assistantMessageId = (Date.now() + 1).toString()
  workflowEditMessages.value.push({
    id: assistantMessageId,
    role: 'assistant',
    content: ''
  })

  function getTextFromParts(parts: ContentPart[]): string {
    return parts
      .filter(p => p.type === 'text')
      .map(p => p.content || '')
      .join('')
  }

  try {
    await workflowEditChat(
      currentWorkflow.value.id,
      message,
      {
        onStart: () => {
        },
        onText: (text: string) => {
          const lastPart = workflowEditStreamingParts.value[workflowEditStreamingParts.value.length - 1]
          if (lastPart && lastPart.type === 'text') {
            lastPart.content = (lastPart.content || '') + text
          } else {
            workflowEditStreamingParts.value.push({ type: 'text', content: text })
          }
          const lastMsg = workflowEditMessages.value[workflowEditMessages.value.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.content = getTextFromParts(workflowEditStreamingParts.value)
          }
        },
        onCitationRef: (citation: FeatureEditCitationRef) => {
          workflowEditStreamingParts.value.push({
            type: 'citation_ref',
            display_num: citation.display_num,
            file_name: citation.file_name || '',
            segment_id: citation.segment_id || '',
            summary: citation.summary || ''
          } as unknown as ContentPart)
        },
        onToolExecuting: (tools: ToolExecuting[]) => {
          for (const tool of tools) {
            workflowEditStreamingParts.value.push({
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
          }
        },
        onEditPreview: (data: {
          step_index: number
          step_name: string
          block_index: number
          old_content_parts?: Array<{ type: 'text' | 'citation_ref'; content?: string; display_num?: number; citation_id?: string; file_name?: string; segment_id?: string; summary?: string }>
          new_content_parts?: Array<{ type: 'text' | 'citation_ref'; content?: string; display_num?: number; citation_id?: string; file_name?: string; segment_id?: string; summary?: string }>
        }) => {
          editingStepIndex.value = data.step_index
          editingWorkflowBlockIndex.value = data.block_index

          if (data.old_content_parts && data.new_content_parts) {
            workflowBlockDiffData.value = {
              stepIndex: data.step_index,
              blockIndex: data.block_index,
              oldContentParts: data.old_content_parts,
              newContentParts: data.new_content_parts
            }
          }
        },
        onEditApplied: (data: { step_index: number; step_name: string; block_index: number; success: boolean; new_content?: string; block?: any; error?: string }) => {
          editingStepIndex.value = null
          editingWorkflowBlockIndex.value = null

          const oldContent = workflowBlockDiffData.value?.stepIndex === data.step_index && workflowBlockDiffData.value?.blockIndex === data.block_index
            ? workflowBlockDiffData.value.oldContentParts.map(p => p.type === 'text' ? p.content || '' : `[${p.display_num}]`).join('')
            : ''
          collectedChanges.push({
            block_index: data.block_index,
            old_content: oldContent,
            new_content: data.new_content || '',
            step_index: data.step_index,
            step_name: data.step_name,
            success: data.success,
            error_message: data.error
          })

          if (data.success && data.block) {
            const stepIndex = data.step_index
            const feature = workflowFeatures.value.find((_, i) => i === stepIndex - 1)
            if (feature && feature.blocks) {
              feature.blocks[data.block_index] = data.block
            }
          } else if (!data.success && data.error) {
            console.error('Workflow edit applied failed:', data.error)
          }
        },
        onDone: (data) => {
          workflowEditSessionId.value = data.session_id
          isWorkflowEditStreaming.value = false
          workflowEditStreamingParts.value = []

          const messages = data.history
            .filter((msg: FeatureEditHistoryMessage) => msg.content?.trim() || (msg.content_parts && msg.content_parts.length > 0))
            .map((msg: FeatureEditHistoryMessage, index: number) => ({
              id: `history-${Date.now()}-${index}`,
              role: msg.role,
              content: msg.content || '',
              content_parts: msg.content_parts,
              tool_executing: msg.tool_executing,
              changes: undefined as typeof collectedChanges | undefined
            }))

          if (collectedChanges.length > 0) {
            const lastAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant')
            if (lastAssistantMsg) {
              lastAssistantMsg.changes = [...collectedChanges]
            }
          }

          workflowEditMessages.value = messages

          if (data.citations) {
            workflowEditCitations.value = data.citations
          }
        },
        onError: (error: string) => {
          console.error('Workflow edit error:', error)
          isWorkflowEditStreaming.value = false
          workflowEditStreamingParts.value = []
          const lastMsg = workflowEditMessages.value[workflowEditMessages.value.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.content = `错误: ${error}`
          }
        }
      },
      workflowEditSessionId.value
    )
  } catch (error) {
    console.error('Workflow edit chat failed:', error)
    isWorkflowEditStreaming.value = false
    workflowEditStreamingParts.value = []
    const lastMsg = workflowEditMessages.value[workflowEditMessages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content = `请求失败: ${error instanceof Error ? error.message : '未知错误'}`
    }
  }
}


function handleWorkflowEditNewSession() {
  workflowEditSessionId.value = null
  workflowEditMessages.value = []
  workflowEditCurrentSessionTitle.value = ''
}

async function handleWorkflowEditLoadSessions() {
  if (!currentWorkflow.value?.id) return

  isLoadingWorkflowEditHistory.value = true
  try {
    const response = await getWorkflowEditSessions(currentWorkflow.value.id)
    workflowEditSessions.value = response.sessions
  } catch (error) {
    console.error('Failed to load workflow edit sessions:', error)
  } finally {
    isLoadingWorkflowEditHistory.value = false
  }
}

async function handleWorkflowEditLoadSessionDetail(sessionId: string) {
  if (!currentWorkflow.value?.id) return

  isLoadingWorkflowEditDetail.value = true
  try {
    const response = await getWorkflowEditSessionDetail(currentWorkflow.value.id, sessionId)
    workflowEditSessionDetail.value = {
      session: response.session,
      messages: response.messages
    }
  } catch (error) {
    console.error('Failed to load workflow edit session detail:', error)
  } finally {
    isLoadingWorkflowEditDetail.value = false
  }
}

function handleWorkflowEditContinueSession(sessionId: string) {
  if (!workflowEditSessionDetail.value) return

  workflowEditSessionId.value = sessionId
  workflowEditMessages.value = workflowEditSessionDetail.value.messages
    .filter(msg => msg.role !== 'tool')
    .map(msg => ({
      id: msg.id,
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
      content_parts: msg.content_parts as EditMessage['content_parts'],
      tool_executing: msg.tool_executing,
      changes: msg.changes
    }))
  const firstUserMsg = workflowEditSessionDetail.value.messages.find(m => m.role === 'user')
  workflowEditCurrentSessionTitle.value = firstUserMsg?.content.slice(0, 20) || ''
}

function handleWorkflowEditChangeClick(change: { block_index: number; old_content: string; new_content: string; step_index: number; step_name: string }) {
  workflowBlockDiffData.value = {
    stepIndex: change.step_index,
    blockIndex: change.block_index,
    oldContentParts: [{ type: 'text' as const, content: change.old_content }],
    newContentParts: [{ type: 'text' as const, content: change.new_content }]
  }
}

async function handleRegenerateFeature(featureItem: FeatureListItem) {
  featureMenuId.value = null

  try {
    await deleteFeature(featureItem.id)

    features.value = features.value.filter(f => f.id !== featureItem.id)

    await handleToolClick(featureItem.feature_type)
  } catch (error) {
    console.error('Failed to regenerate feature:', error)
  }
}

async function handleDeleteFeature(featureItem: FeatureListItem) {
  featureMenuId.value = null

  try {
    await deleteFeature(featureItem.id)
    features.value = features.value.filter(f => f.id !== featureItem.id)

    if (activeFeature.value?.id === featureItem.id) {
      closeFeatureDetail()
    }
  } catch (error) {
    console.error('Failed to delete feature:', error)
  }
}

defineExpose({ titleInputRef })


/**
 * TODO: workflow / feature 列表、详情面板菜单、重试等 UI 尚未重新挂载。
 * 以下 state/handler 是预留给这些入口的占位实现，通过 void 引用避免 TS6133
 * "declared but never read" 报错，重新挂载对应 UI 时直接绑定即可。
 */
void [
  processingToolTypes,
  isLoadingWorkflows,
  toggleWorkflowMenu,
  handleRenameWorkflow,
  handleRenameFeature,
  handleFeatureClick,
  openToolConfig,
  openWorkflowConfig,
  startWorkflowPolling,
  viewWorkflowDetail,
  handleCancelWorkflow,
  handleDeleteWorkflow,
  handleFinalizeWorkflow,
  handleRegenerateFeature,
  handleDeleteFeature,
  getWorkflowStatusText,
  getWorkflowStatusClass,
  formatTime,
]
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


.studio-panel.collapsed {
  padding: 0;
  border: none;
  overflow: hidden;
  min-width: 0;
}

.studio-panel.collapsed > * {
  display: none;
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


.studio-panel {
  background: var(--bg-white);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  flex-shrink: 1;
  overflow: hidden;
  transition: width 0.2s ease;
  min-width: 280px;
  max-width: 500px;
}

.studio-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 8px;
}

.studio-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 8px;
  background: var(--bg-main);
  border-radius: 12px;
  color: var(--text-secondary);
  font-size: 13px;
  text-align: center;
  cursor: pointer;
  transition: background 0.15s;
  min-height: 80px;
  flex: 1 1 calc(33.333% - 8px);
  min-width: 80px;
  max-width: calc(50% - 5px);
}

.studio-item svg {
  width: 24px;
  height: 24px;
}

.studio-item:hover:not(.disabled) {
  background: var(--bg-hover);
}

.studio-item.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.studio-item.loading {
  cursor: wait;
  background: var(--primary-light);
}

.studio-item.completed {
  background: var(--primary-light);
  color: var(--primary-color);
}

.studio-item.completed svg {
  color: var(--primary-color);
}

.studio-item .loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.studio-item.more-features {
  opacity: 0.5;
  font-size: 12px;
  color: var(--text-tertiary);
}


.studio-tasks {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
}

.studio-task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.studio-task-item:hover:not(.disabled):not(.loading) {
  background: var(--bg-hover);
}

.studio-task-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.studio-task-item.loading {
  cursor: wait;
}

.studio-task-item.completed {
  background: var(--primary-light);
}

.studio-task-item.completed:hover {
  background: rgba(26, 115, 232, 0.15);
}

.studio-task-item.failed {
  background: rgba(220, 53, 69, 0.08);
  cursor: not-allowed;
}

.studio-task-item.failed:hover {
  background: rgba(220, 53, 69, 0.12);
}

.studio-task-item .task-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-main);
  border-radius: 8px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.studio-task-item.completed .task-icon {
  background: var(--primary-color);
  color: white;
}

.studio-task-item.failed .task-icon {
  background: rgba(220, 53, 69, 0.15);
  color: #dc3545;
}

.studio-task-item.loading .task-icon {
  background: var(--primary-light);
}

.studio-task-item .task-icon .loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.studio-task-item .task-info {
  flex: 1;
  min-width: 0;
}

.studio-task-item .task-title {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.studio-task-item .task-status {
  display: block;
  font-size: 12px;
  color: var(--text-tertiary);
}

.studio-task-item.completed .task-status {
  color: var(--primary-color);
}

.studio-task-item.failed .task-status {
  color: #dc3545;
}

.studio-task-item .task-action {
  position: relative;
  color: var(--text-tertiary);
  opacity: 0;
  transition: opacity 0.15s;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.studio-task-item .task-action:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.studio-task-item:hover .task-action,
.studio-task-item .task-action.menu-open {
  opacity: 1;
}


.feature-dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--bg-white);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 120px;
  z-index: 100;
  overflow: hidden;
}

.feature-dropdown-menu .dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s;
}

.feature-dropdown-menu .dropdown-item:hover {
  background: var(--bg-hover);
}

.feature-dropdown-menu .dropdown-item svg {
  flex-shrink: 0;
  color: var(--text-secondary);
}


.feature-report-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}


.workflow-report-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.workflow-report-content .workflow-feature-section {
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
}

.workflow-report-content .workflow-feature-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.workflow-report-content .report-body {
  padding: 16px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
}

.feature-report-content .report-body {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
}


.feature-report-content .report-body h1,
.feature-report-content .report-body h2,
.feature-report-content .report-body h3,
.feature-report-content .report-body h4,
.feature-report-content .report-body h5,
.feature-report-content .report-body h6 {
  margin: 1.2em 0 0.6em;
  font-weight: 600;
  color: var(--text-primary);
}

.feature-report-content .report-body h1 { font-size: 1.4em; }
.feature-report-content .report-body h2 { font-size: 1.2em; }
.feature-report-content .report-body h3 { font-size: 1.1em; }
.feature-report-content .report-body h4 { font-size: 1em; }


.feature-report-content .report-body .feature-paragraph {
  margin: 0.6em 0;
}


.feature-report-content .report-body .feature-list {
  margin: 0.6em 0;
  padding-left: 0;
  list-style-type: none;
}

.feature-report-content .report-body .feature-list li {
  margin: 0.6em 0;
  line-height: 1.8;
}


.feature-report-content .report-body .feature-quote {
  margin: 0.8em 0;
  padding: 10px 14px;
  border-left: 3px solid var(--primary-color);
  background: var(--bg-main);
  border-radius: 0 6px 6px 0;
  color: var(--text-secondary);
}


.feature-report-content .report-body .feature-image {
  margin: 1em 0;
  text-align: center;
}

.feature-report-content .report-body .feature-image .image-wrapper {
  position: relative;
  display: inline-block;
}

.feature-report-content .report-body .feature-image img {
  max-width: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.feature-report-content .report-body .image-download-btn {
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  opacity: 0;
  transition: opacity 0.2s, background 0.2s, color 0.2s;
}

.feature-report-content .report-body .image-wrapper:hover .image-download-btn {
  opacity: 1;
}

.feature-report-content .report-body .image-download-btn:hover {
  background: var(--primary-color);
  color: white;
}

.feature-report-content .report-body .feature-image figcaption {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
}


.feature-report-content .report-body .feature-image-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin: 1em 0;
}

.feature-report-content .report-body .feature-image-group .feature-image {
  margin: 0;
}

.feature-report-content .report-body .feature-image-group > figcaption {
  grid-column: 1 / -1;
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
}


.feature-report-content .report-body .feature-video {
  margin: 1em 0;
  text-align: center;
}

.feature-report-content .report-body .feature-video video {
  max-width: 100%;
  border-radius: 8px;
}

.feature-report-content .report-body .feature-video figcaption {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
}


.feature-report-content .report-body .feature-text {
  white-space: pre-wrap;
}


.feature-report-content .report-body .inline-citation {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  margin: 0 1px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  vertical-align: baseline;
  position: relative;
  top: -2px;
}

.feature-report-content .report-body .inline-citation:hover {
  background: #1976d2;
  color: white;
}

.feature-report-content .report-body .inline-citation.active {
  background: #1976d2;
  color: white;
  box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.3);
}


.feature-report-content .report-body .inline-citation.disabled {
  background: #e0e0e0;
  color: #9e9e9e;
  cursor: default;
}

.feature-report-content .report-body .inline-citation.disabled:hover {
  background: #d0d0d0;
  transform: none;
}


.feature-report-content .report-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--text-secondary);
}

.feature-report-content .report-error p {
  margin: 0;
  font-size: 14px;
}

.studio-notes {
  flex: 1;
  padding: 16px;
  border-top: 1px solid var(--border-light);
}

.notes-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
}

.notes-hint {
  font-size: 13px;
  color: var(--text-tertiary);
  text-align: center;
  padding: 40px 0;
}


.panel-back-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.panel-back-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}


.studio-content-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.studio-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0 16px 16px;
  overflow: hidden;
  min-height: 0;
  width: 100%;
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #fff;
}


.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease-out;
}

.slide-left-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}


.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s ease-out;
}

.slide-right-enter-from {
  transform: translateX(-100%);
  opacity: 0;
}

.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}


.studio-tools-fixed {
  flex-shrink: 0;
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}


.studio-results-scroll {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}


.studio-results-scroll::-webkit-scrollbar {
  width: 6px;
}

.studio-results-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.studio-results-scroll::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
  transition: background 0.2s;
}

.studio-results-scroll:hover::-webkit-scrollbar-thumb {
  background: var(--border-color);
}

.studio-results-scroll:hover::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}


.panel-title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-title-wrapper .panel-title {
  font-size: 14px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.panel-title-wrapper .panel-title:hover {
  color: var(--text-secondary);
}

.panel-title-wrapper .panel-title.active {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.panel-title-wrapper .panel-title-divider {
  font-size: 14px;
  color: var(--border-color);
  margin: 0 2px;
}


.tool-grid.oneclick {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}


.tool-grid.oneclick .tool-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 60px;
}

.tool-grid.oneclick .tool-card:hover:not(.disabled):not(.tool-card--placeholder) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.tool-grid.oneclick .tool-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tool-grid.oneclick .tool-card-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
}

.tool-grid.oneclick .tool-card-title {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.2;
}

.tool-grid.oneclick .tool-card-edit {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
  transition: opacity 0.15s;
}

.tool-grid.oneclick .tool-card:hover:not(.disabled) .tool-card-edit {
  opacity: 1;
}


.tool-card--orange {
  background: linear-gradient(135deg, rgba(255, 186, 125, 0.5) 0%, rgba(255, 154, 77, 0.5) 100%);
}
.tool-card--orange .tool-card-icon { color: #c2410c; }
.tool-card--orange .tool-card-title { color: #c2410c; }
.tool-card--orange .tool-card-edit { color: #ea580c; }


.tool-card--blue {
  background: linear-gradient(135deg, rgba(147, 197, 253, 0.5) 0%, rgba(96, 165, 250, 0.5) 100%);
}
.tool-card--blue .tool-card-icon { color: #1d4ed8; }
.tool-card--blue .tool-card-title { color: #1d4ed8; }
.tool-card--blue .tool-card-edit { color: #2563eb; }


.tool-card--purple {
  background: linear-gradient(135deg, rgba(192, 132, 252, 0.5) 0%, rgba(168, 85, 247, 0.5) 100%);
}
.tool-card--purple .tool-card-icon { color: #7c3aed; }
.tool-card--purple .tool-card-title { color: #7c3aed; }
.tool-card--purple .tool-card-edit { color: #8b5cf6; }


.tool-card--teal {
  background: linear-gradient(135deg, rgba(94, 234, 212, 0.5) 0%, rgba(45, 212, 191, 0.5) 100%);
}
.tool-card--teal .tool-card-icon { color: #0d9488; }
.tool-card--teal .tool-card-title { color: #0d9488; }
.tool-card--teal .tool-card-edit { color: #14b8a6; }


.tool-card--green {
  background: linear-gradient(135deg, rgba(134, 239, 172, 0.5) 0%, rgba(74, 222, 128, 0.5) 100%);
}
.tool-card--green .tool-card-icon { color: #16a34a; }
.tool-card--green .tool-card-title { color: #16a34a; }
.tool-card--green .tool-card-edit { color: #22c55e; }


.tool-card--cyan {
  background: linear-gradient(135deg, rgba(165, 243, 252, 0.5) 0%, rgba(103, 232, 249, 0.5) 100%);
}
.tool-card--cyan .tool-card-icon { color: #0e7490; }
.tool-card--cyan .tool-card-title { color: #0e7490; }
.tool-card--cyan .tool-card-edit { color: #0891b2; }


.tool-card--amber {
  background: linear-gradient(135deg, rgba(253, 230, 138, 0.5) 0%, rgba(251, 191, 36, 0.5) 100%);
}
.tool-card--amber .tool-card-icon { color: #b45309; }
.tool-card--amber .tool-card-title { color: #b45309; }
.tool-card--amber .tool-card-edit { color: #f59e0b; }


.tool-card--rose {
  background: linear-gradient(135deg, rgba(254, 205, 211, 0.5) 0%, rgba(251, 113, 133, 0.5) 100%);
}
.tool-card--rose .tool-card-icon { color: #be123c; }
.tool-card--rose .tool-card-title { color: #be123c; }
.tool-card--rose .tool-card-edit { color: #f43f5e; }


.tool-card--indigo {
  background: linear-gradient(135deg, rgba(199, 210, 254, 0.5) 0%, rgba(165, 180, 252, 0.5) 100%);
}
.tool-card--indigo .tool-card-icon { color: #4338ca; }
.tool-card--indigo .tool-card-title { color: #4338ca; }
.tool-card--indigo .tool-card-edit { color: #6366f1; }

.tool-card--custom {
  background:
    linear-gradient(135deg, rgba(20, 184, 166, 0.28) 0%, rgba(250, 204, 21, 0.34) 100%),
    radial-gradient(circle at 85% 12%, rgba(255, 255, 255, 0.68) 0%, rgba(255, 255, 255, 0) 34%);
  border: 1px solid rgba(13, 148, 136, 0.28);
}
.tool-card--custom .tool-card-icon {
  color: #0f766e;
}
.tool-card--custom .tool-card-title {
  color: #0f766e;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-weight: 650;
  letter-spacing: 0;
}
.tool-grid.oneclick .tool-card--custom:hover:not(.disabled) {
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.18);
}


.tool-card--placeholder {
  background: transparent;
  border: none;
  opacity: 0;
  cursor: default;
  pointer-events: none;
}
.tool-card--placeholder:hover {
  transform: none;
  box-shadow: none;
}
.tool-card--placeholder .tool-card-icon { color: var(--text-tertiary); }
.tool-card--placeholder .tool-card-title { color: var(--text-tertiary); }


.oneclick-queue {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.queue-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.queue-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.queue-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  font-size: 13px;
}


.workflow-detail {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.workflow-detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.workflow-detail-header .workflow-name {
  flex: 1;
}

.workflow-close-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.workflow-close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}


.workflow-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: var(--bg-primary);
  border-radius: 6px;
  transition: background 0.15s;
}

.workflow-step.clickable {
  cursor: pointer;
}

.workflow-step.clickable:hover {
  background: var(--bg-hover);
}

.step-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  flex-shrink: 0;
}


.step-icon.icon-blue {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.step-icon.icon-orange {
  background: rgba(249, 115, 22, 0.15);
  color: #f97316;
}

.step-icon.icon-cream {
  background: rgba(251, 191, 36, 0.15);
  color: #d97706;
}

.step-icon.icon-green {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.step-icon.icon-purple {
  background: rgba(168, 85, 247, 0.15);
  color: #a855f7;
}

.step-icon.icon-brown {
  background: rgba(180, 83, 9, 0.15);
  color: #b45309;
}

.step-icon.icon-teal {
  background: rgba(20, 184, 166, 0.15);
  color: #14b8a6;
}

.step-icon.icon-indigo {
  background: rgba(99, 102, 241, 0.15);
  color: #6366f1;
}

.step-icon.icon-rose {
  background: rgba(244, 63, 94, 0.15);
  color: #f43f5e;
}

.step-icon.icon-amber {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.step-icon.icon-emerald {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.step-icon.icon-default {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.step-num {
  font-size: 11px;
  font-weight: 500;
}

.step-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-name {
  font-size: 13px;
  color: var(--text-primary);
}

.step-title {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step-error {
  font-size: 12px;
  color: #ef4444;
}

.step-arrow {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.step-failed-icon {
  color: #ef4444;
  flex-shrink: 0;
}

.workflow-step.failed {
  opacity: 0.7;
}

.workflow-step.failed .step-icon {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}


.workflow-combined-content {
  max-height: calc(100vh - 280px);
  overflow-y: auto;
  padding-right: 4px;
}

.workflow-combined-content::-webkit-scrollbar {
  width: 6px;
}

.workflow-combined-content::-webkit-scrollbar-track {
  background: transparent;
}

.workflow-combined-content::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
  transition: background 0.2s;
}

.workflow-combined-content:hover::-webkit-scrollbar-thumb {
  background: var(--border-color);
}

.workflow-feature-section {
  background: var(--bg-primary);
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.workflow-feature-section.failed {
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.workflow-feature-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.feature-section-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  flex-shrink: 0;
}

.feature-section-icon.icon-blue {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.feature-section-icon.icon-orange {
  background: rgba(249, 115, 22, 0.15);
  color: #f97316;
}

.feature-section-icon.icon-cream {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.feature-section-icon.icon-green {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.feature-section-icon.icon-purple {
  background: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
}

.feature-section-icon.icon-red {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.feature-section-icon.icon-default {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.feature-section-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.workflow-feature-body {
  padding: 12px;
}

.workflow-feature-error {
  padding: 12px;
  color: #ef4444;
  font-size: 13px;
}

.workflow-empty {
  padding: 24px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
}


.workflow-history {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.workflow-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.workflow-item:hover {
  background: var(--bg-hover);
}

.workflow-item-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 12px;
}

.workflow-item-icon.icon-purple {
  background: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
}

.workflow-item-icon.icon-blue {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.workflow-item-icon.icon-teal {
  background: rgba(20, 184, 166, 0.15);
  color: #14b8a6;
}

.workflow-item-icon.icon-green {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.workflow-item-icon.icon-orange {
  background: rgba(249, 115, 22, 0.15);
  color: #f97316;
}

.workflow-item-icon.icon-default {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.workflow-item-icon.source-quick-read {
  background: linear-gradient(135deg, rgba(147, 197, 253, 0.5) 0%, rgba(96, 165, 250, 0.5) 100%);
  color: #1d4ed8;
}

.workflow-item-icon.source-deep-dive {
  background: linear-gradient(135deg, rgba(199, 210, 254, 0.5) 0%, rgba(165, 180, 252, 0.5) 100%);
  color: #4338ca;
}

.workflow-item-icon.source-custom {
  background:
    linear-gradient(135deg, rgba(20, 184, 166, 0.28) 0%, rgba(250, 204, 21, 0.34) 100%),
    radial-gradient(circle at 85% 12%, rgba(255, 255, 255, 0.68) 0%, rgba(255, 255, 255, 0) 34%);
  border: 1px solid rgba(13, 148, 136, 0.28);
  color: #0f766e;
}

.workflow-item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.workflow-item-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.workflow-item-name {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.35;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-source-chip {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  height: 18px;
  max-width: 118px;
  padding: 0 7px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
  line-height: 18px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-source-chip.source-quick-read {
  background: linear-gradient(135deg, rgba(147, 197, 253, 0.42) 0%, rgba(96, 165, 250, 0.28) 100%);
  color: #1d4ed8;
}

.workflow-source-chip.source-deep-dive {
  background: linear-gradient(135deg, rgba(199, 210, 254, 0.55) 0%, rgba(165, 180, 252, 0.38) 100%);
  color: #4338ca;
}

.workflow-source-chip.source-custom {
  background:
    linear-gradient(135deg, rgba(20, 184, 166, 0.2) 0%, rgba(250, 204, 21, 0.28) 100%),
    radial-gradient(circle at 86% 12%, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0) 36%);
  border: 1px solid rgba(13, 148, 136, 0.22);
  color: #0f766e;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  letter-spacing: 0;
}

.workflow-item-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.workflow-item-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.workflow-status-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
}

.workflow-status-badge.status-pending {
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
}

.workflow-status-badge.status-processing {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
  position: relative;
  animation: workflowBreathing 1.6s ease-in-out infinite;
}

.workflow-status-badge.status-cancelling {
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
  position: relative;
}

.workflow-status-badge.status-completed {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.workflow-status-badge.status-failed {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.workflow-status-badge.status-partial {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.workflow-status-badge.status-cancelled {
  background: rgba(107, 114, 128, 0.15);
  color: #6b7280;
}

.workflow-status-badge.status-processing::after {
  content: '...';
  display: inline-block;
  margin-left: 2px;
  animation: workflowDots 1.2s steps(4, end) infinite;
}

.workflow-status-badge.status-cancelling::after {
  content: '...';
  display: inline-block;
  margin-left: 2px;
  animation: workflowDots 1.2s steps(4, end) infinite;
}

@keyframes workflowDots {
  0% { clip-path: inset(0 100% 0 0); }
  33% { clip-path: inset(0 66% 0 0); }
  66% { clip-path: inset(0 33% 0 0); }
  100% { clip-path: inset(0 0 0 0); }
}

@keyframes workflowBreathing {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.25);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(59, 130, 246, 0);
  }
}

.workflow-stop-btn,
.workflow-delete-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-left: 8px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--text-tertiary);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s, background 0.15s, color 0.15s;
}

.workflow-item:hover .workflow-stop-btn,
.workflow-item:hover .workflow-delete-btn {
  opacity: 1;
}

.workflow-stop-btn {
  opacity: 1;
}

.workflow-stop-btn:hover {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.workflow-delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}


@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 1s linear infinite;
}


.workflow-item-action {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  opacity: 0;
}

.workflow-item:hover .workflow-item-action,
.workflow-item-action.active,
.workflow-item:hover .workflow-finalize-btn {
  opacity: 1;
}

.workflow-finalize-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-right: 4px;
  border: none;
  background: transparent;
  color: var(--success-color);
  border-radius: 4px;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s;
}

.workflow-finalize-btn:hover {
  background: var(--bg-success-light, #ecfdf5);
  color: var(--success-color-dark, #059669);
}

.workflow-finalized-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background-color: var(--bg-success-light, #ecfdf5);
  color: var(--success-color, #10b981);
  border: 1px solid var(--success-color-light, #a7f3d0);
  margin-right: 4px;
}

.workflow-loading {
  padding: 20px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
}

.workflow-item-action:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.workflow-dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  width: 120px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
  padding: 4px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}

.dropdown-item:hover {
  background: var(--bg-hover);
}

.dropdown-item.danger {
  color: var(--error-color);
}

.dropdown-item.danger:hover {
  background: var(--error-bg-hover, rgba(220, 38, 38, 0.05));
}
</style>
