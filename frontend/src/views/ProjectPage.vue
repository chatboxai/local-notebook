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
        <button class="btn-settings" @click="$router.push('/settings')" title="设置">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87a.49.49 0 0 0 .12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32a.49.49 0 0 0-.12-.61l-2.01-1.58zM12 15.6a3.6 3.6 0 1 1 0-7.2 3.6 3.6 0 0 1 0 7.2z"/>
          </svg>
        </button>
        <span class="user-badge">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
          <span>admin</span>
        </span>
      </div>
    </header>


    <div class="project-main">

      <div class="project-body">

        <aside
          class="sources-panel"
          :class="{ collapsed: leftPanelCollapsed }"
          :style="{ width: leftPanelCollapsed ? '0px' : leftPanelWidth + 'px' }"
        >

        <template v-if="isPreviewMode && (previewingFileContent || isPreviewingImage || isPdfFile)">
          <div class="panel-header">
            <span class="panel-title">来源</span>
            <button class="panel-toggle-btn" @click="closePreview" title="返回列表">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
              </svg>
            </button>
          </div>
          <div class="preview-file-header">
            <div class="preview-file-name">
              <svg v-if="isPreviewingImage" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
              </svg>
              <span>{{ previewingFileName }}</span>
            </div>

            <div v-if="isPdfFile && supportsRawView" class="view-toggle">
              <button
                class="view-toggle-btn"
                :class="{ active: viewMode === 'raw' }"
                @click="switchViewMode('raw')"
                title="原文视图"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                  <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/>
                </svg>
                原文
              </button>
              <button
                class="view-toggle-btn"
                :class="{ active: viewMode === 'parsed' }"
                @click="switchViewMode('parsed')"
                title="解析视图"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                  <path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/>
                </svg>
                解析
              </button>
            </div>
          </div>


          <template v-if="isPreviewingImage">
            <div class="preview-content image-preview-content" ref="previewContentRef">
              <div v-if="isLoadingContent" class="preview-loading">加载中...</div>
              <div v-else class="image-preview-wrapper">
                <img
                  v-if="previewingFile"
                  :src="getImagePreviewUrl(previewingFile.id)"
                  :alt="previewingFileName"
                  class="preview-image"
                />

                <div v-if="previewingImageInfo?.description" class="image-description-card">
                  <div class="image-description-header">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <span>图片描述</span>
                    <span v-if="previewingImageInfo.vlm_model" class="vlm-model-tag">
                      {{ previewingImageInfo.vlm_model }}
                    </span>
                  </div>
                  <div class="image-description-content">{{ previewingImageInfo.description }}</div>
                </div>
              </div>
            </div>
          </template>


          <template v-else>

            <div v-if="previewSummary" class="source-guide-card">
              <div class="source-guide-header">
                <div class="source-guide-title">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7zm2.85 11.1l-.85.6V16h-4v-2.3l-.85-.6A4.997 4.997 0 0 1 7 9c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.63-.8 3.16-2.15 4.1z"/>
                  </svg>
                  <span>来源指南</span>
                </div>
                <button class="source-guide-toggle" @click="summaryExpanded = !summaryExpanded">
                  <svg :class="{ rotated: !summaryExpanded }" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                    <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
                  </svg>
                </button>
              </div>
              <div v-show="summaryExpanded" class="source-guide-content" v-html="renderSummary(previewSummary)"></div>

              <div v-show="summaryExpanded" v-if="previewingFileContent?.keywords?.length" class="source-guide-keywords">
                <span
                  v-for="(keyword, index) in previewingFileContent.keywords"
                  :key="index"
                  class="keyword-tag"
                  @click="handleKeywordClick(keyword)"
                >{{ keyword }}</span>
              </div>
            </div>


            <div class="preview-content-wrapper">
              <div class="preview-content" ref="previewContentRef" @scroll="handlePreviewScroll">

              <div v-if="isLoadingContent" class="preview-loading">加载中...</div>


              <PdfViewer
                v-if="isRawViewMode && pdfPageInfo && previewingFile"
                ref="pdfViewerRef"
                :file-id="previewingFile.id"
                :page-info="pdfPageInfo"
                @page-change="handlePdfPageChange"
                @block-click="handlePdfBlockClick"
                @clear-selection="handlePdfClearSelection"
                @loading="handlePdfLoading"
              />


              <template v-else-if="isPdfFile && visibleParsedPages.length > 0">
                <div
                  v-for="pageNum in visibleParsedPages"
                  :key="pageNum"
                  :data-page="pageNum"
                  class="parsed-page-section"
                >

                  <div class="page-divider">
                    <span class="page-divider-line"></span>
                    <span class="page-divider-text">第 {{ pageNum }} 页</span>
                    <span class="page-divider-line"></span>
                  </div>


                  <div class="parsed-page-content">

                    <template v-for="block in parsedBlocksByPage.get(pageNum) || []" :key="block.block_id">
                      <div
                        v-if="block.extra?.is_table"
                        :data-block-id="block.block_id"
                        class="preview-block table-block"
                        :class="{ highlighted: highlightBlockIds.includes(block.block_id) }"
                      >
                        <div v-if="block.extra?.table_caption" class="table-caption">{{ block.extra.table_caption }}</div>
                        <div class="table-content" v-html="block.extra?.table_html || renderLatexOnly(block.content)"></div>
                        <div v-if="block.extra?.table_footnote" class="table-footnote">{{ block.extra.table_footnote }}</div>
                      </div>

                      <div
                        v-else
                        :data-block-id="block.block_id"
                        class="preview-block"
                        :class="{ [block.block_type]: true, highlighted: highlightBlockIds.includes(block.block_id) }"
                      ><span v-if="highlightBlockIds.includes(block.block_id)" class="highlight-text" v-html="renderLatexOnly(block.content)"></span><span v-else v-html="renderLatexOnly(block.content)"></span></div>
                    </template>
                  </div>
                </div>
              </template>


              <template v-else-if="isPreviewingAudio && previewingFileContent?.blocks">
                <div
                  v-for="block in previewingFileContent.blocks"
                  :key="block.block_id"
                  :data-block-id="block.block_id"
                  class="audio-block"
                  :class="{ highlighted: highlightBlockIds.includes(block.block_id) }"
                >
                  <span class="audio-meta">{{ block.extra?.time_range || '' }} 说话人{{ (block.extra?.speaker ?? 0) + 1 }}</span>
                  <span class="audio-text">{{ block.content }}</span>
                </div>
              </template>


              <template v-else-if="previewingFileContent?.blocks">

                <template v-for="block in previewingFileContent.blocks" :key="block.block_id">
                  <div
                    v-if="block.extra?.is_table"
                    :data-block-id="block.block_id"
                    class="preview-block table-block"
                    :class="{ highlighted: highlightBlockIds.includes(block.block_id) }"
                  >
                    <div v-if="block.extra?.table_caption" class="table-caption">{{ block.extra.table_caption }}</div>
                    <div class="table-content" v-html="block.extra?.table_html || renderLatexOnly(block.content)"></div>
                    <div v-if="block.extra?.table_footnote" class="table-footnote">{{ block.extra.table_footnote }}</div>
                  </div>

                  <div
                    v-else
                    :data-block-id="block.block_id"
                    class="preview-block"
                    :class="{ [block.block_type]: true, highlighted: highlightBlockIds.includes(block.block_id) }"
                  ><span v-if="highlightBlockIds.includes(block.block_id)" class="highlight-text" v-html="renderLatexOnly(block.content)"></span><span v-else v-html="renderLatexOnly(block.content)"></span></div>
                </template>
              </template>
              </div>


              <div v-if="isPdfFile && currentTotalPages > 0" class="page-nav-float">
                <span class="page-indicator">第 {{ currentPageNum }} / {{ currentTotalPages }} 页</span>
                <div class="page-jump">
                  <input
                    type="number"
                    v-model="jumpToPageInput"
                    :min="1"
                    :max="currentTotalPages"
                    placeholder="页码"
                    @keyup.enter="jumpToPage"
                  />
                  <button class="jump-btn" @click="jumpToPage">跳转</button>
                </div>
              </div>
            </div>
          </template>
        </template>


        <template v-else>
        <div class="panel-header">
          <span class="panel-title">来源</span>
          <button class="panel-toggle-btn" @click="leftPanelCollapsed = !leftPanelCollapsed" title="收起面板">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/>
              <path d="M7 7h4v10H7z" opacity="0.5"/>
            </svg>
          </button>
        </div>

        <button class="add-source-btn" @click="triggerFileUpload">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
          </svg>
          添加来源
        </button>


        <div v-if="uploadingFiles.length > 0" class="upload-progress-container">
          <div
            v-for="(item, index) in uploadingFiles"
            :key="index"
            class="upload-progress-item"
            :class="item.status"
          >
            <div class="upload-file-name">{{ item.name }}</div>
            <div class="upload-progress-bar">
              <div
                class="upload-progress-fill"
                :style="{ width: item.progress + '%' }"
              ></div>
            </div>
            <div class="upload-status">
              <template v-if="item.status === 'uploading'">{{ item.progress }}%</template>
              <template v-else-if="item.status === 'success'">完成</template>
              <template v-else-if="item.status === 'error'">失败</template>
            </div>
          </div>
        </div>


        <div v-if="readyFiles.length > 0" class="select-all-row" @click="toggleSelectAll">
          <span>选择所有来源</span>
          <div class="select-all-check" :class="{ checked: isAllSelected }">
            <svg v-if="isAllSelected" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
          </div>
        </div>


        <div class="sources-list">
          <div v-if="files.length === 0" class="empty-sources">
            <div class="empty-icon">
              <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
              </svg>
            </div>
            <p>已保存的来源将显示在此处</p>
            <p class="hint">点击上方的"添加来源"即可添加 PDF、文本文件。</p>
          </div>

          <div
            v-for="file in sortedFiles"
            :key="file.id"
            class="source-item"
            :class="{
              selected: selectedFileIds.includes(file.id),
              processing: file.status === 'processing',
              pending: file.status === 'pending',
              ready: file.status === 'ready'
            }"
            @click="file.status === 'ready' && openFilePreview(file.id)"
            @mouseenter="hoveringFileId = file.id"
            @mouseleave="hoveringFileId = null"
          >

            <div class="source-left">

              <div v-if="hoveringFileId === file.id && (file.status === 'ready' || file.status === 'failed')" class="source-menu-wrapper">
                <button
                  class="source-menu-btn"
                  @click.stop="toggleFileMenu(file.id)"
                >
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                    <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                  </svg>
                </button>

                <div v-if="openMenuFileId === file.id" class="source-dropdown">
                  <button v-if="file.status === 'ready'" class="dropdown-item" @click.stop="openRenameModal('file', file.id, file.file_name)">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                    </svg>
                    重命名
                  </button>
                  <button class="dropdown-item danger" @click.stop="handleDeleteFile(file.id)">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                    </svg>
                    删除
                  </button>
                </div>
              </div>

              <div v-else class="source-icon" :class="{ 'image-icon': isImageFile(file), 'audio-icon': isAudioFile(file) }">

                <svg v-if="isImageFile(file)" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
                </svg>

                <svg v-else-if="isAudioFile(file)" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
                </svg>

                <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
                </svg>
              </div>
            </div>
            <div class="source-info">
              <span class="source-name">{{ file.file_name }}</span>
              <span
                v-if="file.status !== 'ready'"
                class="source-status"
                :class="file.status"
                :title="file.status === 'failed' ? (file.error_message || '') : ''"
              >
                {{ getStatusText(file.status) }}
                <span v-if="file.status === 'failed' && file.error_message" class="source-status-reason">
                  {{ file.error_message }}
                </span>
              </span>
            </div>

            <div v-if="file.status === 'ready'" class="source-right">
              <div
                class="source-checkbox"
                :class="{ checked: selectedFileIds.includes(file.id) }"
                @click="toggleFileSelection(file.id, $event)"
              >
                <svg v-if="selectedFileIds.includes(file.id)" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
        </template>
      </aside>


      <div
        class="resizer left-resizer"
        :class="{ hidden: leftPanelCollapsed }"
        @mousedown="startResizeLeft"
      >
        <div class="resizer-line"></div>
      </div>


      <div v-if="leftPanelCollapsed" class="collapsed-sidebar left">
        <div class="collapsed-icon-btn" @click="leftPanelCollapsed = false" title="展开来源面板">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/>
            <path d="M7 7h4v10H7z" opacity="0.5"/>
          </svg>
        </div>
        <div class="collapsed-icon-btn" @click="triggerFileUpload" title="添加来源">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
          </svg>
        </div>
        <div class="collapsed-icon-btn" @click="leftPanelCollapsed = false" :title="`${files.length} 个来源文件`">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
          </svg>
          <span v-if="files.length > 0" class="icon-badge">{{ files.length }}</span>
        </div>
      </div>


      <main class="chat-panel">
        <div class="chat-header">

          <div class="session-title-wrapper">
            <input
              v-if="isEditingSessionTitle"
              ref="sessionTitleInputRef"
              v-model="editingSessionTitleValue"
              class="session-title-input"
              @blur="handleSessionTitleBlur"
              @keydown.enter="handleSessionTitleEnter"
              @keydown.escape="cancelSessionTitleEdit"
              @compositionstart="isSessionTitleComposing = true"
              @compositionend="isSessionTitleComposing = false"
            />
            <span
              v-else
              class="chat-title"
              @click="startSessionTitleEdit"
              title="点击编辑会话标题"
            >{{ currentSession?.title || '新对话' }}</span>
          </div>

          <div class="chat-header-actions">
            <button
              class="header-action-btn"
              @click="handleCreateNewSession"
              :disabled="isStreaming"
              title="新建对话"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
              </svg>
            </button>
            <button
              class="header-action-btn"
              @click="showSessionHistory = true"
              title="历史对话"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="chat-messages" ref="messagesRef" @scroll="handleMessagesScroll" @mouseover="handleWebCitationHover" @mouseout="handleWebCitationLeave" @click="handleChatAreaClick">
          <div v-if="messages.length === 0" class="chat-empty">

            <template v-if="hasReadyFiles">
              <div class="greeting-message">{{ localizedGreeting }}</div>
            </template>

            <template v-else>
              <div class="empty-upload-icon">
                <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
                  <path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z" />
                </svg>
              </div>
              <h3>添加来源即可开始使用</h3>
              <button class="upload-btn" @click="triggerFileUpload">上传来源</button>
            </template>
          </div>

          <template v-else>

            <div v-if="isLoadingMoreMessages" class="loading-more-messages">
              <span class="loading-spinner"></span>
              <span>加载历史消息...</span>
            </div>
            <div v-else-if="hasMoreMessages && isMessagesScrollable" class="load-more-hint">
              <span>向上滚动加载更多</span>
            </div>

            <div
              v-for="(msg, index) in messages"
              :key="msg.id"
              class="message"
              :class="[msg.role, {
                'tool-only': isToolOnlyMessage(msg),
                'selection-mode': isExportSelectionMode,
                'conversation-selected': isExportSelectionMode && isMessageInSelectedConversation(index)
              }]"
              @click="isExportSelectionMode && toggleConversationSelection(index)"
            >

              <div v-if="isExportSelectionMode && msg.role === 'user'" class="message-selection-check">
                <div class="custom-checkbox" :class="{ checked: selectedUserMessageIds.includes(msg.id) }">
                  <svg v-if="selectedUserMessageIds.includes(msg.id)" viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                </div>
              </div>


              <div v-if="msg.role === 'compact_divider'" class="compact-divider">
                <span>── 更早的对话已压缩 ──</span>
              </div>

              <div v-else-if="msg.role === 'user'" class="user-message" :class="{ 'editing': editingMessageId === msg.id, 'selectable': isExportSelectionMode }">

                <div v-if="editingMessageId === msg.id" class="user-message-edit">
                  <textarea
                    ref="editTextareaRef"
                    v-model="editingContent"
                    class="user-edit-textarea"
                    @keydown.enter.exact.prevent="submitEditMessage(msg)"
                    @keydown.escape="cancelEditMessage"
                    @input="autoResizeEditTextarea"
                  ></textarea>
                  <div class="user-edit-actions">
                    <button class="edit-cancel-btn" @click="cancelEditMessage">取消</button>
                    <button class="edit-submit-btn" :disabled="!editingContent.trim() || isStreaming" @click="submitEditMessage(msg)">
                      保存并重新生成
                    </button>
                  </div>
                </div>

                <template v-else>
                  <span class="user-message-content">{{ msg.content }}</span>
                  <div v-if="!isExportSelectionMode" class="user-action-btns">
                    <button class="user-action-btn" :data-tooltip="isPreCompactMessage(index) ? '已压缩的消息不可编辑' : '编辑'" @click="startEditMessage(msg)" :disabled="isStreaming || isPreCompactMessage(index)">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                      </svg>
                    </button>
                    <button class="user-action-btn" data-tooltip="复制" @click="copyUserMessage(msg)">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                    </button>
                  </div>
                </template>
              </div>
              <div v-else class="assistant-message">
                <div
                  class="assistant-content"
                  :class="{ 'has-error': parseMessageContent(msg).hasError }"
                >
                  <div
                    v-for="(segment, segIndex) in getRenderedMessage(msg)"
                    :key="segIndex"
                    class="assistant-segment"
                    :class="`segment-${segment.type}`"
                  >
                    <div
                      v-if="segment.type === 'body'"
                      class="assistant-body markdown-body"
                      v-html="segment.html"
                    ></div>
                    <div
                      v-else
                      v-html="segment.html"
                    ></div>
                  </div>
                </div>

                <div v-if="shouldShowMessageActions(index)" class="message-actions">
                  <button class="action-btn" data-tooltip="复制纯文本" @click="copyMessageAsText(msg)">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                  </button>
                  <button class="action-btn" data-tooltip="复制 Markdown" @click="copyMessageAsMarkdown(msg)">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 3v4a1 1 0 001 1h4"></path>
                      <path d="M17 21H7a2 2 0 01-2-2V5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2z"></path>
                      <path d="M9 15l2-2 2 2"></path>
                      <path d="M11 13v4"></path>
                    </svg>
                  </button>
                  <button class="action-btn" disabled data-tooltip="喜欢（即将推出）">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                    </svg>
                  </button>
                  <button class="action-btn" disabled data-tooltip="不喜欢（即将推出）">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                    </svg>
                  </button>
                  <button
                    class="action-btn"
                    :class="{ 'error-retry': parseMessageContent(msg).hasError }"
                    :disabled="!isLastAssistantMessage(index) || isStreaming || isPreCompactMessage(index)"
                    :data-tooltip="isPreCompactMessage(index) ? '已压缩的消息不可重新生成' : (parseMessageContent(msg).hasError ? '重新生成（上次出错）' : (isLastAssistantMessage(index) ? '重新生成' : '仅最后一条消息可重新生成'))"
                    @click="regenerateMessage(index)"
                  >
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 4v6h6"></path>
                      <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
                    </svg>
                  </button>
                  <button
                    class="action-btn"
                    data-tooltip="下载对话"
                    :disabled="isStreaming"
                    @click.stop="enterExportModeWithSelection(index)"
                  >
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7 10 12 15 17 10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                  </button>
                  <span class="actions-divider">|</span>
                  <span class="agent-role-label">{{ msg.agent_role === 'analysis' ? '分析助手' : '小洛' }}</span>
                  <span class="message-time">{{ formatMessageTime(msg.created_at) }}</span>
                </div>
              </div>
            </div>


            <div v-if="streamingParts.length > 0 || isStreaming" class="message assistant">
              <div class="assistant-message">
                <div class="assistant-content">
                  <div
                    v-for="(segment, segIndex) in streamingRendered"
                    :key="segIndex"
                    class="assistant-segment"
                    :class="`segment-${segment.type}`"
                  >
                    <div
                      v-if="segment.type === 'body'"
                      class="assistant-body markdown-body"
                      v-html="segment.html"
                    ></div>
                    <div
                      v-else
                      v-html="segment.html"
                    ></div>
                  </div>
                </div>

                <div v-if="isThinking" class="thinking-indicator">
                  <svg class="thinking-spinner" viewBox="0 0 24 24" width="14" height="14">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="31.4 31.4" stroke-linecap="round"/>
                  </svg>
                  <span>思考中...</span>
                </div>
              </div>
            </div>
          </template>
        </div>


        <transition name="fade">
          <button
            v-if="showScrollToBottom"
            class="scroll-to-bottom-btn"
            :style="{ bottom: scrollBtnBottom + (isExportSelectionMode ? 60 : 0) + 'px' }"
            @click="forceScrollToBottom"
            title="滚动到底部"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
            </svg>
          </button>
        </transition>


        <transition name="slide-up">
          <div v-if="isExportSelectionMode" class="selection-action-bar">
            <div class="selection-info">
              <button class="select-all-btn" @click="toggleSelectAllUserMessages">
                {{ selectedUserMessageIds.length === messages.filter(m => m.role === 'user').length ? '取消全选' : '全选' }}
              </button>
              <span class="selected-count">已选中 {{ selectedUserMessageIds.length }} 项</span>
            </div>
            <div class="selection-actions">
              <button class="selection-cancel-btn" @click="toggleExportSelectionMode">取消</button>
              <button
                class="selection-export-btn"
                :disabled="selectedUserMessageIds.length === 0 || isExportingMessages"
                @click="handleExportSelectedMessages"
              >
                {{ isExportingMessages ? '导出中...' : '导出为 Word' }}
              </button>
            </div>
          </div>
        </transition>


        <div class="chat-input-wrapper" ref="inputWrapperRef" :class="{ 'disabled-by-selection': isExportSelectionMode }">
          <div class="chat-input-box">
            <div class="input-main-row">
              <textarea
                ref="textareaRef"
                v-model="inputMessage"
                :placeholder="hasReadyFiles ? '有什么想问的？' : '上传来源即可开始使用'"
                :disabled="!currentSession || isStreaming || !hasReadyFiles"
                @keydown.enter.exact.prevent="handleSendEnter"
                @compositionstart="isComposing = true"
                @compositionend="isComposing = false"
                @input="autoResizeTextarea"
                rows="1"
              ></textarea>
              <button
                v-if="!isStreaming"
                class="send-btn"
                :disabled="!inputMessage.trim() || !currentSession || !hasReadyFiles"
                @click="sendMessage"
                title="发送"
              >
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              </button>
              <button
                v-else
                class="send-btn"
                @click="stopStreaming"
                title="暂停"
              >
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M6 5h4v14H6zm8 0h4v14h-4z" />
                </svg>
              </button>
            </div>
            <div class="input-options-row">
              <label class="web-search-toggle" :class="{ active: enableWebSearch }">
                <input type="checkbox" v-model="enableWebSearch" />
                <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
                <span>联网搜索</span>
              </label>


              <span class="source-count">{{ readyFiles.length }} 个来源</span>
            </div>
          </div>
        </div>


        <Transition name="copy-toast">
          <div v-if="copyToastVisible" class="copy-toast">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
            {{ copyToastMessage }}
          </div>
        </Transition>
      </main>


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
          maxWidth: (showFeatureDetail || showWorkflowDetail) ? '900px' : '500px'
        }"
      >

        <WorkflowDetailPanel
          v-if="showWorkflowDetail && currentWorkflow"
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
                    <div class="tool-card tool-card--purple disabled" title="功能开发中">
                      <div class="tool-card-icon">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                      </div>
                      <span class="tool-card-title">综合报告</span>
                    </div>
                    <div class="tool-card tool-card--blue disabled" title="功能开发中">
                      <div class="tool-card-icon">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/></svg>
                      </div>
                      <span class="tool-card-title">深度解析</span>
                    </div>
                    <div class="tool-card tool-card--teal disabled" title="功能开发中">
                      <div class="tool-card-icon">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zM7 17h7v-2H7v2zm0-4h10v-2H7v2zm0-4h10V7H7v2z"/></svg>
                      </div>
                      <span class="tool-card-title">知识图谱</span>
                    </div>
                  </div>
                </div>


            <div class="studio-results-scroll">
              <div class="oneclick-queue">
                <div class="queue-header">
                  <span class="queue-title">生成结果</span>
                </div>

                <div class="queue-empty">
                  <p>功能开发中</p>
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
      :max-file-count="30"
      :is-uploading="isUploading"
      @close="showUploadModal = false"
      @upload-files="handleUploadFiles"
      @insert-text="handleInsertText"
    />


    <ImageCitationModal
      :visible="imageCitationModal.visible"
      :file-name="imageCitationModal.fileName"
      :preview-url="imageCitationModal.previewUrl"
      @close="closeImageCitationModal"
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
      :workflow-type="workflowConfigModal.workflowType"
      :workflow-title="workflowConfigModal.workflowTitle"
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
      title="确认定稿"
      message="确认将此工作流标记为“定稿”吗？

      定稿后内容将不可修改，且会作为后续生成的重要参考。"
      confirm-text="确认定稿"
      cancel-text="取消"
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


    <Teleport to="body">
      <div
        v-if="copyPanelVisible && selectedPdfBlock && copyPanelPosition"
        class="block-copy-panel-floating"
        :style="{
          top: copyPanelPosition.top + 'px',
          left: copyPanelPosition.left + 'px'
        }"
      >
        <div class="copy-panel-content">
          <div class="copy-panel-text">{{ selectedPdfBlock.content }}</div>
          <div class="copy-panel-actions">
            <button class="copy-btn" @click.stop="copySelectedBlockText">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
              </svg>
              复制文本
            </button>
            <button class="close-btn" @click.stop="clearSelectedBlock">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </Teleport>


    <Toast :visible="toastVisible" :message="toastMessage" :type="toastType" />

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import 'katex/dist/katex.min.css'
import { escapeHtml, renderMarkdownWithLatex, renderLatexOnly, renderSummary } from '../utils'
import { parseThinkingContent, renderThinkingBlock, ENABLE_THINK_PARSING } from '../utils/think'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import FeatureConfigModal from '../components/common/FeatureConfigModal.vue'
import UploadSourceModal from '../components/common/UploadSourceModal.vue'
import ToolConfigModal from '../components/common/ToolConfigModal.vue'
import WorkflowConfigModal from '../components/common/WorkflowConfigModal.vue'
import ImageCitationModal from '../components/common/ImageCitationModal.vue'
import ImageGenerationModal, { type ImageFile } from '../components/common/ImageGenerationModal.vue'
import VideoGenerationModal, { type VideoFile, type VideoGenerationMode, type VideoGenerationConfig } from '../components/common/VideoGenerationModal.vue'
import FeatureDetailPanel from '../components/project/FeatureDetailPanel.vue'
import WorkflowDetailPanel from '../components/project/WorkflowDetailPanel.vue'
import PdfViewer from '../components/PdfViewer.vue'
import SessionHistoryPanel from '../components/SessionHistoryPanel.vue'
import LanguageSwitcher from '../components/common/LanguageSwitcher.vue'
import { usePanelResize } from '../composables/usePanelResize'
import {
  getProject,
  getFiles,
  uploadFile,
  deleteFile,
  getFileContent,
  getFilePageInfo,
  getFilesStatusBatch,
  getSessions,
  createSession,
  getSession,
  deleteSession,
  updateSessionTitle,
  chatStream,
  editMessageAndRegenerate,
  type AgentRole,
  getImagePreviewUrl,
  getImageInfo,
  getBlocksLocation,
  getFile,
  type CitationRef,
  type FoundBlock,
  type FilePageInfo,
  exportChatMessagesToWord,
  updateProject,
  updateFile,


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
  renameWorkflow,
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
  type WorkflowStatus,
  type WorkflowCitation,
  type WorkflowContentFeature,
  type EditSession,
  type EditSessionMessage,
  type FeatureEditCitationRef,
  type FeatureEditHistoryMessage,
} from '../services/api'
import type { Project, FileInfo, Session, Message, ContentPart, ToolExecuting, ToolStatusPart, FileContent, Feature, FeatureCitationRefPart, ImageInfo } from '../types'
import RenameModal from '../components/common/RenameModal.vue'
import WebCitationTooltip from '../components/common/WebCitationTooltip.vue'
import Toast from '../components/common/Toast.vue'
import { locale, translateText } from '../i18n'


