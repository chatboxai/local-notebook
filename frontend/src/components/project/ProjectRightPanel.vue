<template>
  <div v-if="rightPanelCollapsed" class="collapsed-sidebar right">
    <div class="collapsed-icon-btn" @click="emit('update:rightPanelCollapsed', false)" :title="$t('ui.expandToolboxPanel')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/>
        <path d="M13 7h4v10h-4z" opacity="0.5"/>
      </svg>
    </div>
    <div class="collapsed-icon-btn disabled" :title="developmentTitle('audioOverview')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
      </svg>
    </div>
    <div class="collapsed-icon-btn disabled" :title="developmentTitle('videoOverview')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z" />
      </svg>
    </div>
    <div class="collapsed-icon-btn disabled" :title="developmentTitle('mindMap')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M22 11V3h-7v3H9V3H2v8h7V8h2v10h4v3h7v-8h-7v3h-2V8h2v3h7zM7 9H4V5h3v4zm10 6h3v4h-3v-4zm0-10h3v4h-3V5z" />
      </svg>
    </div>
    <div class="collapsed-icon-btn disabled" :title="developmentTitle('report')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
      </svg>
    </div>
    <div class="collapsed-icon-btn disabled" :title="developmentTitle('flashcards')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
      </svg>
    </div>
    <div class="collapsed-icon-btn disabled" :title="developmentTitle('quiz')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H7v-2h5v2zm5-4H7v-2h10v2zm0-4H7V7h10v2z" />
      </svg>
    </div>
    <div class="collapsed-icon-btn disabled" :title="developmentTitle('timeline')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z" />
      </svg>
    </div>
    <div class="collapsed-icon-btn disabled" :title="developmentTitle('summary')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-4 6h-4v2h4v2h-4v2h4v2H9V7h6v2z" />
      </svg>
    </div>
    <div class="collapsed-icon-btn disabled" :title="developmentTitle('keyPoints')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
      </svg>
    </div>
    <div class="collapsed-icon-btn disabled" :title="developmentTitle('notes')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
      </svg>
    </div>
  </div>

  <aside
    class="studio-panel"
    :class="{ collapsed: rightPanelCollapsed, 'detail-mode': showFeatureDetail || showWorkflowDetail }"
    :style="{
      width: rightPanelCollapsed ? '0px' : `${rightPanelWidth}px`,
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
      @close="emit('close-workflow-detail')"
      @cancel="workflowId => emit('cancel-workflow', workflowId)"
      @update-title="(id, title) => emit('workflow-title-update', id, title)"
      @citation-click="(part, feature) => emit('workflow-citation-click', part, feature)"
      @clear-citation="emit('clear-workflow-citation')"
      @regenerate-step="stepIndex => emit('workflow-step-regenerate', stepIndex)"
      @show-toast="(message, type) => emit('show-toast', message, type)"
    />

    <FeatureDetailPanel
      v-else-if="showFeatureDetail && activeFeature"
      :feature="activeFeature"
      :active-citation-num="activeFeatureCitationNum"
      @close="emit('close-feature-detail')"
      @citation-click="part => emit('feature-citation-click', part)"
      @clear-citation="emit('clear-feature-citation')"
      @rename="title => emit('feature-rename', title)"
    />

    <template v-else>
      <div class="panel-header">
        <div class="panel-title-wrapper">
          <span
            class="panel-title clickable"
            :class="{ active: toolboxMode === 'tools' }"
            @click="emit('update:toolboxMode', 'tools')"
          >{{ $t('ui.quickTools') }}</span>
          <span class="panel-title-divider">/</span>
          <span
            class="panel-title clickable"
            :class="{ active: toolboxMode === 'oneclick' }"
            @click="emit('update:toolboxMode', 'oneclick')"
          >{{ $t('ui.smartAnalysis') }}</span>
        </div>
        <button class="panel-toggle-btn" @click="emit('update:rightPanelCollapsed', true)" :title="$t('ui.collapsePanel')">
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
                <div
                  v-for="tool in enabledQuickTools"
                  :key="tool.type"
                  class="tool-card"
                  :class="[`tool-card--${tool.color}`, { disabled: !hasReadyFiles }]"
                  :title="hasReadyFiles ? t(tool.tooltipKey) : t('ui.uploadAndProcessFilesFirst')"
                  @click="hasReadyFiles && emit('open-tool-config', tool)"
                >
                  <div class="tool-card-icon">
                    <svg v-if="tool.icon === 'audience'" viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
                    <svg v-else-if="tool.icon === 'market'" viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
                    <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2 4 5v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V5l-8-3zm0 2.18 6 2.25V11c0 4.28-2.72 8.24-6 9.75C8.72 19.24 6 15.28 6 11V6.43l6-2.25zM9 11h6v2H9v-2zm0-3h6v2H9V8z"/></svg>
                  </div>
                  <span class="tool-card-title">{{ t(tool.titleKey) }}</span>
                </div>
              </div>
            </div>

            <div class="studio-results-scroll">
              <div class="oneclick-queue">
                <div class="queue-header">
                  <span class="queue-title">{{ t('ui.generatedResult') }}</span>
                </div>

                <div v-if="features.length === 0" class="queue-empty">
                  <p>{{ hasReadyFiles ? t('ui.useTheButtonsAboveToGenerateQuickTool') : t('ui.uploadSourcesToGenerateQuickTool') }}</p>
                </div>

                <div v-else class="workflow-list">
                  <div
                    v-for="feature in features"
                    :key="feature.id"
                    class="workflow-item feature-item"
                    :class="{ highlighted: highlightedFeatureId === feature.id }"
                    @click="emit('view-feature-detail', feature)"
                  >
                    <div class="workflow-item-icon icon-default" :class="getFeatureSourceClass(feature)">
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                        <path d="M4 4h16v2H4V4zm0 4h16v2H4V8zm0 4h10v2H4v-2zm0 4h13v2H4v-2z"/>
                      </svg>
                    </div>
                    <div class="workflow-item-info">
                      <div class="workflow-item-title-row">
                        <div class="workflow-item-name">{{ getFeatureDisplayName(feature) }}</div>
                        <span class="workflow-source-chip" :class="getFeatureSourceClass(feature)">
                          {{ getFeatureSourceLabel(feature) }}
                        </span>
                      </div>
                      <div class="workflow-item-status">
                        <span class="workflow-status-badge" :class="getFeatureStatusClass(feature.status)">
                          {{ getFeatureStatusText(feature.status) }}
                        </span>
                        <span v-if="feature.created_at" class="workflow-item-time">{{ formatTime(feature.created_at) }}</span>
                      </div>
                    </div>
                    <button class="workflow-delete-btn" @click.stop="emit('delete-feature', feature)" :title="t('ui.delete')">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="studio-content" key="oneclick">
            <div class="studio-tools-fixed">
              <div class="tool-grid oneclick">
                <div class="tool-card tool-card--blue" :class="{ disabled: !hasReadyFiles }" :title="hasReadyFiles ? t('ui.quicklyGraspTheMainThreadAndKeyPoints') : t('ui.uploadAndProcessFilesFirst')" @click="openWorkflowConfig('quick_read')">
                  <div class="tool-card-icon">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M4 4h16v2H4V4zm0 4h10v2H4V8zm0 4h16v2H4v-2zm0 4h10v2H4v-2z"/></svg>
                  </div>
                  <span class="tool-card-title">{{ t('ui.quickRead') }}</span>
                </div>
                <div class="tool-card tool-card--indigo" :class="{ disabled: !hasReadyFiles }" :title="hasReadyFiles ? t('ui.systematicallyUnpackTheKeyLogicInTheMaterial') : t('ui.uploadAndProcessFilesFirst')" @click="openWorkflowConfig('deep_dive')">
                  <div class="tool-card-icon">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M9 3h6l1 2h4a1 1 0 0 1 1 1v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a1 1 0 0 1 1-1h4l1-2zm1.24 2-.5 1H5v13h14V7h-4.74l-.5-1h-3.52zM7 10h10v2H7v-2zm0 4h7v2H7v-2z"/></svg>
                  </div>
                  <span class="tool-card-title">{{ t('ui.coreDeepDive') }}</span>
                </div>
                <div class="tool-card tool-card--custom" :class="{ disabled: !hasReadyFiles }" :title="hasReadyFiles ? t('ui.planAndGenerateFullyFromYourInstructions') : t('ui.uploadAndProcessFilesFirst')" @click="openWorkflowConfig('custom')">
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
                  <span class="tool-card-title">{{ t('ui.customWorkflow') }}</span>
                </div>
              </div>
            </div>

            <div class="studio-results-scroll">
              <div class="oneclick-queue">
                <div class="queue-header">
                  <span class="queue-title">{{ t('ui.generatedResult') }}</span>
                </div>

                <div v-if="workflows.length === 0" class="queue-empty">
                  <p>{{ hasReadyFiles ? t('ui.useTheButtonsAboveToGenerateAReport') : t('ui.uploadSourcesToGenerateAReport') }}</p>
                </div>

                <div v-else class="workflow-list">
                  <div
                    v-for="workflow in workflows"
                    :key="workflow.id"
                    class="workflow-item"
                    :class="{ highlighted: highlightedWorkflowId === workflow.id }"
                    @click="emit('view-workflow-detail', workflow.id)"
                  >
                    <div class="workflow-item-icon icon-default" :class="getWorkflowSourceClass(workflow)">
                      <svg v-if="getWorkflowPresetKey(workflow) === 'quick_read'" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                        <path d="M4 4h16v2H4V4zm0 4h10v2H4V8zm0 4h16v2H4v-2zm0 4h10v2H4v-2z"/>
                      </svg>
                      <svg v-else-if="getWorkflowPresetKey(workflow) === 'deep_dive'" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
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
                        <div class="workflow-item-name">{{ getWorkflowDisplayName(workflow) }}</div>
                        <span class="workflow-source-chip" :class="getWorkflowSourceClass(workflow)">
                          {{ getWorkflowSourceLabel(workflow) }}
                        </span>
                      </div>
                      <div class="workflow-item-status">
                        <span class="workflow-status-badge" :class="getWorkflowStatusClass(workflow.status)">
                          {{ getWorkflowDisplayStatusText(workflow) }}
                        </span>
                        <span v-if="isWorkflowActiveStatus(workflow.status)" class="workflow-item-time">
                          {{ formatWorkflowProgress(workflow) }}
                        </span>
                        <span v-if="isWorkflowActiveStatus(workflow.status) && workflow.created_at" class="workflow-item-time">
                          {{ formatWorkflowElapsed(workflow.created_at) }}
                        </span>
                        <span v-else-if="workflow.created_at" class="workflow-item-time">{{ formatTime(workflow.created_at) }}</span>
                      </div>
                    </div>
                    <button
                      v-if="isWorkflowCancellable(workflow.status)"
                      class="workflow-stop-btn"
                      @click.stop="emit('cancel-workflow', workflow.id)"
                      :title="t('ui.stopGeneration')"
                    >
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                        <path d="M6 6h12v12H6z"/>
                      </svg>
                    </button>
                    <button v-else class="workflow-delete-btn" @click.stop="emit('delete-workflow', workflow.id)" :title="t('ui.delete')">
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
</template>

