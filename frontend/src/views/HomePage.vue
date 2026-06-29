<template>
  <div class="home-page">
    
    <header class="home-header">
      <div class="header-left">
        <div class="logo">
          <img src="/logo/logo.png" alt="Local Notebook" class="logo-img" />
          <span class="logo-text">Local Notebook</span>
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

    
    <main class="home-main">
      <section class="projects-section">
        <div v-if="loading" class="loading">{{ $t('ui.loading') }}</div>

        <div v-else-if="projects.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
            </svg>
          </div>
          <p>{{ $t('ui.noProjectsYet') }}</p>
          <button class="btn-primary" @click="showCreateModal = true">
            {{ $t('ui.createYourFirstProject') }}
          </button>
        </div>

        <div v-else class="projects-container">
          
          <div v-for="(group, index) in groupedProjects" :key="group.label" class="project-group">
            <h3 class="group-title">{{ group.label }}</h3>
            <div class="projects-grid">
              
              <div v-if="index === 0" class="project-card new-card" @click="showCreateModal = true">
                <div class="new-card-content">
                  <div class="new-icon">
                    <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                      <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
                    </svg>
                  </div>
                  <span>{{ $t('ui.newProject') }}</span>
                </div>
              </div>
              <div
                v-for="project in group.projects"
                :key="project.id"
                class="project-card"
                :class="project.color ? `theme-${project.color}` : ''"
                @click="goToProject(project.id)"
              >
                <div class="card-icon" :style="{ color: getProjectColor(project.color) }">
                  <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
                  </svg>
                </div>
                <div class="card-content">
                  <h3 class="card-title">{{ project.name }}</h3>
                  <div class="card-summary-wrapper" :class="{ placeholder: !project.summary }">
                    <p class="card-summary">{{ truncateSummary(project.summary) }}</p>
                    <div v-if="project.summary" class="summary-tooltip">
                      <div class="tooltip-content">{{ project.summary }}</div>
                    </div>
                  </div>
                  <p class="card-meta">
                    {{ formatDate(project.created_at) }} · {{ formatFileCount(project.file_count) }}
                  </p>
                </div>
                <div class="card-menu-wrapper">
                  <button
                    class="card-menu-btn"
                    @click.stop="toggleProjectMenu(project.id)"
                    :title="$t('ui.moreActions')"
                  >
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                      <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
                    </svg>
                  </button>
                  <div v-if="activeProjectMenu === project.id" class="card-dropdown-menu">
                    <button class="card-dropdown-item" @click.stop="openRenameModal(project)">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                        <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                      </svg>
                      {{ $t('ui.rename') }}
                    </button>
                    <button class="card-dropdown-item danger" @click.stop="handleDeleteProject(project.id)">
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                        <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
                      </svg>
                      {{ $t('ui.delete') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          
          <div v-if="groupedProjects.length === 0 && projects.length > 0" class="project-group">
            <h3 class="group-title">{{ $t('ui.today') }}</h3>
            <div class="projects-grid">
              <div class="project-card new-card" @click="showCreateModal = true">
                <div class="new-card-content">
                  <div class="new-icon">
                    <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                      <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
                    </svg>
                  </div>
                  <span>{{ $t('ui.newProject') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal" @click.stop>
        <h3 class="modal-title">{{ $t('ui.newProject') }}</h3>
        <input
          type="text"
          class="modal-input"
          :placeholder="$t('ui.enterProjectName')"
          v-model="newProjectName"
          @keydown.enter="handleCreateEnter"
          @compositionstart="isComposing = true"
          @compositionend="isComposing = false"
          ref="inputRef"
        />
        <div class="modal-actions">
          <button class="btn-cancel" @click="showCreateModal = false">{{ $t('ui.cancel') }}</button>
          <button
            class="btn-primary"
            @click="handleCreateProject"
            :disabled="!newProjectName.trim() || creating"
          >
            {{ creating ? $t('ui.creating') : $t('ui.create') }}
          </button>
        </div>
      </div>
    </div>

    
    <div v-if="showPreflightWarning" class="modal-overlay" @click="showPreflightWarning = false">
      <div class="modal" @click.stop>
        <h3 class="modal-title">{{ $t('ui.basicConfigurationIsIncomplete') }}</h3>
        <p class="preflight-desc">
          {{ canAdmin ? $t('ui.completeTheFollowingConfigurationBeforeCreatingAProject') : $t('ui.systemConfigurationIncompleteContactAdmin') }}
        </p>
        <ul class="preflight-list">
          <li v-for="item in preflightMissing" :key="item">{{ item }}</li>
        </ul>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showPreflightWarning = false">{{ $t('ui.later') }}</button>
          <button v-if="canAdmin" class="btn-primary" @click="goToSettings">{{ $t('ui.goToSettings') }}</button>
        </div>
      </div>
    </div>

    
    <div v-if="showRenameModal" class="modal-overlay" @click="closeRenameModal">
      <div class="modal" @click.stop>
        <h3 class="modal-title">{{ $t('ui.renameProject') }}</h3>
        <input
          type="text"
          class="modal-input"
          :placeholder="$t('ui.enterANewProjectName')"
          v-model="renameProjectName"
          @keydown.enter="handleRenameEnter"
          @compositionstart="isComposing = true"
          @compositionend="isComposing = false"
          ref="renameInputRef"
        />
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeRenameModal">{{ $t('ui.cancel') }}</button>
          <button
            class="btn-primary"
            @click="handleRenameProject"
            :disabled="!renameProjectName.trim() || renaming"
          >
            {{ renaming ? $t('ui.saving') : $t('ui.save') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getProjects, createProject, deleteProject, updateProject, checkPreflight } from '../services/api'
import type { Project, ProjectColor } from '../types'
import LanguageSwitcher from '../components/common/LanguageSwitcher.vue'
import { formatDate } from '../utils/format'
import { usePollingTask } from '../composables/usePollingTask'
import { clearTokens, getDisplayUsername, isAdmin } from '../services/auth'
import { t } from '../i18n'

const router = useRouter()
const displayUsername = computed(() => getDisplayUsername() || t('ui.defaultUser'))
const canAdmin = computed(() => isAdmin())

const projects = ref<Project[]>([])
const loading = ref(true)
const showCreateModal = ref(false)
const newProjectName = ref('')
const creating = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

const ACTIVE_PROJECT_REFRESH_MS = 10000
const IDLE_PROJECT_REFRESH_MS = 30000


const activeProjectMenu = ref<string | null>(null)


const showRenameModal = ref(false)
const renameProjectId = ref<string | null>(null)
const renameProjectName = ref('')
const renaming = ref(false)
const renameInputRef = ref<HTMLInputElement | null>(null)


const isComposing = ref(false)


interface ProjectGroup {
  label: string
  projects: Project[]
}


const groupedProjects = computed((): ProjectGroup[] => {
  if (projects.value.length === 0) return []

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  const dayBeforeYesterday = new Date(today.getTime() - 2 * 24 * 60 * 60 * 1000)
  const threeDaysAgo = new Date(today.getTime() - 3 * 24 * 60 * 60 * 1000)
  const sevenDaysAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
  const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)

  const todayList: Project[] = []
  const yesterdayList: Project[] = []
  const dayBeforeYesterdayList: Project[] = []
  const threeDaysList: Project[] = []
  const sevenDaysList: Project[] = []
  const thirtyDaysList: Project[] = []
  const olderList: Project[] = []

  
  const sorted = [...projects.value].sort((a, b) => {
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  })

  for (const project of sorted) {
    const updatedAt = new Date(project.updated_at)

    if (updatedAt >= today) {
      todayList.push(project)
    } else if (updatedAt >= yesterday) {
      yesterdayList.push(project)
    } else if (updatedAt >= dayBeforeYesterday) {
      dayBeforeYesterdayList.push(project)
    } else if (updatedAt >= threeDaysAgo) {
      threeDaysList.push(project)
    } else if (updatedAt >= sevenDaysAgo) {
      sevenDaysList.push(project)
    } else if (updatedAt >= thirtyDaysAgo) {
      thirtyDaysList.push(project)
    } else {
      olderList.push(project)
    }
  }

  
  const result: ProjectGroup[] = []
  result.push({ label: t('ui.today'), projects: todayList })
  if (yesterdayList.length > 0) result.push({ label: t('ui.yesterday'), projects: yesterdayList })
  if (dayBeforeYesterdayList.length > 0) result.push({ label: t('ui.twoDaysAgo'), projects: dayBeforeYesterdayList })
  if (threeDaysList.length > 0) result.push({ label: t('ui.last3Days'), projects: threeDaysList })
  if (sevenDaysList.length > 0) result.push({ label: t('ui.last7Days'), projects: sevenDaysList })
  if (thirtyDaysList.length > 0) result.push({ label: t('ui.lastMonth'), projects: thirtyDaysList })
  if (olderList.length > 0) result.push({ label: t('ui.older'), projects: olderList })

  return result
})


function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.card-menu-wrapper')) {
    activeProjectMenu.value = null
  }
}

function needsActiveProjectRefresh(project: Project): boolean {
  return project.file_count > 0 && (!project.summary || !project.color)
}

function getProjectRefreshDelay(): number {
  return projects.value.some(needsActiveProjectRefresh)
    ? ACTIVE_PROJECT_REFRESH_MS
    : IDLE_PROJECT_REFRESH_MS
}

const projectRefresh = usePollingTask({
  run: () => loadProjects({ silent: true }),
  getDelay: getProjectRefreshDelay,
  retryDelay: ACTIVE_PROJECT_REFRESH_MS,
  canRun: () => !loading.value,
  pauseWhenHidden: true,
  refreshOnVisible: true,
  onError: (error) => console.error('Failed to refresh projects:', error),
})

onMounted(() => {
  void loadProjects().finally(() => projectRefresh.start())
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  projectRefresh.stop()
  document.removeEventListener('click', handleClickOutside)
})

watch(showCreateModal, (val) => {
  if (val) {
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
})

watch(showRenameModal, (val) => {
  if (val) {
    nextTick(() => {
      renameInputRef.value?.focus()
      renameInputRef.value?.select()
    })
  }
})

async function loadProjects(options: { silent?: boolean } = {}) {
  try {
    if (!options.silent) loading.value = true
    projects.value = await getProjects()
  } catch (error) {
    console.error('Failed to load projects:', error)
  } finally {
    if (!options.silent) loading.value = false
  }
}


function handleCreateEnter() {
  if (isComposing.value) return
  handleCreateProject()
}


const showPreflightWarning = ref(false)
const preflightMissing = ref<string[]>([])

async function handleCreateProject() {
  if (!newProjectName.value.trim()) return

  try {
    creating.value = true

    
    const preflight = await checkPreflight()
    if (!preflight.ready) {
      preflightMissing.value = preflight.missing
      showPreflightWarning.value = true
      return
    }

    const project = await createProject(newProjectName.value.trim())
    projects.value.unshift(project)
    newProjectName.value = ''
    showCreateModal.value = false
    router.push(`/project/${project.id}`)
  } catch (error) {
    console.error('Failed to create project:', error)
  } finally {
    creating.value = false
  }
}

function goToSettings() {
  showPreflightWarning.value = false
  showCreateModal.value = false
  router.push('/settings')
}

function logout() {
  clearTokens()
  router.push('/login')
}

async function handleDeleteProject(projectId: string) {
  activeProjectMenu.value = null
  if (!confirm(t('ui.confirmDeleteProject'))) return

  try {
    await deleteProject(projectId)
    projects.value = projects.value.filter((p) => p.id !== projectId)
  } catch (error) {
    console.error('Failed to delete project:', error)
  }
}


function toggleProjectMenu(projectId: string) {
  if (activeProjectMenu.value === projectId) {
    activeProjectMenu.value = null
  } else {
    activeProjectMenu.value = projectId
  }
}


function openRenameModal(project: Project) {
  activeProjectMenu.value = null
  renameProjectId.value = project.id
  renameProjectName.value = project.name
  showRenameModal.value = true
}


function closeRenameModal() {
  showRenameModal.value = false
  renameProjectId.value = null
  renameProjectName.value = ''
}


function handleRenameEnter() {
  if (isComposing.value) return
  handleRenameProject()
}


async function handleRenameProject() {
  if (!renameProjectName.value.trim() || !renameProjectId.value) return

  try {
    renaming.value = true
    const updated = await updateProject(renameProjectId.value, {
      name: renameProjectName.value.trim()
    })
    
    const index = projects.value.findIndex(p => p.id === renameProjectId.value)
    if (index !== -1) {
      projects.value[index] = { ...projects.value[index], ...updated }
    }
    closeRenameModal()
  } catch (error) {
    console.error('Failed to rename project:', error)
  } finally {
    renaming.value = false
  }
}

function goToProject(projectId: string) {
  router.push(`/project/${projectId}`)
}

const colorMap: Record<ProjectColor, string> = {
  blue: '#3B82F6',
  green: '#22C55E',
  orange: '#F97316',
  red: '#EF4444',
  purple: '#A855F7',
  cyan: '#06B6D4',
  pink: '#EC4899',
  brown: '#A16207'
}


function getProjectColor(color: ProjectColor | null): string {
  return color ? colorMap[color] : '#4a90a4'
}


function formatFileCount(fileCount: number | null | undefined): string {
  if (!Number.isFinite(fileCount)) return t('ui.files')
  return t('ui.fileCount', { count: fileCount })
}


function truncateSummary(summary: string | null | undefined, maxLength: number = 30): string {
  if (!summary) return ''
  if (summary.length <= maxLength) return summary
  return summary.slice(0, maxLength) + '...'
}

</script>

<style scoped>
.home-page {
  height: 100vh;
  background: var(--bg-main);
  overflow-y: auto;
}


.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--bg-main);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-img {
  height: 48px;
  width: auto;
}

.logo-text {
  font-family: "STXingkai", "华文行楷", "方正行楷", "STKaiti", "楷体", serif;
  font-size: 28px;
  font-weight: 600;
  letter-spacing: 0.18em;
  color: #3a8a96;
}

.btn-settings {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.btn-settings:hover {
  background: var(--hover-bg);
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
  gap: 12px;
}

.user-menu {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 14px;
}

.user-btn:hover {
  background: var(--bg-hover);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  min-width: 160px;
  padding: 6px 0;
  z-index: 100;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  background: transparent;
  color: var(--text-primary);
  font-size: 14px;
  text-align: left;
}

.dropdown-item:hover {
  background: var(--bg-hover);
}


.home-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px;
}


.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.empty-icon {
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.empty-state p {
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.btn-primary {
  padding: 10px 20px;
  background: var(--primary-color);
  color: white;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-primary:disabled {
  background: var(--text-disabled);
}


.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}


.projects-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}


.project-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.group-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-tertiary);
  padding-left: 4px;
}


.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.project-card {
  position: relative;
  background: var(--bg-white);
  border-radius: var(--radius-md);
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
  box-shadow: var(--shadow-sm);
}

.project-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}