const IMAGE_TYPES = ['jpg', 'jpeg', 'png']


const AUDIO_TYPES = ['wav', 'mp3', 'm4a', 'wma']


function isImageFile(file: FileInfo): boolean {
  return IMAGE_TYPES.includes(file.file_type?.toLowerCase() || '')
}


function isAudioFile(file: FileInfo): boolean {
  return AUDIO_TYPES.includes(file.file_type?.toLowerCase() || '')
}

const route = useRoute()
const router = useRouter()

const project = ref<Project | null>(null)
const files = ref<FileInfo[]>([])
const sessions = ref<Session[]>([])
const currentSession = ref<Session | null>(null)
const messages = ref<Message[]>([])


const totalMessages = ref(0)
const messagesOffset = ref(0)
const hasMoreMessages = ref(false)
const isLoadingMoreMessages = ref(false)
const isMessagesScrollable = ref(false)
const MESSAGES_PAGE_SIZE = 50


const isExportSelectionMode = ref(false)
const selectedUserMessageIds = ref<string[]>([])
const isExportingMessages = ref(false)


function toggleExportSelectionMode() {
  if (isStreaming.value) return
  isExportSelectionMode.value = !isExportSelectionMode.value
  if (!isExportSelectionMode.value) {
    selectedUserMessageIds.value = []
  }
}