<script setup lang="ts">
import type { FeatureListItem, WorkflowDetail, WorkflowListItem, WorkflowContentFeature } from '../../services/api'
import type { Feature, FeatureCitationRefPart } from '../../types'
import { t } from '../../i18n'
import FeatureDetailPanel from './FeatureDetailPanel.vue'
import WorkflowDetailPanel from './WorkflowDetailPanel.vue'
import { TOOL_TYPES } from '../../views/projectPage/toolTypes'
import {
  formatWorkflowProgress,
  getWorkflowDisplayName,
  getWorkflowDisplayStatusText,
  getWorkflowPresetKey,
  getWorkflowSourceClass,
  getWorkflowSourceLabel,
  getWorkflowStatusClass,
  isWorkflowActiveStatus,
  isWorkflowCancellable,
  type WorkflowPresetKey,
} from '../../views/projectPage/workflowHelpers'

type ToolboxMode = 'tools' | 'oneclick'
type ToastType = 'success' | 'error' | 'info' | 'warning'
type DevelopmentToolKey = 'audioOverview' | 'videoOverview' | 'mindMap' | 'report' | 'flashcards' | 'quiz' | 'timeline' | 'summary' | 'keyPoints' | 'notes'
type QuickTool = typeof TOOL_TYPES[number]