.project-card.theme-blue { background: linear-gradient(135deg, #FFFFFF 0%, #F0F7FF 100%); }
.project-card.theme-green { background: linear-gradient(135deg, #FFFFFF 0%, #F0FDF4 100%); }
.project-card.theme-orange { background: linear-gradient(135deg, #FFFFFF 0%, #FFF8F0 100%); }
.project-card.theme-red { background: linear-gradient(135deg, #FFFFFF 0%, #FFF5F5 100%); }
.project-card.theme-purple { background: linear-gradient(135deg, #FFFFFF 0%, #FAF5FF 100%); }
.project-card.theme-cyan { background: linear-gradient(135deg, #FFFFFF 0%, #F0FDFF 100%); }
.project-card.theme-pink { background: linear-gradient(135deg, #FFFFFF 0%, #FFF5F9 100%); }
.project-card.theme-brown { background: linear-gradient(135deg, #FFFFFF 0%, #FFFBEB 100%); }

.new-card {
  border: 2px dashed var(--border-color);
  background: transparent;
  box-shadow: none;
}

.new-card:hover {
  border-color: var(--primary-color);
  background: var(--primary-light);
  box-shadow: none;
  transform: none;
}

.new-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: var(--text-secondary);
  gap: 8px;
}

.new-icon {
  color: var(--text-tertiary);
}

.new-card:hover .new-icon {
  color: var(--primary-color);
}

.new-card:hover .new-card-content {
  color: var(--primary-color);
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-summary-wrapper {
  position: relative;
  margin-bottom: 6px;
  min-height: 17px;
}

.card-summary-wrapper:not(.placeholder):hover {
  z-index: 100;
}


.project-card:has(.card-summary-wrapper:not(.placeholder):hover) {
  z-index: 100;
}

.card-summary {
  font-size: 12px;
  color: #333;
  font-weight: 300;
  line-height: 1.4;
  cursor: default;
}

.card-summary-wrapper.placeholder .card-summary {
  visibility: hidden;
}

.summary-tooltip {
  position: absolute;
  left: 0;
  top: 100%;
  margin-top: 8px;
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-4px);
  transition: opacity 0.2s ease, transform 0.2s ease, visibility 0.2s;
  pointer-events: none;
}

.card-summary-wrapper:hover .summary-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.tooltip-content {
  background: rgba(30, 30, 30, 0.95);
  color: #fff;
  font-size: 13px;
  line-height: 1.5;
  padding: 12px 14px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-width: 280px;
  min-width: 200px;
  backdrop-filter: blur(8px);
}

.tooltip-content::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 16px;
  width: 12px;
  height: 12px;
  background: rgba(30, 30, 30, 0.95);
  transform: rotate(45deg);
  border-radius: 2px;
}

.card-meta {
  font-size: 12px;
  color: #333;
  font-weight: 300;
}


.card-menu-wrapper {
  position: absolute;
  top: 12px;
  right: 12px;
}

.card-menu-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  opacity: 0;
  transition: opacity 0.2s, background 0.2s;
}

.project-card:hover .card-menu-btn {
  opacity: 1;
}

.card-menu-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.card-dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  min-width: 120px;
  padding: 4px 0;
  z-index: 100;
  animation: dropdownFadeIn 0.15s ease;
}

@keyframes dropdownFadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  text-align: left;
  transition: background 0.15s;
}

.card-dropdown-item:hover {
  background: var(--bg-hover);
}

.card-dropdown-item.danger {
  color: var(--error-color);
}

.card-dropdown-item.danger:hover {
  background: rgba(239, 68, 68, 0.1);
}


.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  padding: 24px;
  width: 400px;
  max-width: 90vw;
  box-shadow: var(--shadow-lg);
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
}

.modal-input {
  width: 100%;
  padding: 12px 14px;
  font-size: 14px;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel {
  padding: 10px 20px;
  background: var(--bg-hover);
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  font-size: 14px;
}

.btn-cancel:hover {
  background: var(--bg-active);
}


.preflight-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.preflight-list {
  list-style: none;
  padding: 0;
  margin: 0 0 20px 0;
}

.preflight-list li {
  padding: 8px 12px;
  margin-bottom: 6px;
  background: var(--bg-hover);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-primary);
}

.preflight-list li::before {
  content: '•';
  color: var(--error-color, #ef4444);
  margin-right: 8px;
  font-weight: bold;
}
</style>