function enterExportModeWithSelection(assistantIndex: number) {
  if (isStreaming.value) return


  let userMessageId: string | null = null
  for (let i = assistantIndex - 1; i >= 0; i--) {
    const msg = messages.value[i]
    if (msg?.role === 'user' && !msg.id.startsWith('temp_')) {
      userMessageId = msg.id
      break
    }
  }


  isExportSelectionMode.value = true


  if (userMessageId) {
    selectedUserMessageIds.value = [userMessageId]
  } else {
    selectedUserMessageIds.value = []
  }
}


function toggleMessageSelection(messageId: string) {
  const index = selectedUserMessageIds.value.indexOf(messageId)
  if (index === -1) {
    selectedUserMessageIds.value.push(messageId)
  } else {
    selectedUserMessageIds.value.splice(index, 1)
  }
}


function getConversationUserMsgId(msgIndex: number): string | null {
  const msg = messages.value[msgIndex]
  if (!msg) return null


  if (msg.role === 'user' && !msg.id.startsWith('temp_')) {
    return msg.id
  }


  for (let i = msgIndex - 1; i >= 0; i--) {
    const prevMsg = messages.value[i]
    if (prevMsg?.role === 'user' && !prevMsg.id.startsWith('temp_')) {
      return prevMsg.id
    }
  }
  return null
}


function isMessageInSelectedConversation(msgIndex: number): boolean {
  const userMsgId = getConversationUserMsgId(msgIndex)
  return userMsgId ? selectedUserMessageIds.value.includes(userMsgId) : false
}


function toggleConversationSelection(msgIndex: number) {
  if (!isExportSelectionMode.value) return

  const userMsgId = getConversationUserMsgId(msgIndex)
  if (userMsgId) {
    toggleMessageSelection(userMsgId)
  }
}


function toggleSelectAllUserMessages() {
  const userMsgIds = messages.value
    .filter(m => m.role === 'user' && !m.id.startsWith('temp_'))
    .map(m => m.id)

  if (selectedUserMessageIds.value.length === userMsgIds.length) {
    selectedUserMessageIds.value = []
  } else {
    selectedUserMessageIds.value = userMsgIds
  }
}


async function handleExportSelectedMessages() {
  if (selectedUserMessageIds.value.length === 0 || !currentSession.value) return

  isExportingMessages.value = true
  try {
    const { blob, filename } = await exportChatMessagesToWord(
      currentSession.value.id,
      selectedUserMessageIds.value
    )


    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    showToast('导出成功', 'success')
    isExportSelectionMode.value = false
    selectedUserMessageIds.value = []
  } catch (error: any) {
    console.error('Failed to export messages:', error)
    showToast(error.response?.data?.error || '导出失败', 'error')
  } finally {
    isExportingMessages.value = false
  }
}


function checkMessagesScrollable() {
  nextTick(() => {
    if (messagesRef.value) {
      isMessagesScrollable.value = messagesRef.value.scrollHeight > messagesRef.value.clientHeight
    }
  })
}


watch(messages, () => {
  checkMessagesScrollable()
}, { flush: 'post' })


const isEditingTitle = ref(false)
const editingTitleValue = ref('')
const titleInputRef = ref<HTMLInputElement | null>(null)
const isTitleComposing = ref(false)
const titleInputWidth = ref('120px')


const isEditingSessionTitle = ref(false)
const editingSessionTitleValue = ref('')
const sessionTitleInputRef = ref<HTMLInputElement | null>(null)
const isSessionTitleComposing = ref(false)


const showSessionHistory = ref(false)


const sortedFiles = computed(() => {
  return [...files.value].sort((a, b) => {
    const aIsImage = isImageFile(a)
    const bIsImage = isImageFile(b)
    if (aIsImage === bIsImage) return 0
    return aIsImage ? 1 : -1
  })
})


const readyFiles = computed(() => files.value.filter(f => f.status === 'ready'))


const hasReadyFiles = computed(() => readyFiles.value.length > 0)


const GREETINGS = [
  { zh: '小洛在此，您请讲', en: 'Xiaoluo is here. Go ahead.' },
  { zh: '今天想聊点什么呀？', en: 'What would you like to talk about today?' },
  { zh: '嗨，你来啦', en: 'Hi, you are here.' },
] as const
const randomGreeting = ref<(typeof GREETINGS)[number]>(
  GREETINGS[Math.floor(Math.random() * GREETINGS.length)] ?? GREETINGS[0],
)
const localizedGreeting = computed(() => randomGreeting.value[locale.value])


const selectedFileIds = ref<string[]>([])


watch(readyFiles, (newReadyFiles, oldReadyFiles) => {
  const oldIds = new Set((oldReadyFiles || []).map(f => f.id))
  const currentSelected = new Set(selectedFileIds.value)


  newReadyFiles.forEach(file => {
    if (!oldIds.has(file.id)) {
      currentSelected.add(file.id)
    }
  })


  const newIds = new Set(newReadyFiles.map(f => f.id))
  selectedFileIds.value = Array.from(currentSelected).filter(id => newIds.has(id))
}, { immediate: true })

function toggleFileSelection(fileId: string, event: Event) {
  event.stopPropagation()
  const index = selectedFileIds.value.indexOf(fileId)
  if (index === -1) {
    selectedFileIds.value.push(fileId)
  } else {
    selectedFileIds.value.splice(index, 1)
  }
}


function toggleSelectAll() {
  if (selectedFileIds.value.length === readyFiles.value.length) {

    selectedFileIds.value = []
  } else {

    selectedFileIds.value = readyFiles.value.map(f => f.id)
  }
}


const isAllSelected = computed(() =>
  readyFiles.value.length > 0 && selectedFileIds.value.length === readyFiles.value.length
)

const inputMessage = ref('')
const enableWebSearch = ref(localStorage.getItem('enableWebSearch') === 'true')
const agentRole = ref<AgentRole>('default')
const isStreaming = ref(false)
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
const editTextareaRef = ref<HTMLTextAreaElement[]>([])


watch(enableWebSearch, (val) => {
  localStorage.setItem('enableWebSearch', val ? 'true' : 'false')
})


const userExpandedThinkingBlocks = new Set<string>()
const isComposing = ref(false)

const messagesRef = ref<HTMLDivElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const inputWrapperRef = ref<HTMLDivElement | null>(null)
const scrollBtnBottom = ref(100)


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


const hoveringFileId = ref<string | null>(null)
const pollingFileIds = ref<Set<string>>(new Set())
const openMenuFileId = ref<string | null>(null)
let filePollingTimer: ReturnType<typeof setInterval> | null = null


const showUploadModal = ref(false)


const TOOL_TYPES = [


  { type: 'objective_positioning', title: '定位分析', tooltip: '确定内容定位和差异化重点', color: 'cyan', icon: 'positioning', enabled: false },
  { type: 'audience_profile', title: '受众画像', tooltip: '分析核心受众群体和需求', color: 'amber', icon: 'audience', enabled: false },
  { type: 'comparative_analysis', title: '同类分析', tooltip: '搜索分析同类资料或方案', color: 'indigo', icon: 'market', enabled: false },


  { type: 'content_summary', title: '内容摘要', tooltip: '生成文档内容摘要', color: 'green', icon: 'summary', enabled: false },


  { type: 'title_suggestion', title: '标题生成', tooltip: '分析文档内容，生成标题建议', color: 'purple', icon: 'title', enabled: false },
  { type: 'communication_copy', title: '传播文案', tooltip: '生成传播文案和推荐语', color: 'rose', icon: 'copy', enabled: false },


  { type: 'text_to_image', title: '文生图', tooltip: '输入描述文字，AI生成图片', color: 'brown', icon: 'image', enabled: false },
  { type: 'reference_to_image', title: '图生图', tooltip: '选择参考图片，AI生成新图片', color: 'teal', icon: 'image_ref', enabled: false },

  { type: 'text_to_video', title: '文生视频', tooltip: '输入描述文字，AI生成视频', color: 'indigo', icon: 'video', enabled: false },
  { type: 'image_to_video', title: '图生视频', tooltip: '选择一张图片作为首帧生成视频', color: 'rose', icon: 'video_image', enabled: false },
  { type: 'start_end_to_video', title: '首尾帧视频', tooltip: '选择首尾两张图片生成过渡视频', color: 'amber', icon: 'video_frames', enabled: false },

]


const IMAGE_GENERATION_TYPES = ['text_to_image', 'reference_to_image']


const VIDEO_GENERATION_TYPES = ['text_to_video', 'image_to_video', 'start_end_to_video']


const features = ref<FeatureListItem[]>([])

const activeFeature = ref<Feature | null>(null)

const showFeatureDetail = ref(false)

const featureMenuId = ref<string | null>(null)


const featureEditMode = ref(false)
const editingFeature = ref<Feature | null>(null)


type EditMessageContentPart = { type: 'text'; content: string } | { type: 'citation_ref'; display_num: number; citation_id: string; file_name?: string; segment_id?: string; summary?: string; citation_type?: 'image' | 'web' }
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
    .filter(f => f.status === 'ready' && ['jpg', 'jpeg', 'png', 'webp'].includes(f.file_type?.toLowerCase() || ''))
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
    .filter(f => f.status === 'ready' && ['jpg', 'jpeg', 'png'].includes(f.file_type?.toLowerCase() || ''))
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


  if (citationType === 'image') {
    const fileId = citationMeta?.file_id
    const imageName = citationMeta?.image_name

    if (imageName && fileId) {

      await jumpToPdfImageLocation({
        fileId,
        fileName: citationMeta?.file_name || '',
        imageName,
        imageIndex: citationMeta?.image_index,
        page: citationMeta?.page
      })
    } else if (fileId) {

      openImageCitationModal({
        fileId,
        fileName: citationMeta?.file_name || '',
        previewUrl: getImagePreviewUrl(fileId)
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

  highlightBlockIds.value = []
  pdfViewerRef.value?.clearHighlights()
}


function clearWorkflowCitation() {
  activeWorkflowCitationNum.value = null
  activeWorkflowFeatureId.value = null

  highlightBlockIds.value = []
  pdfViewerRef.value?.clearHighlights()
}


const isPreviewMode = ref(false)
const previewingFileContent = ref<FileContent | null>(null)
const previewingFileName = ref<string>('')
const previewingFile = ref<FileInfo | null>(null)
const previewingImageInfo = ref<ImageInfo | null>(null)
const highlightBlockIds = ref<string[]>([])
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
  openRenameModal('workflow', workflow.id, workflow.title || workflow.display_name)
}


function closeWorkflowMenu() {
  workflowMenuId.value = null
}

const activeWorkflowFeatureId = ref<string | null>(null)
const featureEditActiveCitationNum = ref<number | null>(null)
const workflowEditActiveCitationNum = ref<number | null>(null)
const fileContentCache = ref<Map<string, FileContent>>(new Map())
const pageInfoCache = ref<Map<string, FilePageInfo>>(new Map())
const isLoadingContent = ref(false)
const previewContentRef = ref<HTMLDivElement | null>(null)
const pdfViewerRef = ref<InstanceType<typeof PdfViewer> | null>(null)
const summaryExpanded = ref(true)


const isPdfFile = ref(false)
const supportsRawView = ref(false)
const viewMode = ref<'raw' | 'parsed'>('raw')
const currentBlockIds = ref<string[]>([])
const pdfPageInfo = ref<FilePageInfo | null>(null)
const currentPageNum = ref(1)
const jumpToPageInput = ref('')


const selectedPdfBlock = ref<FoundBlock | null>(null)
const copyPanelVisible = ref(false)
const copyPanelPosition = ref<{ top: number; left: number } | null>(null)


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


const isUploading = ref(false)


interface UploadingFile {
  name: string
  progress: number
  status: 'uploading' | 'success' | 'error'
  error?: string
}
const uploadingFiles = ref<UploadingFile[]>([])


const isRawViewMode = computed(() => isPdfFile.value && viewMode.value === 'raw')


watch(activeChatCitationNum, (newNum, oldNum) => {

  if (oldNum !== null) {
    const oldElements = document.querySelectorAll(`.assistant-content .segment-citation[data-display-num="${oldNum}"]`)
    oldElements.forEach(el => el.classList.remove('active'))
  }

  if (newNum !== null) {
    const newElements = document.querySelectorAll(`.assistant-content .segment-citation[data-display-num="${newNum}"]`)
    newElements.forEach(el => el.classList.add('active'))
  }
})


const parsedBlocksByPage = computed(() => {
  type BlocksType = NonNullable<typeof previewingFileContent.value>['blocks']
  if (!previewingFileContent.value?.blocks) return new Map<number, BlocksType>()

  const grouped = new Map<number, BlocksType>()
  for (const block of previewingFileContent.value.blocks) {
    const page = block.page || 1
    if (!grouped.has(page)) {
      grouped.set(page, [])
    }
    grouped.get(page)!.push(block)
  }
  return grouped
})


const parsedTotalPages = computed(() => {
  if (!previewingFileContent.value?.blocks) return 0
  let maxPage = 0
  for (const block of previewingFileContent.value.blocks) {
    if (block.page && block.page > maxPage) {
      maxPage = block.page
    }
  }
  return maxPage
})


const visibleParsedPages = computed(() => {
  if (!isPdfFile.value || isRawViewMode.value || parsedTotalPages.value === 0) return []


  const pages: number[] = []
  for (let p = 1; p <= parsedTotalPages.value; p++) {
    pages.push(p)
  }
  return pages
})


const currentTotalPages = computed(() => {
  if (isRawViewMode.value) {

    return pdfViewerRef.value?.totalPages || 0
  }
  return parsedTotalPages.value
})


function clearSelectedBlock() {
  selectedPdfBlock.value = null
  copyPanelVisible.value = false
  copyPanelPosition.value = null

  pdfViewerRef.value?.clearSelectedBlock()
}


function handlePdfPageChange(pageNum: number) {
  currentPageNum.value = pageNum
}


function handlePdfLoading(loading: boolean) {
  isLoadingContent.value = loading
}


function handlePdfBlockClick(block: FoundBlock, position: { top: number; left: number }) {
  selectedPdfBlock.value = block
  copyPanelVisible.value = true


  const panelWidth = 320
  const viewportWidth = window.innerWidth
  let panelLeft = position.left + 8

  if (panelLeft + panelWidth > viewportWidth - 20) {
    panelLeft = position.left - panelWidth - 8
  }

  copyPanelPosition.value = {
    top: position.top,
    left: Math.max(8, panelLeft)
  }
}


function handlePdfClearSelection() {
  selectedPdfBlock.value = null
  copyPanelVisible.value = false
  copyPanelPosition.value = null
}


async function copySelectedBlockText() {
  if (!selectedPdfBlock.value) return

  try {
    await copyTextToClipboard(selectedPdfBlock.value.content)
    showToast('复制成功')
  } catch (error) {
    console.error('Failed to copy text:', error)
    showToast('复制失败', 'error')
  }
}


const isPreviewingImage = computed(() => {
  return previewingFile.value ? isImageFile(previewingFile.value) : false
})


const isPreviewingAudio = computed(() => {
  return previewingFile.value ? isAudioFile(previewingFile.value) : false
})


const previewSummary = computed(() => {

  if (previewingFileContent.value?.summary) {
    return previewingFileContent.value.summary
  }

  return ''
})


const isUserScrolling = ref(false)
const showScrollToBottom = ref(false)


const clickedCitationElement = ref<HTMLElement | null>(null)
const clickedCitationTop = ref<number>(0)


const leftPanelCollapsed = ref(false)
const rightPanelCollapsed = ref(true)
const leftPanelWidth = ref(400)
const rightPanelWidth = ref(450)


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
  workflowType: '',
  workflowTitle: ''
})