const enabledQuickTools = TOOL_TYPES.filter(tool => tool.enabled && !tool.type.includes('image') && !tool.type.includes('video'))

defineProps<{
  rightPanelCollapsed: boolean
  rightPanelWidth: number
  showFeatureDetail: boolean
  showWorkflowDetail: boolean
  currentWorkflow: WorkflowDetail | null
  workflowFeatures: WorkflowContentFeature[]
  activeWorkflowCitationNum: number | null
  activeWorkflowFeatureId: string | null
  activeFeature: Feature | null
  activeFeatureCitationNum: number | null
  toolboxMode: ToolboxMode
  transitionName: string
  hasReadyFiles: boolean
  features: FeatureListItem[]
  workflows: WorkflowListItem[]
  highlightedFeatureId: string | null
  highlightedWorkflowId: string | null
  formatTime: (isoString: string) => string
  formatWorkflowElapsed: (isoString: string) => string
}>()

const emit = defineEmits<{
  (e: 'update:rightPanelCollapsed', value: boolean): void
  (e: 'update:toolboxMode', value: ToolboxMode): void
  (e: 'close-workflow-detail'): void
  (e: 'cancel-workflow', workflowId: string): void
  (e: 'delete-workflow', workflowId: string): void
  (e: 'workflow-title-update', id: string, title: string): void
  (e: 'workflow-citation-click', part: FeatureCitationRefPart, feature: WorkflowContentFeature): void
  (e: 'clear-workflow-citation'): void
  (e: 'workflow-step-regenerate', stepIndex: number): void
  (e: 'show-toast', message: string, type: ToastType): void
  (e: 'close-feature-detail'): void
  (e: 'feature-citation-click', part: FeatureCitationRefPart): void
  (e: 'clear-feature-citation'): void
  (e: 'feature-rename', newTitle: string): void
  (e: 'open-tool-config', tool: QuickTool): void
  (e: 'view-feature-detail', feature: FeatureListItem): void
  (e: 'delete-feature', feature: FeatureListItem): void
  (e: 'open-workflow-config', presetKey: WorkflowPresetKey): void
  (e: 'view-workflow-detail', workflowId: string): void
}>()