const workflows = ref<WorkflowListItem[]>([])
const currentWorkflow = ref<WorkflowDetail | null>(null)
const workflowPollingTimer = ref<number | null>(null)
const workflowLoading = ref(false)
const isLoadingWorkflows = ref(false)
const workflowFeatures = ref<WorkflowContentFeature[]>([])
const workflowCitations = ref<Record<string, WorkflowCitation>>({})
const showWorkflowDetail = ref(false)


let pollErrorCount = 0
const MAX_POLL_ERRORS = 5


const PREVIEW_MIN_WIDTH = 700
const leftPanelWidthBeforePreview = ref<number | null>(null)


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
    maxWidth: (showFeatureDetail.value || showWorkflowDetail.value) ? 900 : 500
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
    confirmDialog.confirmText = options.confirmText || '确定'
    confirmDialog.cancelText = options.cancelText || '取消'
    confirmDialog.onConfirm = () => resolve(true)
    confirmDialog.onCancel = () => resolve(false)
    confirmDialog.visible = true
  })
}

function openFeatureConfigDialog(stepIndex: number, dialogTitle: string, prompt: string, fileIds: string[]) {
  featureConfigDialog.title = dialogTitle
  featureConfigDialog.message = '确定要重新生成该步骤吗？'
  featureConfigDialog.confirmText = '重新生成'
  featureConfigDialog.cancelText = '取消'
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
  return '该步骤'
}


const imageCitationModal = reactive({
  visible: false,
  fileId: '',
  fileName: '',
  previewUrl: ''
})


function openImageCitationModal(data: {
  fileId: string
  fileName: string
  previewUrl: string
}) {
  imageCitationModal.fileId = data.fileId
  imageCitationModal.fileName = data.fileName
  imageCitationModal.previewUrl = data.previewUrl
  imageCitationModal.visible = true
}


function closeImageCitationModal() {
  imageCitationModal.visible = false
}

const projectId = route.params.id as string


function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {

    const processingWorkflow = workflows.value.find(
      wf => wf.status === 'pending' || wf.status === 'processing'
    )
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

  nextTick(() => updateScrollBtnPosition())

  window.addEventListener('resize', checkMessagesScrollable)

  checkMessagesScrollable()
})


onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('click', handleCitationClickEvent)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  window.removeEventListener('resize', checkMessagesScrollable)

  stopFilePolling()
  stopFeaturePolling()
  stopWorkflowPolling()
})

function localizedThinkingLabel() {
  return escapeHtml(translateText('思考过程'))
}

function renderThinkingToggleContent(isExpanded: boolean) {
  const iconPath = isExpanded
    ? 'M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z'
    : 'M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z'

  return `<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="${iconPath}"/></svg><span>${localizedThinkingLabel()}</span>`
}


async function handleCitationClickEvent(event: MouseEvent) {
  const target = event.target as HTMLElement


  const thinkingToggle = target.closest('[data-thinking-toggle]') as HTMLElement | null
  if (thinkingToggle) {
    const thinkingBlock = thinkingToggle.closest('.thinking-block') as HTMLElement | null
    if (thinkingBlock) {
      const isExpanded = thinkingBlock.classList.contains('expanded')
      const blockId = thinkingBlock.dataset.thinkingId || ''

      if (isExpanded) {

        thinkingBlock.classList.remove('expanded')
        thinkingBlock.classList.add('collapsed')

        thinkingToggle.innerHTML = renderThinkingToggleContent(false)

        if (blockId) {
          userExpandedThinkingBlocks.delete(blockId)
        }
      } else {

        thinkingBlock.classList.remove('collapsed')
        thinkingBlock.classList.add('expanded')

        thinkingToggle.innerHTML = renderThinkingToggleContent(true)

        if (blockId) {
          userExpandedThinkingBlocks.add(blockId)
        }
      }
      return
    }
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


      const isPdfImage = !!imageName

      if (isPdfImage && fileId) {

        const imageIndex = imageIndexStr ? parseInt(imageIndexStr, 10) : undefined
        const page = pageStr ? parseInt(pageStr, 10) : undefined
        await jumpToPdfImageLocation({
          fileId,
          fileName,
          imageName,
          imageIndex,
          page
        })
      } else if (fileId) {

        openImageCitationModal({
          fileId,
          fileName,
          previewUrl: getImagePreviewUrl(fileId)
        })
      }
    } else {

      const segmentId = citationEl.dataset.segmentId
      const displayNum = parseInt(citationEl.textContent || '0', 10)

      if (segmentId) {

        activeFeatureCitationNum.value = null
        activeWorkflowCitationNum.value = null
        featureEditActiveCitationNum.value = null
        workflowEditActiveCitationNum.value = null
        activeChatCitationNum.value = displayNum


        const parts = segmentId.split('_s_')
        const fileId = parts[0]

        if (fileId) {

          const willExpand = !isPreviewMode.value && leftPanelWidth.value < PREVIEW_MIN_WIDTH

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

  pdfViewerRef.value?.clearHighlights()
  highlightBlockIds.value = []
  currentBlockIds.value = []
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

watch(messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
})

watch(streamingParts, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

async function loadProject() {
  try {
    const data = await getProject(projectId)
    project.value = data
  } catch (error) {
    console.error('Failed to load project:', error)
  }
}

async function loadFiles() {
  try {
    files.value = await getFiles(projectId)

    for (const file of files.value) {
      if (file.status === 'processing' || file.status === 'pending') {
        pollFileStatus(file.id)
      }
    }
  } catch (error) {
    console.error('Failed to load files:', error)
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

function triggerFileUpload() {
  showUploadModal.value = true
}


const MAX_FILE_COUNT = 30


const FILE_SIZE_LIMITS = {
  document: 100 * 1024 * 1024,
  image: 20 * 1024 * 1024,
  audio: 200 * 1024 * 1024,
} as const


function getFileSizeLimit(file: File): number | null {
  const ext = file.name.split('.').pop()?.toLowerCase() || ''

  if (['txt', 'docx', 'pdf', 'epub'].includes(ext)) {
    return FILE_SIZE_LIMITS.document
  }
  if (['jpg', 'jpeg', 'png'].includes(ext)) {
    return FILE_SIZE_LIMITS.image
  }
  if (['wav', 'mp3', 'm4a', 'wma'].includes(ext)) {
    return FILE_SIZE_LIMITS.audio
  }
  return FILE_SIZE_LIMITS.document
}


function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}


function checkFileSize(file: File): { valid: boolean; error?: string } {
  const limit = getFileSizeLimit(file)
  if (limit === null) return { valid: true }

  if (file.size > limit) {
    return {
      valid: false,
      error: `"${file.name}" 超过大小限制（最大 ${formatFileSize(limit)}）`
    }
  }
  return { valid: true }
}


async function handleUploadFiles(fileList: File[]) {
  const remainingCount = MAX_FILE_COUNT - files.value.length
  if (remainingCount <= 0) {
    showToast(`已达到文件数量上限（${MAX_FILE_COUNT} 个）`, 'error')
    return
  }

  const filesToUpload = fileList.slice(0, remainingCount)


  const validFiles: File[] = []
  const sizeErrors: string[] = []
  const typeErrors: string[] = []

  for (const file of filesToUpload) {
    const ext = file.name.split('.').pop()?.toLowerCase() || ''
    if (ext === 'doc') {
      typeErrors.push(`"${file.name}" 暂不支持旧版 .doc 格式，请另存为 .docx 后再上传`)
      continue
    }

    const check = checkFileSize(file)
    if (check.valid) {
      validFiles.push(file)
    } else {
      sizeErrors.push(check.error!)
    }
  }


  const errors = [...typeErrors, ...sizeErrors]
  if (errors.length > 0) {
    showToast(errors.join('\n'), 'error', 5000)
    if (validFiles.length === 0) return
  }

  isUploading.value = true


  uploadingFiles.value = validFiles.map(f => ({
    name: f.name,
    progress: 0,
    status: 'uploading' as const
  }))

  let successCount = 0
  let failedCount = 0

  for (let i = 0; i < validFiles.length; i++) {
    const file = validFiles[i]!
    const uploadItem = uploadingFiles.value[i]!
    try {
      const uploaded = await uploadFile(projectId, file, (progress) => {
        uploadItem.progress = progress
      })
      files.value.push(uploaded)
      uploadItem.status = 'success'
      uploadItem.progress = 100
      successCount++

      if (uploaded.status !== 'ready' && uploaded.status !== 'failed') {
        pollFileStatus(uploaded.id)
      }
    } catch (error: any) {
      console.error('Failed to upload file:', error)
      const errorMsg = error?.response?.data?.error || error?.response?.data?.detail || error?.message || '上传失败'
      uploadItem.status = 'error'
      uploadItem.error = errorMsg
      failedCount++
    }
  }

  isUploading.value = false


  if (failedCount > 0 && successCount > 0) {
    showToast(`${successCount} 个成功，${failedCount} 个失败`, 'info', 4000)
  } else if (failedCount > 0) {
    showToast(`${failedCount} 个文件上传失败`, 'error', 4000)
  } else if (successCount > 0) {
    showToast(`${successCount} 个文件上传成功`, 'success', 3000)
  }


  setTimeout(() => {
    uploadingFiles.value = []
  }, 3000)
}


async function handleInsertText(content: string) {
  if (files.value.length >= MAX_FILE_COUNT) {
    showToast(`已达到文件数量上限（${MAX_FILE_COUNT} 个）`, 'error')
    return
  }

  const fileName = `粘贴文本_${new Date().toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).replace(/[\/\s:]/g, '')}.txt`
  const blob = new Blob([content], { type: 'text/plain' })
  const file = new File([blob], fileName, { type: 'text/plain' })

  isUploading.value = true
  try {
    const uploaded = await uploadFile(projectId, file)
    files.value.push(uploaded)

    if (uploaded.status !== 'ready' && uploaded.status !== 'failed') {
      pollFileStatus(uploaded.id)
    }
  } catch (error: any) {
    console.error('Failed to upload pasted text:', error)
    const msg = error?.response?.data?.error || error?.response?.data?.detail || error?.message || '上传失败'
    showToast(msg, 'error', 4000)
  } finally {
    isUploading.value = false
  }
}



function pollFileStatus(fileId: string) {
  pollingFileIds.value.add(fileId)

  startFilePolling()
}


function startFilePolling() {
  if (filePollingTimer) return

  filePollingTimer = setInterval(async () => {
    if (pollingFileIds.value.size === 0) {
      stopFilePolling()
      return
    }

    try {
      const fileIds = Array.from(pollingFileIds.value)
      const result = await getFilesStatusBatch(fileIds)

      for (const fileStatus of result.files) {

        const index = files.value.findIndex(f => f.id === fileStatus.id)
        if (index !== -1) {
          const existingFile = files.value[index]!
          files.value[index] = {
            ...existingFile,
            status: fileStatus.status as FileInfo['status'],
            error_message: fileStatus.error_message || existingFile.error_message
          }
        }


        if (fileStatus.status === 'ready' || fileStatus.status === 'failed') {
          pollingFileIds.value.delete(fileStatus.id)
        }
      }


      if (pollingFileIds.value.size === 0) {
        stopFilePolling()
      }
    } catch (error) {
      console.error('Failed to poll file status:', error)
    }
  }, 2000)
}


function stopFilePolling() {
  if (filePollingTimer) {
    clearInterval(filePollingTimer)
    filePollingTimer = null
  }
}

async function handleDeleteFile(fileId: string) {

  const file = files.value.find(f => f.id === fileId)
  const fileName = file?.file_name || '此文件'


  openMenuFileId.value = null


  const confirmed = await showConfirm({
    title: '删除文件',
    message: `确定要删除"${fileName}"吗？\n⚠️ 对话中所有引用该文件的标注将失效，无法查看原文出处。此操作无法撤销。`,
    type: 'danger',
    confirmText: '删除',
    cancelText: '取消'
  })
  if (!confirmed) return

  try {
    await deleteFile(fileId)
    files.value = files.value.filter((f) => f.id !== fileId)


    fileContentCache.value.delete(fileId)
    pageInfoCache.value.delete(fileId)


    if (previewingFileContent.value?.file_id === fileId) {
      closePreview()
    }
  } catch (error) {
    console.error('Failed to delete file:', error)
  }
}

function toggleFileMenu(fileId: string) {
  if (openMenuFileId.value === fileId) {
    openMenuFileId.value = null
  } else {
    openMenuFileId.value = fileId
  }
}


function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.source-menu-wrapper')) {
    openMenuFileId.value = null
  }

}


async function loadFileContent(fileId: string): Promise<FileContent | null> {

  if (fileContentCache.value.has(fileId)) {
    return fileContentCache.value.get(fileId)!
  }

  isLoadingContent.value = true
  try {
    const content = await getFileContent(fileId)
    fileContentCache.value.set(fileId, content)
    return content
  } catch (error) {
    console.error('Failed to load file content:', error)
    return null
  } finally {
    isLoadingContent.value = false
  }
}


async function openFilePreview(fileId: string, segmentId?: string) {
  const file = files.value.find(f => f.id === fileId)
  if (!file || file.status !== 'ready') return


  const isSwitchingFile = previewingFile.value && previewingFile.value.id !== fileId
  const isFirstOpen = !isPreviewMode.value
  const isImage = isImageFile(file)


  summaryExpanded.value = !segmentId


  if (isFirstOpen) {
    leftPanelWidthBeforePreview.value = leftPanelWidth.value
    if (leftPanelWidth.value < PREVIEW_MIN_WIDTH) {
      leftPanelWidth.value = PREVIEW_MIN_WIDTH
    }
  }


  if (isSwitchingFile || isFirstOpen) {

    previewingFileName.value = file.file_name
    previewingFile.value = file
    isPreviewMode.value = true
    highlightBlockIds.value = []
    isLoadingContent.value = true


    previewingFileContent.value = null
    isPdfFile.value = false
    supportsRawView.value = false
    viewMode.value = 'raw'
    currentBlockIds.value = []
    pdfPageInfo.value = null
    currentPageNum.value = 1
    jumpToPageInput.value = ''


    if (isSwitchingFile) {
      await nextTick()
      if (previewContentRef.value) {
        previewContentRef.value.scrollTop = 0
      }
    }

    if (isImage) {

      try {
        const imageInfo = await getImageInfo(fileId)
        if (imageInfo.images && imageInfo.images.length > 0) {
          previewingImageInfo.value = imageInfo.images[0] ?? null
        }
      } catch (error) {
        console.error('[Preview] Failed to get image info:', error)

      }
    } else {

      try {

        const fileInfo = await getFile(fileId)


        let pageInfo = pageInfoCache.value.get(fileId)
        if (!pageInfo) {
          pageInfo = await getFilePageInfo(fileId)
          pageInfoCache.value.set(fileId, pageInfo)
        }

        if (pageInfo.has_pages && file.file_type === 'pdf') {

          isPdfFile.value = true
          supportsRawView.value = fileInfo.supports_raw_view ?? true
          pdfPageInfo.value = pageInfo


          viewMode.value = 'raw'
        } else {

          const content = await loadFileContent(fileId)
          if (!content) {
            isLoadingContent.value = false
            return
          }
          previewingFileContent.value = content
        }
      } catch (error) {
        console.error('[Preview] Failed to get page info:', error)

        const content = await loadFileContent(fileId)
        if (content) {
          previewingFileContent.value = content
        }
      }
    }


    if (!isPdfFile.value || viewMode.value !== 'raw') {
      isLoadingContent.value = false
    }


    await nextTick()
    if (previewContentRef.value) {
      previewContentRef.value.scrollTop = 0
    }
  }


  highlightBlockIds.value = []


  if (segmentId && !isImage) {
    await scrollToSegment(fileId, segmentId)
  }
}


interface PdfImageCitation {
  fileId: string
  fileName: string
  imageName: string
  imageIndex?: number
  page?: number
}

async function jumpToPdfImageLocation(citation: PdfImageCitation) {

  await openFilePreview(citation.fileId)


  await nextTick()


  if (isRawViewMode.value && pdfPageInfo.value && citation.page) {

    await nextTick()


    const maxWait = 5000
    const checkInterval = 50
    let waited = 0
    while (waited < maxWait) {
      if (pdfViewerRef.value?.isDocumentLoaded) {
        break
      }
      await new Promise(resolve => setTimeout(resolve, checkInterval))
      waited += checkInterval
    }


    await waitForLayoutStable()


    let bbox: number[] | undefined
    if (pdfPageInfo.value.blocks && citation.imageIndex !== undefined) {
      const imageBlock = pdfPageInfo.value.blocks.find((block: any) =>
        block.extra?.is_image &&
        block.extra?.image_index === citation.imageIndex
      )
      if (imageBlock?.extra?.bbox) {
        bbox = imageBlock.extra.bbox
      }
    }


    if (pdfViewerRef.value) {
      await pdfViewerRef.value.scrollToPageAndHighlightBbox(citation.page, bbox)
    }
  } else if (previewingFileContent.value && citation.imageIndex !== undefined) {

    const imageBlock = previewingFileContent.value.blocks.find(block =>
      block.extra?.is_image &&
      block.extra?.image_index === citation.imageIndex
    )

    if (imageBlock) {
      highlightBlockIds.value = [imageBlock.block_id]
      currentBlockIds.value = [imageBlock.block_id]
      await nextTick()
      scrollToBlock(imageBlock.block_id)
    } else if (citation.page) {


    }
  }
}


async function scrollToSegment(_fileId: string, segmentId: string) {

  let blockIds: string[] = []
  if (pdfPageInfo.value) {
    const segment = pdfPageInfo.value.segments.find((s: { segment_id: string }) => s.segment_id === segmentId)
    if (segment) blockIds = segment.block_ids
  } else if (previewingFileContent.value) {
    const segment = previewingFileContent.value.segments.find(s => s.segment_id === segmentId)
    if (segment) blockIds = segment.block_ids
  }

  if (blockIds.length === 0) return


  currentBlockIds.value = blockIds

  if (isRawViewMode.value && pdfPageInfo.value) {


    await nextTick()


    const maxWait = 5000
    const checkInterval = 50
    let waited = 0
    while (waited < maxWait) {
      if (pdfViewerRef.value?.isDocumentLoaded) {
        break
      }
      await new Promise(resolve => setTimeout(resolve, checkInterval))
      waited += checkInterval
    }


    await waitForLayoutStable()

    if (pdfViewerRef.value) {
      await pdfViewerRef.value.scrollToSegment(segmentId)
    }
  } else if (previewingFileContent.value) {

    await new Promise(resolve => setTimeout(resolve, 100))
    highlightBlockIds.value = blockIds
    await nextTick()
    const firstBlockId = blockIds[0]
    if (firstBlockId) {
      scrollToBlock(firstBlockId)
    }
  }
}


async function waitForLayoutStable(maxWait = 500): Promise<void> {
  const previewContent = previewContentRef.value
  if (!previewContent) {

    await new Promise(resolve => setTimeout(resolve, 300))
    return
  }

  let lastWidth = previewContent.clientWidth
  let lastHeight = previewContent.clientHeight
  let stableCount = 0
  const startTime = Date.now()

  while (Date.now() - startTime < maxWait) {
    await new Promise<void>(resolve => requestAnimationFrame(() => resolve()))

    const currentWidth = previewContent.clientWidth
    const currentHeight = previewContent.clientHeight

    if (currentWidth === lastWidth && currentHeight === lastHeight) {
      stableCount++

      if (stableCount >= 3) {
        return
      }
    } else {
      stableCount = 0
      lastWidth = currentWidth
      lastHeight = currentHeight
    }
  }
}


async function switchViewMode(mode: 'raw' | 'parsed') {
  if (mode === viewMode.value || !previewingFile.value) return

  const fileId = previewingFile.value.id
  const savedPageNum = currentPageNum.value
  const savedBlockIds = currentBlockIds.value

  viewMode.value = mode

  try {
    if (mode === 'raw') {


      isLoadingContent.value = true


      previewingFileContent.value = null
      highlightBlockIds.value = []


      currentPageNum.value = savedPageNum


      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 200))


      if (savedBlockIds.length > 0 && pdfPageInfo.value) {

        const segment = pdfPageInfo.value.segments.find(s =>
          s.block_ids.some(bid => savedBlockIds.includes(bid))
        )
        if (segment && pdfViewerRef.value) {
          await pdfViewerRef.value.scrollToSegment(segment.segment_id)
        }
      } else if (pdfViewerRef.value) {

        pdfViewerRef.value.goToPage(savedPageNum)
      }
    } else {

      isLoadingContent.value = true


      const content = await loadFileContent(fileId)
      if (content) {
        previewingFileContent.value = content
      }


      if (savedBlockIds.length > 0) {
        highlightBlockIds.value = savedBlockIds


        try {
          const locationResponse = await getBlocksLocation(fileId, savedBlockIds)
          const firstBlockId = savedBlockIds[0]
          if (firstBlockId) {
            const location = locationResponse.blocks[firstBlockId]
            if (location && location.exists) {
              currentPageNum.value = location.page
            }
          }
        } catch (error) {
          console.error('Failed to get block location:', error)
        }


        await nextTick()
        await new Promise(resolve => setTimeout(resolve, 100))
        const firstBlockId = savedBlockIds[0]
        if (firstBlockId) {
          scrollToBlock(firstBlockId)
        }
      }
    }
  } catch (error) {
    console.error('Failed to switch view mode:', error)
  } finally {


    if (viewMode.value !== 'raw') {
      isLoadingContent.value = false
    }
  }
}

function closePreview() {
  isPreviewMode.value = false
  previewingFileContent.value = null
  previewingFileName.value = ''
  previewingFile.value = null
  previewingImageInfo.value = null
  highlightBlockIds.value = []


  isPdfFile.value = false
  supportsRawView.value = false
  viewMode.value = 'raw'
  currentBlockIds.value = []
  pdfPageInfo.value = null
  currentPageNum.value = 1
  jumpToPageInput.value = ''


  if (leftPanelWidthBeforePreview.value !== null) {
    leftPanelWidth.value = leftPanelWidthBeforePreview.value
    leftPanelWidthBeforePreview.value = null
  }
}

function scrollToBlock(blockId: string) {
  if (!previewContentRef.value) return
  const container = previewContentRef.value
  const blockEl = container.querySelector(`[data-block-id="${blockId}"]`) as HTMLElement
  if (blockEl) {


    const containerRect = container.getBoundingClientRect()
    const blockRect = blockEl.getBoundingClientRect()
    const targetScrollTop = container.scrollTop + (blockRect.top - containerRect.top) - (containerRect.height / 2) + (blockRect.height / 2)
    container.scrollTo({ top: targetScrollTop, behavior: 'smooth' })
  }
}


async function jumpToPage() {
  if (currentTotalPages.value === 0 || !previewingFile.value) return

  const pageNum = parseInt(jumpToPageInput.value)
  if (isNaN(pageNum) || pageNum < 1 || pageNum > currentTotalPages.value) {
    jumpToPageInput.value = ''
    return
  }

  currentPageNum.value = pageNum
  jumpToPageInput.value = ''

  if (isRawViewMode.value) {

    pdfViewerRef.value?.goToPage(pageNum)
  } else {

    await nextTick()
    const pageSection = previewContentRef.value?.querySelector(`[data-page="${pageNum}"]`) as HTMLElement
    if (pageSection) {
      pageSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }
}


function handlePreviewScroll() {

  if (isRawViewMode.value) return
  if (!previewContentRef.value || !isPdfFile.value || currentTotalPages.value === 0) return


  if (copyPanelVisible.value) {
    clearSelectedBlock()
  }

  const container = previewContentRef.value
  const containerRect = container.getBoundingClientRect()
  const containerTop = containerRect.top


  const pageSections = container.querySelectorAll('[data-page]')
  let currentVisiblePage = 1

  for (const section of pageSections) {
    const rect = section.getBoundingClientRect()

    if (rect.top <= containerTop + containerRect.height / 2) {
      currentVisiblePage = parseInt(section.getAttribute('data-page') || '1')
    }
  }

  if (currentVisiblePage !== currentPageNum.value) {
    currentPageNum.value = currentVisiblePage
  }
}

function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    pending: '等待处理',
    processing: '处理中',
    ready: '就绪',
    error: '错误',
    failed: '解析失败'
  }
  return statusMap[status] || status
}


function handleKeywordClick(keyword: string) {
  if (!currentSession.value || isStreaming.value) return


  inputMessage.value = `请你根据已有的文档内容，研究「${keyword}」`
  nextTick(() => {
    sendMessage()
  })
}


function autoResizeTextarea() {
  const textarea = textareaRef.value
  if (!textarea) return


  textarea.style.height = 'auto'


  const maxHeight = 150
  const newHeight = Math.min(textarea.scrollHeight, maxHeight)
  textarea.style.height = newHeight + 'px'


  updateScrollBtnPosition()
}

function updateScrollBtnPosition() {
  const wrapper = inputWrapperRef.value
  if (wrapper) {
    scrollBtnBottom.value = wrapper.offsetHeight + 20
  }
}


function resetTextareaHeight() {
  const textarea = textareaRef.value
  if (textarea) {
    textarea.style.height = 'auto'
  }

  nextTick(() => updateScrollBtnPosition())
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
          content: hasPartial ? undefined : `⚠️ 生成失败：${error}`,
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


function processUnresolvedCitations(text: string): string {
  const unresolvedHtml = (displayNum: string) =>
    `<span class="inline-citation segment-citation disabled unresolved" data-citation-type="segment">${displayNum}</span>`


  let processed = text.replace(/\[citation:([^\]]+)\]/gi, (_match, value) => {
    const trimmed = String(value || '').trim()
    const displayNum = /^\d+$/.test(trimmed) ? trimmed : 'x'
    return unresolvedHtml(displayNum)
  })


  processed = processed.replace(/\bcitation_([a-z0-9]+)\b/gi, (_match, value) => {
    const trimmed = String(value || '').trim()
    const displayNum = /^\d+$/.test(trimmed) ? trimmed : 'x'
    return unresolvedHtml(displayNum)
  })

  return processed
}

type RenderedSegmentType = 'thinking' | 'tool' | 'body'
type RenderedSegment = { type: RenderedSegmentType; html: string }


interface ReasoningExpandState {
  shouldExpand: boolean
  isStreaming: boolean
}


function analyzeReasoningExpandStates(
  parts: ContentPart[],
  isStreamingMode: boolean,
  messageId: string
): Map<number, ReasoningExpandState> {
  const states = new Map<number, ReasoningExpandState>()
  if (!parts || parts.length === 0) return states

  let reasoningBlockIndex = 0

  for (let i = 0; i < parts.length; i++) {
    const part = parts[i]
    if (!part || part.type !== 'reasoning') continue

    const blockId = messageId ? `${messageId}_reasoning_${reasoningBlockIndex++}` : ''


    const userExpanded = blockId && userExpandedThinkingBlocks.has(blockId)


    let hasContentAfter = false
    for (let j = i + 1; j < parts.length; j++) {
      const nextPart = parts[j]
      if (!nextPart) continue

      if (nextPart.type === 'text') {
        const text = 'content' in nextPart && typeof (nextPart as any).content === 'string' ? (nextPart as any).content : ''

        const parsed = parseThinkingContent(text)
        if (parsed.content && parsed.content.trim() !== '') {
          hasContentAfter = true
          break
        }
      } else if (nextPart.type === 'citation_ref') {

        hasContentAfter = true
        break
      }

    }


    const autoExpand = isStreamingMode && !hasContentAfter
    const shouldExpand = userExpanded || autoExpand


    const isStreaming = isStreamingMode && !hasContentAfter

    states.set(i, {
      shouldExpand,
      isStreaming
    })
  }

  return states
}