function openWorkflowConfig(presetKey: WorkflowPresetKey) {
  emit('open-workflow-config', presetKey)
}

function developmentTitle(key: DevelopmentToolKey): string {
  return t('ui.developmentTitle', {
    name: t(`ui.${key}`),
    status: t('ui.underDevelopment'),
  })
}

function getFeatureTool(feature: FeatureListItem): QuickTool | undefined {
  return TOOL_TYPES.find(tool => tool.type === feature.feature_type)
}

function getFeatureDisplayName(feature: FeatureListItem): string {
  return feature.title || feature.display_name || getFeatureSourceLabel(feature)
}

function getFeatureSourceLabel(feature: FeatureListItem): string {
  const tool = getFeatureTool(feature)
  return tool ? t(tool.titleKey) : t('ui.quickTools')
}

function getFeatureSourceClass(feature: FeatureListItem): string {
  const color = getFeatureTool(feature)?.color || 'cyan'
  return `feature-source-${color}`
}

function getFeatureStatusText(status: FeatureListItem['status']): string {
  if (status === 'pending') return t('ui.queued')
  if (status === 'processing') return t('ui.generating2')
  if (status === 'completed') return t('ui.completed')
  if (status === 'failed') return t('ui.failed')
  return status
}

function getFeatureStatusClass(status: FeatureListItem['status']): string {
  if (status === 'pending' || status === 'processing') return 'status-processing'
  if (status === 'completed') return 'status-completed'
  if (status === 'failed') return 'status-failed'
  return ''
}
</script>