function renderContentParts(parts: ContentPart[], isStreamingMode: boolean = false, messageId: string = ''): RenderedSegment[] {
  if (!parts || parts.length === 0) return []


  const segments: RenderedSegment[] = []
  let currentText = ''
  let thinkingBlockIndex = 0


  const reasoningExpandStates = analyzeReasoningExpandStates(parts, isStreamingMode, messageId)

  for (let i = 0; i < parts.length; i++) {
    const part = parts[i]
    if (!part) continue

    if (part.type === 'text') {
      const content = 'content' in part && typeof (part as any).content === 'string' ? (part as any).content : ''
      if (content.trim() === '') {
        if (content.includes('\n')) {
          continue
        }
        if (currentText && !currentText.endsWith(' ')) {
          currentText += ' '
        }
        continue
      }
      currentText += content
    } else if (part.type === 'reasoning') {


      if (currentText) {
        renderTextWithThinking(currentText, isStreamingMode)
        currentText = ''
      }

      const reasoningContent = 'content' in part && typeof (part as any).content === 'string' ? (part as any).content : ''
      if (reasoningContent) {
        const blockId = messageId ? `${messageId}_reasoning_${thinkingBlockIndex++}` : ''

        const expandState = reasoningExpandStates.get(i)
        const shouldExpand = expandState?.shouldExpand ?? isStreamingMode
        const isStreaming = expandState?.isStreaming ?? isStreamingMode

        segments.push({
          type: 'thinking',
          html: renderThinkingBlock(reasoningContent, shouldExpand, isStreaming, blockId, localizedThinkingLabel())
        })
      }
    } else if (part.type === 'citation_ref') {

      const partAny = part as any

      if (partAny.citation_type === 'web') {

        const title = partAny.title || ''
        const url = partAny.url || ''
        const snippet = partAny.snippet || ''
        const source = partAny.source || ''
        const publishedDate = partAny.published_date || ''
        const favicon = partAny.favicon || ''

        const iconHtml = favicon
          ? `<img class="web-favicon" src="${escapeHtml(favicon)}" width="12" height="12" onerror="this.style.display='none';this.nextElementSibling.style.display='inline'" /><svg class="web-icon" style="display:none" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>`
          : `<svg class="web-icon" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>`
        currentText += `<span class="inline-citation web-citation" data-citation-type="web" data-title="${escapeHtml(title)}" data-url="${escapeHtml(url)}" data-snippet="${escapeHtml(snippet)}" data-source="${escapeHtml(source)}" data-date="${escapeHtml(publishedDate)}" data-favicon="${escapeHtml(favicon)}">${partAny.display_num}${iconHtml}</span>`
      } else if (partAny.citation_type === 'image') {

        const fileId = partAny.file_id || ''
        const fileName = partAny.file_name || ''
        const imageName = partAny.image_name || ''
        const imageIndex = partAny.image_index ?? ''
        const page = partAny.page ?? ''
        currentText += `<span class="inline-citation image-citation" data-citation-type="image" data-file-id="${escapeHtml(fileId)}" data-file="${escapeHtml(fileName)}" data-image-name="${escapeHtml(imageName)}" data-image-index="${imageIndex}" data-page="${page}">${partAny.display_num}</span>`
      } else {


        const segmentId = partAny.segment_id || ''
        const disabledClass = segmentId ? '' : ' disabled'
        currentText += `<span class="inline-citation segment-citation${disabledClass}" data-citation-type="segment" data-display-num="${partAny.display_num}" data-file="${escapeHtml(partAny.file_name || '')}" data-segment-id="${escapeHtml(segmentId)}">${partAny.display_num}</span>`
      }
    } else if (part.type === 'tool_status') {

      if (currentText) {
        renderTextWithThinking(currentText, isStreamingMode)
        currentText = ''
      }

      segments.push({ type: 'tool', html: `<div class="tool-status-item">${escapeHtml(translateText(part.display))}</div>` })
    }
  }


  if (currentText) {
    renderTextWithThinking(currentText, isStreamingMode)
  }


  function renderTextWithThinking(text: string, isStreamingMode: boolean) {
    if (ENABLE_THINK_PARSING) {
      const { thinking, content, isThinkingComplete } = parseThinkingContent(text)


      if (thinking) {

        const blockId = messageId ? `${messageId}_think_${thinkingBlockIndex++}` : ''


        const userExpanded = blockId && userExpandedThinkingBlocks.has(blockId)
        const autoExpand = isStreamingMode && !content && !isThinkingComplete
        const shouldExpand = userExpanded || autoExpand

        segments.push({ type: 'thinking', html: renderThinkingBlock(thinking, shouldExpand, isStreamingMode && !isThinkingComplete, blockId, localizedThinkingLabel()) })
      }


      if (content) {
        segments.push({ type: 'body', html: renderMarkdownWithLatex(processUnresolvedCitations(content)) })
      }
    } else {
      segments.push({ type: 'body', html: renderMarkdownWithLatex(processUnresolvedCitations(text)) })
    }
  }

  return segments
}


function renderMessageWithError(msg: Message): RenderedSegment[] {
  const parsed = parseMessageContent(msg)

  if (!parsed.hasError) {

    return renderContentParts(getMessageParts(msg), false, msg.id)
  }


  const segments: RenderedSegment[] = []
  const appendBodyHtml = (html: string) => {
    if (!html) return
    const last = segments[segments.length - 1]
    if (last && last.type === 'body') {
      last.html += html
    } else {
      segments.push({ type: 'body', html })
    }
  }


  if (parsed.mainContent) {
    if (parsed.hasPartial) {

      const parts = getMessageParts(msg)
      segments.push(...renderContentParts(parts, false, msg.id))
    } else {

      appendBodyHtml(`<div class="error-placeholder">${escapeHtml(parsed.mainContent)}</div>`)
    }
  }


  if (parsed.systemHint) {
    const icon = parsed.hasPartial ? '⚠️' : '❌'
    appendBodyHtml(`
      <div class="system-hint ${parsed.hasPartial ? 'warning' : 'error'}">
        <span class="hint-icon">${icon}</span>
        <span class="hint-text">${escapeHtml(parsed.systemHint)}</span>
      </div>
    `)
  }

  return segments
}


const streamingRendered = computed(() => {
  return renderContentParts(streamingParts.value, true, 'streaming')
})

const renderedMessages = computed<Record<string, RenderedSegment[]>>(() => {
  const map: Record<string, RenderedSegment[]> = {}
  for (const msg of messages.value) {
    if (msg.role === 'assistant' && msg.id) {
      map[msg.id] = renderMessageWithError(msg)
    }
  }
  return map
})

const emptyRenderedMessage: RenderedSegment[] = []

function getRenderedMessage(msg: Message): RenderedSegment[] {
  if (!msg.id) return emptyRenderedMessage
  return renderedMessages.value[msg.id] || emptyRenderedMessage
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


function getMessageTextContent(msg: Message): string {
  const parts = getMessageParts(msg)
  let text = ''

  for (const part of parts) {
    if (part.type === 'text') {
      text += part.content
    }

  }


  const parsed = parseThinkingContent(text)
  text = parsed.content


  text = text.replace(/\[\[?\d+\]?\]/g, '')

  text = text.replace(/  +/g, ' ').trim()

  return text
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
            file_name: citation.file_name
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
          content: hasPartial ? undefined : `⚠️ 生成失败：${error}`,
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

function getMessageParts(msg: Message): ContentPart[] {
  const parts: ContentPart[] = []

  if (msg.reasoning_content && msg.reasoning_content.trim()) {
    parts.push({ type: 'reasoning', content: msg.reasoning_content })
  }

  if (msg.content_parts && msg.content_parts.length > 0) {
    parts.push(...msg.content_parts)
  } else if (msg.content) {
    parts.push({ type: 'text', content: msg.content })
  }

  const hasToolStatusInParts = parts.some(p => p.type === 'tool_status')

  if (!hasToolStatusInParts && msg.tool_executing && msg.tool_executing.length > 0) {
    for (const tool of msg.tool_executing) {
      parts.push({ type: 'tool_status', display: tool.display })
    }
  }

  return parts
}

function isToolOnlyMessage(msg: Message): boolean {
  const parts = getMessageParts(msg)
  if (!parts || parts.length === 0) return false

  let hasToolStatus = false
  for (const part of parts) {
    if (part.type === 'tool_status') {
      if (part.display && part.display.trim() !== '') {
        hasToolStatus = true
      }
      continue
    }
    if (part.type === 'text') {
      const text = part.content || ''
      if (text.trim() !== '') {
        const parsed = parseThinkingContent(text)
        if (parsed.content && parsed.content.trim() !== '') {
          return false
        }
      }
      continue
    }
    return false
  }

  return hasToolStatus
}

function parseMessageContent(msg: Message): {
  hasError: boolean
  hasPartial: boolean
  mainContent: string
  systemHint: string | null
} {
  const hasError = !!msg._error || (msg.content && msg.content.includes('[系统提示：'))

  if (!hasError) {
    return {
      hasError: false,
      hasPartial: false,
      mainContent: msg.content || '',
      systemHint: null
    }
  }

  const content = msg.content || ''
  const systemHintMatch = content.match(/\[系统提示：([^\]]+)\]/)

  if (systemHintMatch) {
    const systemHint = systemHintMatch?.[1] ?? null
    const mainContent = content.replace(/\[系统提示：[^\]]+\]/, '').trim()

    const hasPartial = !mainContent.startsWith('⚠️')

    return {
      hasError: true,
      hasPartial,
      mainContent,
      systemHint
    }
  }

  return {
    hasError: true,
    hasPartial: !!msg.has_partial,
    mainContent: content,
    systemHint: null
  }
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
          content: hasPartial ? undefined : `⚠️ 生成失败：${error}`,
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

function scrollToBottom() {
  if (messagesRef.value && !isUserScrolling.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    showScrollToBottom.value = false
  }
}

function forceScrollToBottom() {
  if (messagesRef.value) {
    isUserScrolling.value = false
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    showScrollToBottom.value = false
  }
}

function handleMessagesScroll() {
  if (!messagesRef.value) return

  const { scrollTop, scrollHeight, clientHeight } = messagesRef.value
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight

  if (distanceFromBottom > 100) {
    isUserScrolling.value = true
    showScrollToBottom.value = true
  } else {
    isUserScrolling.value = false
    showScrollToBottom.value = false
  }

  if (scrollTop < 50 && hasMoreMessages.value && !isLoadingMoreMessages.value) {
    loadOlderMessages()
  }
}

function goBack() {
  router.push('/')
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
      await updateFile(renameModal.id, { file_name: newName })
      const file = files.value.find(f => f.id === renameModal.id)
      if (file) file.file_name = newName
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
    nextTick(() => {
      if (messagesRef.value) {
        messagesRef.value.scrollTop = messagesRef.value.scrollHeight
      }
    })
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
  nextTick(() => {
    sessionTitleInputRef.value?.focus()
    sessionTitleInputRef.value?.select()
  })
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

function handleSessionTitleBlur() {
  if (!isSessionTitleComposing.value) {
    saveSessionTitle()
  }
}

function handleSessionTitleEnter() {
  if (!isSessionTitleComposing.value) {
    saveSessionTitle()
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

function openWorkflowConfig(type: string) {
  if (!hasReadyFiles.value) return
  const titleMap: Record<string, string> = {
    research_brief: '一键生成研究简报',
    content_plan: '一键生成内容方案',
    design_brief: '一键生成设计简报',
    overview_brief: '一键生成文档概览',
    communication_plan: '一键生成传播方案'
  }
  workflowConfigModal.workflowType = type
  workflowConfigModal.workflowTitle = titleMap[type] || '一键生成'
  workflowConfigModal.visible = true
}

function closeWorkflowConfig() {
  workflowConfigModal.visible = false
  workflowConfigModal.workflowType = ''
  workflowConfigModal.workflowTitle = ''
}

async function handleWorkflowConfigConfirm(workflowType: string, title: string, prompt: string, fileIds: string[]) {
  closeWorkflowConfig()
  await handleOneclickWorkflow(workflowType, title, prompt, fileIds)
}

async function handleOneclickWorkflow(workflowType: string, title: string, prompt: string, fileIds: string[]) {
  if (fileIds.length === 0) return

  const displayNameMap: Record<string, string> = {
    research_brief: '研究简报',
    content_plan: '内容方案',
    design_brief: '设计简报',
    overview_brief: '文档概览',
    communication_plan: '传播方案'
  }
  const displayName = displayNameMap[workflowType] || '工作流'

  try {
    await createWorkflow(projectId, workflowType, title, {
      prompt,
      file_ids: fileIds
    })

    await loadWorkflows()


    showToast(`正在生成${displayName}...`, 'success')
  } catch (error) {
    console.error('创建工作流失败:', error)
    showToast('创建任务失败，请稍后重试', 'error')
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
        showToast('状态获取失败，请刷新页面', 'error')
      }
      return
    }

    pollErrorCount = 0

    const shouldRefreshDetail = showWorkflowDetail.value &&
      currentWorkflow.value?.id === workflowId &&
      currentWorkflow.value?.status !== status.status

    if (currentWorkflow.value?.id === workflowId) {
      currentWorkflow.value.status = status.status
    }

    if (status.status === 'pending' || status.status === 'processing') {
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
      showToast('生成完成', 'success')
    } else if (status.status === 'partial') {
      showToast('部分内容生成完成', 'info')
    } else if (status.status === 'failed') {
      showToast('生成失败，请重试', 'error')
    }
  } catch (error) {
    console.error('获取工作流状态失败:', error)
    pollErrorCount++
    if (pollErrorCount >= MAX_POLL_ERRORS) {
      stopWorkflowPolling()
      workflowLoading.value = false
      showToast('网络连接不稳定，请刷新页面重试', 'error')
    }
  }
}

async function loadWorkflows() {
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
    showToast('获取详情失败', 'error')
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
  const workflowTitle = currentWorkflow.value.title || currentWorkflow.value.display_name
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
      showToast('该步骤不存在，无法重新生成', 'error')
    } else {
      showToast('获取步骤配置失败，请稍后重试', 'error')
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
    showToast(`已重新生成：${result.step_name}`, 'success')
    await loadWorkflows()
    await refreshWorkflowDetail(workflowId)
  } catch (error) {
    console.error('重新生成步骤失败:', error)
    showToast('重新生成失败，请稍后重试', 'error')
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

  if (citationType === 'image') {
    const fileId = citationMeta?.file_id
    const imageName = citationMeta?.image_name

    if (imageName && fileId) {
      await jumpToPdfImageLocation({
        fileId,
        fileName: citationMeta?.file_name || '',
        imageName,
        imageIndex: citationMeta?.image_index,
        page: citationMeta?.page
      })
    } else if (fileId) {
      openImageCitationModal({
        fileId,
        fileName: citationMeta?.file_name || '',
        previewUrl: getImagePreviewUrl(fileId)
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
    title: '确认删除',
    message: '确定要删除这个生成记录吗？',
    type: 'danger'
  })
  if (!confirmed) return

  try {
    await deleteWorkflow(workflowId)
    if (currentWorkflow.value?.id === workflowId) {
      currentWorkflow.value = null
    }
    await loadWorkflows()
    showToast('已删除', 'success')
  } catch (error) {
    console.error('删除工作流失败:', error)
    showToast('删除失败', 'error')
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
      showToast('已成功定稿', 'success')
      await loadWorkflows()
    }
  } catch (error) {
    console.error('Finalize failed:', error)
    showToast('定稿失败', 'error')
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
    showToast('重命名失败', 'error')
  }
}

function getWorkflowStatusText(status: WorkflowStatus): string {
  const map: Record<WorkflowStatus, string> = {
    pending: '等待中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败',
    partial: '部分完成'
  }
  return map[status] || status
}

function getWorkflowStatusClass(status: WorkflowStatus): string {
  const map: Record<WorkflowStatus, string> = {
    pending: 'status-pending',
    processing: 'status-processing',
    completed: 'status-completed',
    failed: 'status-failed',
    partial: 'status-partial'
  }
  return map[status] || ''
}

function getWorkflowIconColorClass(workflowType: string): string {
  const colorMap: Record<string, string> = {
    research_brief: 'icon-purple',
    content_plan: 'icon-blue',
    design_brief: 'icon-teal',
    overview_brief: 'icon-green',
    communication_plan: 'icon-orange'
  }
  return colorMap[workflowType] || 'icon-default'
}

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`

  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${month}月${day}日`
}

function formatMessageTime(isoString: string): string {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()

  const isToday = date.getFullYear() === now.getFullYear() &&
                  date.getMonth() === now.getMonth() &&
                  date.getDate() === now.getDate()

  if (isToday) {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const seconds = date.getSeconds().toString().padStart(2, '0')
    return `${hours}:${minutes}:${seconds}`
  } else {
    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    const weekDay = weekDays[date.getDay()]
    return `${month}/${day} ${weekDay}`
  }
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
  handleDeleteWorkflow,
  handleFinalizeWorkflow,
  handleRegenerateFeature,
  handleDeleteFeature,
  getWorkflowStatusText,
  getWorkflowStatusClass,
  getWorkflowIconColorClass,
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


.sources-panel {
  background: var(--bg-white);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  transition: width 0.2s ease;
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


.sources-panel.collapsed,
.studio-panel.collapsed {
  padding: 0;
  border: none;
  overflow: hidden;
  min-width: 0;
}

.sources-panel.collapsed > *,
.studio-panel.collapsed > * {
  display: none;
}

.add-source-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 12px 20px;
  padding: 12px 20px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 24px;
  color: var(--text-primary);
  font-size: 15px;
}

.add-source-btn:hover {
  background: var(--bg-hover);
}


.select-all-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 28px 8px 16px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
}

.select-all-row:hover {
  background: var(--bg-hover);
}

.select-all-check {
  position: relative;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1.5px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-tertiary);
  transition: all 0.15s;
}


.select-all-check::before {
  content: '';
  position: absolute;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: transparent;
  transition: background 0.15s;
}

.select-all-row:hover .select-all-check::before {
  background: rgba(0, 0, 0, 0.04);
}

.select-all-row:hover .select-all-check {
  border-color: var(--text-tertiary);
}

.select-all-check.checked {
  background: var(--text-tertiary);
  border-color: var(--text-tertiary);
  color: white;
}

.select-all-row:hover .select-all-check.checked::before {
  background: rgba(0, 0, 0, 0.06);
}

.sources-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.empty-sources {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
  font-size: 13px;
}

.empty-sources .empty-icon {
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.empty-sources p {
  font-size: 14px;
  margin-bottom: 10px;
}

.empty-sources .hint {
  font-size: 13px;
  color: var(--text-tertiary);
}

.source-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.3s;
  position: relative;
}

.source-item:hover {
  background: var(--bg-hover);
}


.source-item.ready:hover {
  background: var(--bg-hover);
}


.source-item.pending {
  cursor: not-allowed;
  background: rgba(0, 0, 0, 0.03);
}

.source-item.pending:hover {
  background: rgba(0, 0, 0, 0.05);
}


.source-item.processing {
  cursor: not-allowed;
  background: linear-gradient(
    90deg,
    rgba(74, 155, 168, 0.05) 0%,
    rgba(74, 155, 168, 0.12) 50%,
    rgba(74, 155, 168, 0.05) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 2s ease-in-out infinite;
}

.source-item.processing:hover {
  background: linear-gradient(
    90deg,
    rgba(74, 155, 168, 0.08) 0%,
    rgba(74, 155, 168, 0.15) 50%,
    rgba(74, 155, 168, 0.08) 100%
  );
  background-size: 200% 100%;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}


.source-left {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.source-icon {
  color: #1a73e8;
  flex-shrink: 0;
}

.source-icon.image-icon {
  color: #34a853;
}

.source-icon.audio-icon {
  color: #9333ea;
}


.source-checkbox {
  position: relative;
  width: 18px;
  height: 18px;
  border: 1.5px solid var(--border-color);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  background: transparent;
  cursor: pointer;
}


.source-checkbox::before {
  content: '';
  position: absolute;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: transparent;
  transition: background 0.15s;
}

.source-checkbox:hover::before {
  background: rgba(0, 0, 0, 0.04);
}

.source-checkbox:hover {
  border-color: var(--text-tertiary);
}

.source-checkbox.checked {
  background: var(--text-tertiary);
  border-color: var(--text-tertiary);
  color: white;
}

.source-checkbox.checked:hover::before {
  background: rgba(0, 0, 0, 0.06);
}

.source-right {
  cursor: pointer;
}


.source-menu-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.source-menu-btn:hover {
  background: var(--bg-active);
  color: var(--text-primary);
}


.source-menu-wrapper {
  position: relative;
}


.source-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  min-width: 120px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}

.dropdown-item:hover:not(.disabled) {
  background: var(--bg-hover);
}

.dropdown-item.disabled {
  color: var(--text-disabled);
  cursor: not-allowed;
}


.source-right {
  flex-shrink: 0;
  margin-left: auto;
}


.preview-file-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.preview-file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 0;
  flex: 1;
}

.preview-file-name span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-file-name svg {
  color: #1a73e8;
  flex-shrink: 0;
}


.view-toggle {
  display: flex;
  gap: 4px;
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 3px;
  flex-shrink: 0;
}

.view-toggle-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.view-toggle-btn:hover {
  color: var(--text-primary);
  background: rgba(0, 0, 0, 0.04);
}

.view-toggle-btn.active {
  background: white;
  color: var(--primary-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.view-toggle-btn svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}


.source-guide-card {
  margin: 12px 16px;
  border: 1.5px dashed rgba(0, 0, 0, 0.12);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(249, 250, 251, 0.8) 0%, rgba(243, 244, 246, 0.6) 100%);
  overflow: hidden;
}

.source-guide-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px 8px;
}

.source-guide-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.source-guide-title svg {
  color: var(--primary-color);
  width: 20px;
  height: 20px;
}

.source-guide-toggle {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.source-guide-toggle svg {
  width: 22px;
  height: 22px;
}

.source-guide-toggle:hover {
  background: rgba(0, 0, 0, 0.08);
  color: var(--text-secondary);
}

.source-guide-toggle svg {
  transition: transform 0.2s;
}

.source-guide-toggle svg.rotated {
  transform: rotate(-90deg);
}

.source-guide-content {
  padding: 0 14px 14px;
  font-size: 14px;
  line-height: 1.8;
  color: #1a1a1a;
}

.source-guide-content :deep(strong) {
  color: #1a5c5c;
  font-weight: 600;
}

.source-guide-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 4px 14px 14px;
}

.keyword-tag {
  display: inline-block;
  padding: 4px 12px;
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.15s;
}

.keyword-tag:hover {
  background: var(--primary-light);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  scroll-behavior: smooth;
}


.preview-content-wrapper {
  position: relative;
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}


.page-nav-float {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 10;
  backdrop-filter: blur(8px);
}

.page-nav-float .page-indicator {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

.page-nav-float .page-jump {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-nav-float .page-jump input {
  width: 50px;
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 12px;
  text-align: center;
  background: var(--bg-white);
  color: var(--text-primary);
}

.page-nav-float .page-jump input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.page-nav-float .page-jump input::-webkit-outer-spin-button,
.page-nav-float .page-jump input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.page-nav-float .page-jump input[type=number] {
  -moz-appearance: textfield;
}

.page-nav-float .jump-btn {
  padding: 4px 10px;
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.page-nav-float .jump-btn:hover {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}


.pdf-page-section {
  margin-bottom: 24px;
}


.parsed-page-section {
  margin-bottom: 24px;
}

.parsed-page-content {
  padding: 0 4px;
}

.pdf-page-container {
  display: flex;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.pdf-page-wrapper {
  position: relative;
  display: inline-block;
  max-width: 100%;
}

.pdf-canvas {
  display: block;
  max-width: 100%;
  height: auto;
}


.pdf-highlight-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.pdf-highlight-box {
  position: absolute;
  border: 2px solid #8b5cf6;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 2px;
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.4);
  animation: highlight-pulse 1.5s ease-in-out infinite;
}

@keyframes highlight-pulse {
  0%, 100% {
    box-shadow: 0 0 8px rgba(139, 92, 246, 0.4);
  }
  50% {
    box-shadow: 0 0 16px rgba(139, 92, 246, 0.6);
  }
}


.pdf-selected-block-highlight {
  position: absolute;
  border: 2px solid #10b981;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 2px;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
  pointer-events: auto;
  cursor: default;
}


.block-copy-panel-floating {
  position: fixed;
  z-index: 10000;
  pointer-events: auto;
}

.copy-panel-content {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  max-width: 320px;
  overflow: hidden;
}

.copy-panel-text {
  padding: 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  max-height: 150px;
  overflow-y: auto;
  border-bottom: 1px solid var(--border-color);
  word-break: break-word;
}

.copy-panel-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-secondary);
}

.copy-panel-actions .copy-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.copy-panel-actions .copy-btn:hover {
  background: var(--primary-hover);
}

.copy-panel-actions .close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.copy-panel-actions .close-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}


@media (max-width: 600px) {
  .block-copy-panel-floating {

  }
}


.pdf-page-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-tertiary);
  font-size: 13px;
}


.page-section {
  margin-bottom: 16px;
}

.page-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0 16px;
  padding: 0 4px;
}

.page-divider:first-child {
  margin-top: 0;
}

.page-divider-line {
  flex: 1;
  height: 1px;
  background: var(--border-color);
}

.page-divider-text {
  font-size: 12px;
  color: var(--text-tertiary);
  white-space: nowrap;
}


.page-loading,
.page-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.page-placeholder {
  cursor: pointer;
  background: var(--bg-hover);
  border-radius: 8px;
  transition: background 0.15s;
}

.page-placeholder:hover {
  background: var(--bg-active);
  color: var(--text-secondary);
}


.image-preview-content {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 20px;
}

.image-preview-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 600px;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-loading {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.preview-loading::before {
  content: '';
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: loadingSpin 0.8s linear infinite;
}

@keyframes loadingSpin {
  to {
    transform: rotate(360deg);
  }
}


.image-description-card {
  margin-top: 20px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.image-description-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.image-description-header svg {
  color: var(--primary-color);
}

.vlm-model-tag {
  margin-left: auto;
  padding: 2px 8px;
  font-size: 12px;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  border-radius: 4px;
}

.image-description-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
}


.audio-block {
  margin-bottom: 12px;
  line-height: 1.6;
  padding: 2px 8px;
  border-radius: 4px;
  transition: background 0.3s;
}

.audio-block.highlighted {
  background: rgba(147, 51, 234, 0.1);
  animation: highlightFadeIn 0.3s ease-out;
}

.audio-meta {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-right: 8px;
  font-family: monospace;
}

.audio-text {
  color: var(--text-primary);
  font-size: 14px;
}

.preview-block {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #1a1a1a;
  font-size: 14px;
  transition: background 0.3s;
  padding: 2px 8px;
  border-radius: 4px;
}

.preview-block.heading {
  font-size: 18px;
  font-weight: 600;
  margin-top: 16px;
  margin-bottom: 8px;
}

.preview-block.quote {
  border-left: 3px solid var(--primary-color);
  padding-left: 12px;
  color: var(--text-secondary);
  font-style: italic;
}


.preview-block.table-block {
  margin: 16px 0;
  padding: 0;
  overflow-x: auto;
}

.table-caption {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding: 0 8px;
}

.table-content {
  overflow-x: auto;
}

.table-content table {
  border-collapse: collapse;
  width: 100%;
  font-size: 13px;
}

.table-content td,
.table-content th {
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  text-align: left;
  vertical-align: top;
}

.table-content th {
  background: var(--bg-secondary);
  font-weight: 600;
}

.table-content tr:nth-child(even) {
  background-color: var(--bg-main);
}

.table-content tr:hover {
  background-color: var(--bg-hover);
}

.table-footnote {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 6px;
  padding: 0 8px;
}

.preview-block.table-block.highlighted .table-content table {
  background: rgba(216, 180, 254, 0.2);
}


.preview-block.highlighted {
  animation: highlightFadeIn 0.3s ease-out;
}


.highlight-text {
  background: rgba(216, 180, 254, 0.5);
  box-decoration-break: clone;
  -webkit-box-decoration-break: clone;
  padding: 0 4px;
  border-radius: 3px;
  font-weight: 700;
}

@keyframes highlightFadeIn {
  0% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}

.source-info {
  flex: 1;
  min-width: 0;
}

.source-name {
  display: block;
  font-size: 14px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-status {
  font-size: 12px;
  color: var(--text-tertiary);
}

.source-status.ready {
  color: var(--success-color);
}

.source-status.processing {
  color: var(--primary-color);
}

.source-status.error {
  color: var(--error-color);
}

.source-status.failed {
  color: var(--error-color);
}

.source-status-reason {
  margin-left: 6px;
  color: var(--text-tertiary);
  white-space: nowrap;
}


.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-white);
  border-radius: 16px;
  min-width: 400px;
  position: relative;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
}

.session-title-wrapper {
  flex: 1;
  min-width: 0;
}

.chat-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.15s;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.chat-title:hover {
  background: var(--bg-hover);
}

.session-title-input {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  padding: 4px 8px;
  border: 1px solid var(--primary-color);
  border-radius: 6px;
  outline: none;
  background: var(--bg-white);
  width: 280px;
  max-width: 100%;
}

.chat-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.header-action-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.header-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--text-secondary);
}


.loading-more-messages,
.load-more-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.loading-more-messages .loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.load-more-hint {
  opacity: 0.6;
}

.empty-upload-icon {
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.chat-empty h3 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
}

.greeting-message {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 1px;
}

.upload-btn {
  padding: 10px 20px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  color: var(--text-primary);
  font-size: 14px;
}

.upload-btn:hover {
  background: var(--bg-hover);
}


.message {
  margin-bottom: 14px;
  position: relative;
  transition: all 0.2s;
}

.message.selection-mode {
  padding-left: 40px;
  cursor: pointer;
}

.message.selection-mode.user {
  cursor: pointer;
}


.message.conversation-selected {
  background-color: rgba(0, 127, 255, 0.06);
  margin-left: -8px;
  margin-right: -8px;
  padding-left: 48px;
  padding-right: 8px;
}


.message.conversation-selected.user {
  border-radius: 12px 12px 0 0;
  margin-bottom: 0;
  padding-bottom: 12px;
}


.message.conversation-selected.assistant {
  border-radius: 0 0 12px 12px;
  margin-top: 0;
  padding-top: 12px;
}


.message-selection-check {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 5;
}

.custom-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-white);
  color: #fff;
  transition: all 0.2s;
}

.custom-checkbox.checked {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.user-message.selectable:hover {
  background: var(--bg-hover);
}

.message.assistant + .message.assistant {
  margin-top: 0;
}

.message.assistant.tool-only {
  margin-bottom: 2px;
}

.message.assistant.tool-only + .message.assistant:not(.tool-only) {
  margin-top: 8px;
}

.compact-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 0;
  color: var(--text-tertiary, #999);
  font-size: 12px;

  span {
    background: var(--bg-secondary, #f5f5f5);
    padding: 2px 12px;
    border-radius: 10px;
  }
}

.user-message {
  position: relative;
  max-width: 80%;
  padding: 14px 20px;
  background: var(--bg-main);
  border-radius: 20px 20px 4px 20px;
  color: var(--text-primary);
  float: right;
  clear: both;
  line-height: 1.6;
  letter-spacing: 0.02em;
  text-align: left;
}

.user-message-content {
  white-space: pre-wrap;
  word-break: break-word;
}


.user-action-btns {
  position: absolute;
  left: -60px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s;
}

.message.user:hover .user-action-btns {
  opacity: 1;
  visibility: visible;
}

.user-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.user-action-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-secondary);
}