<style scoped>
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

.studio-panel.collapsed {
  padding: 0;
  border: none;
  overflow: hidden;
  min-width: 0;
}

.studio-panel.collapsed > * {
  display: none;
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

.panel-toggle-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-tertiary);
  transition: background 0.15s, color 0.15s;
  cursor: pointer;
}

.panel-toggle-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
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

.tool-card--blue {
  background: linear-gradient(135deg, rgba(147, 197, 253, 0.5) 0%, rgba(96, 165, 250, 0.5) 100%);
}

.tool-card--blue .tool-card-icon,
.tool-card--blue .tool-card-title {
  color: #1d4ed8;
}

.tool-card--cyan {
  background: linear-gradient(135deg, rgba(165, 243, 252, 0.5) 0%, rgba(103, 232, 249, 0.5) 100%);
}

.tool-card--cyan .tool-card-icon,
.tool-card--cyan .tool-card-title {
  color: #0e7490;
}

.tool-card--amber {
  background: linear-gradient(135deg, rgba(253, 230, 138, 0.5) 0%, rgba(251, 191, 36, 0.5) 100%);
}

.tool-card--amber .tool-card-icon,
.tool-card--amber .tool-card-title {
  color: #b45309;
}

.tool-card--indigo {
  background: linear-gradient(135deg, rgba(199, 210, 254, 0.5) 0%, rgba(165, 180, 252, 0.5) 100%);
}

.tool-card--indigo .tool-card-icon,
.tool-card--indigo .tool-card-title {
  color: #4338ca;
}

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

.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.workflow-item:hover {
  background: var(--bg-hover);
}

.workflow-item.highlighted {
  background: rgba(20, 184, 166, 0.12);
  box-shadow: inset 0 0 0 1px rgba(13, 148, 136, 0.28);
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

.workflow-item-icon.feature-source-cyan {
  background: linear-gradient(135deg, rgba(165, 243, 252, 0.5) 0%, rgba(103, 232, 249, 0.5) 100%);
  color: #0e7490;
}

.workflow-item-icon.feature-source-amber {
  background: linear-gradient(135deg, rgba(253, 230, 138, 0.5) 0%, rgba(251, 191, 36, 0.5) 100%);
  color: #b45309;
}

.workflow-item-icon.feature-source-indigo {
  background: linear-gradient(135deg, rgba(199, 210, 254, 0.5) 0%, rgba(165, 180, 252, 0.5) 100%);
  color: #4338ca;
}

.workflow-item-icon.feature-source-custom {
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

.workflow-source-chip.feature-source-cyan {
  background: linear-gradient(135deg, rgba(165, 243, 252, 0.44) 0%, rgba(103, 232, 249, 0.28) 100%);
  color: #0e7490;
}

.workflow-source-chip.feature-source-amber {
  background: linear-gradient(135deg, rgba(253, 230, 138, 0.5) 0%, rgba(251, 191, 36, 0.28) 100%);
  color: #b45309;
}

.workflow-source-chip.feature-source-indigo {
  background: linear-gradient(135deg, rgba(199, 210, 254, 0.55) 0%, rgba(165, 180, 252, 0.38) 100%);
  color: #4338ca;
}

.workflow-source-chip.feature-source-custom {
  background:
    linear-gradient(135deg, rgba(20, 184, 166, 0.2) 0%, rgba(250, 204, 21, 0.28) 100%),
    radial-gradient(circle at 86% 12%, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0) 36%);
  border: 1px solid rgba(13, 148, 136, 0.22);
  color: #0f766e;
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

.workflow-status-badge.status-processing::after,
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
</style>