.user-action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}


.user-action-btn::before,
.user-action-btn::after {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
  pointer-events: none;
}

.user-action-btn::before {
  content: attr(data-tooltip);
  bottom: calc(100% + 6px);
  padding: 4px 8px;
  background: #1f2937;
  color: #fff;
  font-size: 12px;
  font-weight: 400;
  border-radius: 4px;
  white-space: nowrap;
}

.user-action-btn::after {
  content: '';
  bottom: calc(100% + 1px);
  width: 8px;
  height: 4px;
  background: #1f2937;
  clip-path: polygon(50% 100%, 0% 0%, 100% 0%);
}

.user-action-btn:hover::before,
.user-action-btn:hover::after {
  opacity: 1;
  visibility: visible;
}


.user-message.editing {
  width: 80%;
  background: transparent;
  padding: 0;
}

.user-message-edit {
  width: 100%;
}

.user-edit-textarea {
  display: block;
  width: 100%;
  padding: 8px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-white);
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  resize: none;
  font-family: inherit;
  box-sizing: border-box;
  overflow-y: hidden;
  min-height: 60px;
  max-height: 300px;
}

.user-edit-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
}

.user-edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.edit-cancel-btn {
  padding: 6px 14px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-cancel-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.edit-submit-btn {
  padding: 6px 14px;
  background: var(--primary-color);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-submit-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.edit-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message.user {
  text-align: right;
}

.message.user::after {
  content: '';
  display: table;
  clear: both;
}

.assistant-message {
  max-width: 80%;
}


.message-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
}

.message-actions .action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.message-actions .action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.message-actions .action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message-actions .actions-divider {
  color: var(--border-color);
  font-size: 12px;
  margin: 0 4px;
}

.message-actions .agent-role-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.message-actions .message-time {
  font-size: 12px;
  color: #b0b0b0;
  margin-left: 8px;
}


.message-actions .action-btn {
  position: relative;
}

.message-actions .action-btn::before,
.message-actions .action-btn::after {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
  pointer-events: none;
}

.message-actions .action-btn::before {
  content: attr(data-tooltip);
  bottom: calc(100% + 6px);
  padding: 6px 10px;
  background: #1f2937;
  color: #fff;
  font-size: 12px;
  font-weight: 400;
  border-radius: 6px;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.message-actions .action-btn::after {
  content: '';
  bottom: calc(100% + 1px);
  width: 10px;
  height: 5px;
  background: #1f2937;
  clip-path: polygon(50% 100%, 0% 0%, 100% 0%);
}

.message-actions .action-btn:hover::before,
.message-actions .action-btn:hover::after {
  opacity: 1;
  visibility: visible;
}

.assistant-content {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
  letter-spacing: 0.02em;
}


.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.thinking-spinner {
  animation: spin 1s linear infinite;
  color: var(--text-tertiary);
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}


.assistant-content :deep(.thinking-block) {
  margin-bottom: 2px;
}

.assistant-content :deep(.thinking-header) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-tertiary);
  user-select: none;
}

.assistant-content :deep(.thinking-header:hover) {
  color: var(--text-secondary);
}

.assistant-content :deep(.thinking-header svg) {
  flex-shrink: 0;
}

.assistant-content :deep(.thinking-content) {
  margin-top: 2px;
  font-size: 12px;
  line-height: 1.2;
  color: var(--text-tertiary);
  white-space: pre-wrap;
  word-break: break-word;
}


.assistant-content :deep(.thinking-block.collapsed .thinking-content) {
  display: none;
}


.assistant-content :deep(.thinking-block.expanded .thinking-content) {
  display: block;
}


.assistant-content :deep(.thinking-citation) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 14px;
  height: 14px;
  padding: 0 3px;
  margin: 0 1px;
  background: var(--primary-light, #e3f2fd);
  color: var(--primary-color, #667eea);
  border-radius: 7px;
  font-size: 9px;
  font-weight: 600;
  vertical-align: baseline;
  position: relative;
  top: -1px;
  cursor: default;
}


.assistant-content :deep(.thinking-streaming-dot) {
  display: inline-block;
  width: 5px;
  height: 5px;
  background: var(--text-tertiary);
  border-radius: 50%;
  margin-left: 4px;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
  }
  50% {
    opacity: 1;
  }
}


.assistant-content :deep(.inline-citation) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 2px;
  margin: 0 2px;
  background: var(--primary-light);
  color: var(--primary-color);
  border-radius: 9px;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  vertical-align: middle;
  transition: background 0.15s, color 0.15s, transform 0.15s;
}

.assistant-content :deep(.inline-citation:hover) {
  background: var(--primary-color);
  color: white;
  transform: scale(1.15);
}


.assistant-content :deep(.inline-citation.active) {
  background: var(--primary-color);
  color: white;
  transform: scale(1.15);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
}


.assistant-content :deep(.inline-citation.disabled) {
  background: #e0e0e0;
  color: #9e9e9e;
  cursor: default;
  position: relative;
}

.assistant-content :deep(.inline-citation.disabled:hover) {
  background: #d0d0d0;
  transform: none;
}


.assistant-content :deep(.inline-citation.disabled::after) {
  content: '抱歉，暂时无法定位该引用来源';
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%) scale(0.9);
  padding: 8px 12px;
  background: rgba(30, 30, 30, 0.9);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  white-space: nowrap;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 1000;
  pointer-events: none;
}


.assistant-content :deep(.inline-citation.disabled::before) {
  content: '';
  position: absolute;
  bottom: calc(100% + 2px);
  left: 50%;
  transform: translateX(-50%) scale(0.9);
  border: 6px solid transparent;
  border-top-color: rgba(30, 30, 30, 0.9);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 1000;
  pointer-events: none;
}

.assistant-content :deep(.inline-citation.disabled:hover::after),
.assistant-content :deep(.inline-citation.disabled:hover::before) {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) scale(1);
}


.upload-progress-container {
  padding: 8px 12px;
  margin-top: 8px;
  background: var(--bg-main);
  border-radius: 8px;
}

.upload-progress-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  background: var(--bg-white);
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid var(--border-color);
}

.upload-progress-item:last-child {
  margin-bottom: 0;
}

.upload-progress-item.success {
  background: rgba(82, 196, 26, 0.08);
  border-color: rgba(82, 196, 26, 0.3);
}

.upload-progress-item.error {
  background: rgba(255, 77, 79, 0.08);
  border-color: rgba(255, 77, 79, 0.3);
}

.upload-file-name {
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-progress-bar {
  height: 6px;
  background: var(--border-color);
  border-radius: 3px;
  overflow: hidden;
}

.upload-progress-fill {
  height: 100%;
  background: var(--primary-color);
  border-radius: 3px;
  transition: width 0.2s ease;
}

.upload-progress-item.success .upload-progress-fill {
  background: #52c41a;
}

.upload-progress-item.error .upload-progress-fill {
  background: #ff4d4f;
}

.upload-status {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: right;
}

.upload-progress-item.success .upload-status {
  color: #52c41a;
}

.upload-progress-item.error .upload-status {
  color: #ff4d4f;
}


.chat-input-wrapper {
  padding: 10px 14px;
  position: relative;
}

.chat-input-wrapper.disabled-by-selection {
  opacity: 0.5;
  pointer-events: none;
}


.selection-action-bar {
  position: absolute;
  bottom: 80px;
  left: 20px;
  right: 20px;
  padding: 12px 20px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.selection-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.select-all-btn {
  padding: 4px 8px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
}

.select-all-btn:hover {
  background: var(--bg-hover);
}

.selected-count {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.selection-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-cancel-btn {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
}

.selection-export-btn {
  padding: 6px 16px;
  background: var(--primary-color);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.selection-export-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.selection-export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}


.slide-up-enter-active, .slide-up-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

.chat-input-box {
  display: flex;
  flex-direction: column;
  padding: 10px 14px;
  background: var(--bg-main);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  box-shadow: var(--shadow-sm);
}

.chat-input-box:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px var(--primary-light);
}

.input-main-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-main-row textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  background: transparent;
  max-height: 150px;
  overflow-y: auto;
}

.input-main-row textarea:focus {
  box-shadow: none;
}

.input-options-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 8px;
  margin-top: 8px;
  border-top: 1px solid var(--border-light);
}

.source-count {
  font-size: 12px;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.send-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: scale(1.05);
}

.send-btn:disabled {
  background: var(--text-disabled);
  border-radius: 50%;
}


.web-search-toggle {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  font-size: 12px;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.2s;
  user-select: none;
}

.web-search-toggle:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.web-search-toggle.active {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.web-search-toggle input[type="checkbox"] {
  display: none;
}

.web-search-toggle svg {
  flex-shrink: 0;
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
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 10px;
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

.workflow-item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.workflow-item-name {
  font-size: 13px;
  color: var(--text-primary);
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

.workflow-status-badge.status-processing::after {
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

.workflow-delete-btn {
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
  opacity: 0;
  transition: opacity 0.15s, background 0.15s, color 0.15s;
}

.workflow-item:hover .workflow-delete-btn {
  opacity: 1;
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


.assistant-content :deep(.tool-status-item) {
  padding: 0;
  margin: 0;
  color: var(--text-tertiary);
  font-size: 13px;
  line-height: 1.2;
}

.assistant-content :deep(.tool-status-item + .tool-status-item) {
  margin-top: 2px;
}


.assistant-content :deep(.assistant-segment) {
  margin: 0;
}

.assistant-content :deep(.assistant-segment.segment-thinking + .assistant-segment.segment-tool),
.assistant-content :deep(.assistant-segment.segment-tool + .assistant-segment.segment-thinking),
.assistant-content :deep(.assistant-segment.segment-tool + .assistant-segment.segment-tool) {
  margin-top: 2px;
}


.markdown-body {
  font-size: 15px;
  line-height: 1.8;
  letter-spacing: 0.02em;
  color: var(--text-primary);
}


.markdown-body :deep(p) {
  margin: 0.8em 0;
}

.markdown-body :deep(p:first-child) {
  margin-top: 0;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}


.assistant-content :deep(.assistant-segment.segment-thinking + .assistant-segment.segment-body),
.assistant-content :deep(.assistant-segment.segment-tool + .assistant-segment.segment-body),
.assistant-content :deep(.assistant-segment.segment-body + .assistant-segment.segment-thinking),
.assistant-content :deep(.assistant-segment.segment-body + .assistant-segment.segment-tool) {
  margin-top: 6px;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 1.2em 0 0.6em;
  font-weight: 600;
  color: var(--text-primary);
}

.markdown-body :deep(h1) { font-size: 1.5em; }
.markdown-body :deep(h2) { font-size: 1.3em; }
.markdown-body :deep(h3) { font-size: 1.15em; }
.markdown-body :deep(h4) { font-size: 1.05em; }

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.8em 0;
  padding-left: 1.8em;
}

.markdown-body :deep(li) {
  margin: 0.4em 0;
}

.markdown-body :deep(code) {
  padding: 2px 6px;
  background: var(--bg-hover);
  border-radius: 4px;
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 0.9em;
  color: #c53030;
}

.markdown-body :deep(pre) {
  background: #1a202c;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1em 0;
}

.markdown-body :deep(pre code) {
  padding: 0;
  background: transparent;
  color: #e2e8f0;
}

.markdown-body :deep(blockquote) {
  margin: 1em 0;
  padding: 12px 16px;
  border-left: 4px solid var(--primary-color);
  background: var(--bg-sidebar);
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
}

.markdown-body :deep(hr) {
  border: none;
  height: 1px;
  background: var(--border-color);
  margin: 1.5em 0;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  text-align: left;
}

.markdown-body :deep(th) {
  background: var(--bg-sidebar);
  font-weight: 600;
}

.markdown-body :deep(a) {
  color: var(--primary-color);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}


.scroll-to-bottom-btn {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  color: var(--text-secondary);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  transition: all 0.2s;
  z-index: 10;
}

.scroll-to-bottom-btn:hover {
  background: var(--bg-hover);
  color: var(--primary-color);
  transform: translateX(-50%) scale(1.1);
}


.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}


.assistant-content :deep(.inline-citation.image-citation) {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border: 1px solid #81c784;
}

.assistant-content :deep(.inline-citation.image-citation:hover) {
  background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
  border-color: #66bb6a;
}


.assistant-content :deep(.inline-citation.web-citation) {
  width: auto;
  min-width: 18px;
  padding: 0 5px;
  gap: 2px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border: 1px solid #64b5f6;
  position: relative;
}

.assistant-content :deep(.inline-citation.web-citation .web-icon) {
  flex-shrink: 0;
  margin-left: 1px;
}

.assistant-content :deep(.inline-citation.web-citation .web-favicon) {
  flex-shrink: 0;
  margin-left: 2px;
  border-radius: 2px;
  vertical-align: middle;
}

.assistant-content :deep(.inline-citation.web-citation:hover) {
  background: linear-gradient(135deg, #bbdefb 0%, #90caf9 100%);
  border-color: #42a5f5;
}


.copy-toast {
  position: absolute;
  top: 10%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: rgba(240, 249, 240, 0.98);
  backdrop-filter: blur(8px);
  color: #2e7d32;
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 100;
  pointer-events: none;
}

.copy-toast svg {
  flex-shrink: 0;
}


.copy-toast-enter-active,
.copy-toast-leave-active {
  transition: all 0.3s ease;
}

.copy-toast-enter-from,
.copy-toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.9);
}


.assistant-content.has-error {
  border-left: 3px solid #f59e0b;
  padding-left: 12px;
}


.assistant-content :deep(.error-placeholder) {
  color: #dc2626;
  font-size: 14px;
  line-height: 1.6;
}


.assistant-content :deep(.system-hint) {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  line-height: 1.5;
}


.assistant-content :deep(.system-hint.warning) {
  background-color: #fef3c7;
  border: 1px solid #fbbf24;
  color: #92400e;
}


.assistant-content :deep(.system-hint.error) {
  background-color: #fee2e2;
  border: 1px solid #f87171;
  color: #991b1b;
}


.assistant-content :deep(.system-hint .hint-icon) {
  flex-shrink: 0;
  font-size: 16px;
  line-height: 1;
}


.assistant-content :deep(.system-hint .hint-text) {
  flex: 1;
}


.action-btn.error-retry {
  color: #f59e0b;
}

.action-btn.error-retry:hover:not(:disabled) {
  background-color: #fef3c7;
  color: #d97706;
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
