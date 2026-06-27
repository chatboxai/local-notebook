<template>
  <div class="admin-page">
    <header class="admin-header">
      <div class="header-left">
        <button class="icon-text-btn" @click="router.push('/')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
          </svg>
          返回
        </button>
        <h1>用户管理</h1>
      </div>
      <div class="header-right">
        <span class="admin-badge">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
          {{ currentUsername }}
        </span>
      </div>
    </header>

    <main class="admin-main">
      <div class="toolbar">
        <div class="toolbar-summary">
          <span>共 {{ total }} 位用户</span>
          <span>{{ adminCount }} 位管理员</span>
        </div>
        <button class="primary-btn" @click="openCreateModal">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M15 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm-9-2V7H4v3H1v2h3v3h2v-3h3v-2H6zm9 4c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
          开通用户
        </button>
      </div>

      <div v-if="loading" class="state-row">加载中...</div>
      <div v-else-if="users.length === 0" class="state-row">暂无用户</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>用户名</th>
              <th>角色</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.user_id">
              <td>
                <div class="username-cell">
                  <span>{{ user.username }}</span>
                  <small>{{ user.user_id }}</small>
                </div>
              </td>
              <td>
                <span class="role-badge" :class="user.role">{{ user.role === 'admin' ? '管理员' : '普通用户' }}</span>
              </td>
              <td>{{ formatDateTime(user.created_at) }}</td>
              <td>
                <div class="row-actions">
                  <button class="icon-btn" title="重置密码" @click="openResetModal(user)">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                      <path d="M12 17a2 2 0 0 0 2-2c0-.74-.4-1.38-1-1.72V11h2V9h-2V7h-2v2H9v2h2v2.28c-.6.34-1 .98-1 1.72a2 2 0 0 0 2 2zm6-8h-1V7A5 5 0 0 0 7 7v2H6c-1.1 0-2 .9-2 2v9c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-9c0-1.1-.9-2-2-2zM9 7a3 3 0 0 1 6 0v2H9V7z" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <section class="usage-section">
        <div class="section-header">
          <div>
            <h2>模型用量</h2>
            <p>按日期、用户、模型聚合</p>
          </div>
          <div class="usage-filters">
            <input v-model="usageFilters.start_date" type="date" />
            <input v-model="usageFilters.end_date" type="date" />
            <select v-model="usageFilters.user_id">
              <option value="">全部用户</option>
              <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                {{ user.username }}
              </option>
            </select>
            <button class="plain-btn" @click="loadUsage">刷新</button>
          </div>
        </div>

        <div class="usage-summary">
          <span>调用 {{ formatNumber(usageTotals.call_count) }} 次</span>
          <span>总计 {{ formatNumber(usageTotals.total_tokens) }} tokens</span>
          <span>输入 {{ formatNumber(usageTotals.input_uncached_tokens) }}</span>
          <span>缓存读 {{ formatNumber(usageTotals.input_cache_read_tokens) }}</span>
          <span>缓存写 {{ formatNumber(usageTotals.input_cache_write_tokens) }}</span>
          <span>输出 {{ formatNumber(usageTotals.output_tokens) }}</span>
        </div>

        <div v-if="usageLoading" class="state-row">加载用量中...</div>
        <div v-else-if="usageRows.length === 0" class="state-row">暂无用量记录</div>
        <div v-else class="table-wrap usage-table">
          <table>
            <thead>
              <tr>
                <th>日期</th>
                <th>用户</th>
                <th>模型</th>
                <th>次数</th>
                <th>未缓存输入</th>
                <th>缓存读</th>
                <th>缓存写</th>
                <th>输出</th>
                <th>合计</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in usageRows" :key="`${row.usage_date}-${row.user_id}-${row.model}`">
                <td>{{ row.usage_date }}</td>
                <td>{{ row.username }}</td>
                <td>
                  <span class="model-name">{{ row.model }}</span>
                </td>
                <td>{{ formatNumber(row.call_count) }}</td>
                <td>{{ formatNumber(row.input_uncached_tokens) }}</td>
                <td>{{ formatNumber(row.input_cache_read_tokens) }}</td>
                <td>{{ formatNumber(row.input_cache_write_tokens) }}</td>
                <td>{{ formatNumber(row.output_tokens) }}</td>
                <td>{{ formatNumber(row.total_tokens) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <div v-if="showCreate" class="modal-overlay" @click.self="closeCreateModal">
      <form class="modal" @submit.prevent="submitCreate">
        <h2>开通用户</h2>
        <label>
          用户名
          <input v-model="createForm.username" type="text" autocomplete="off" />
        </label>
        <label>
          初始密码
          <input v-model="createForm.password" type="password" autocomplete="new-password" />
        </label>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="modal-actions">
          <button type="button" class="plain-btn" @click="closeCreateModal">取消</button>
          <button type="submit" class="primary-btn" :disabled="submitting">
            {{ submitting ? '创建中...' : '创建' }}
          </button>
        </div>
      </form>
    </div>

    <div v-if="resetTarget" class="modal-overlay" @click.self="closeResetModal">
      <form class="modal" @submit.prevent="submitReset">
        <h2>重置密码</h2>
        <p class="modal-desc">{{ resetTarget.username }}</p>
        <label>
          新密码
          <input v-model="resetPassword" type="password" autocomplete="new-password" />
        </label>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="modal-actions">
          <button type="button" class="plain-btn" @click="closeResetModal">取消</button>
          <button type="submit" class="primary-btn" :disabled="submitting">
            {{ submitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  createAdminUser,
  getAdminUsage,
  getAdminUsers,
  resetAdminUserPassword,
  type AdminUsageRow,
  type AdminUsageTotals,
  type AdminUser,
} from '../services/api'
import { getDisplayUsername } from '../services/auth'

const router = useRouter()

const users = ref<AdminUser[]>([])
const total = ref(0)
const loading = ref(true)
const usageLoading = ref(true)
const usageRows = ref<AdminUsageRow[]>([])
const usageTotals = reactive<AdminUsageTotals>({
  call_count: 0,
  input_uncached_tokens: 0,
  input_cache_read_tokens: 0,
  input_cache_write_tokens: 0,
  output_tokens: 0,
  total_tokens: 0,
})
const submitting = ref(false)
const showCreate = ref(false)
const resetTarget = ref<AdminUser | null>(null)
const resetPassword = ref('')
const formError = ref('')

const createForm = reactive({
  username: '',
  password: '',
})

const usageFilters = reactive({
  start_date: toDateInputValue(addDays(new Date(), -29)),
  end_date: toDateInputValue(new Date()),
  user_id: '',
})

const currentUsername = computed(() => getDisplayUsername() || 'admin')
const adminCount = computed(() => users.value.filter(user => user.role === 'admin').length)

function toast(message: string, type: 'success' | 'error' = 'success') {
  window.dispatchEvent(new CustomEvent('global-toast', { detail: { message, type } }))
}

function errorMessage(error: any): string {
  return error?.response?.data?.detail || error?.message || '操作失败'
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function addDays(date: Date, days: number): Date {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}

function toDateInputValue(date: Date): string {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 10)
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('zh-CN').format(value || 0)
}

async function loadUsers() {
  try {
    loading.value = true
    const response = await getAdminUsers()
    users.value = response.users
    total.value = response.total
  } catch (error) {
    toast(errorMessage(error), 'error')
  } finally {
    loading.value = false
  }
}

async function loadUsage() {
  try {
    usageLoading.value = true
    const response = await getAdminUsage({
      start_date: usageFilters.start_date || undefined,
      end_date: usageFilters.end_date || undefined,
      user_id: usageFilters.user_id || undefined,
    })
    usageRows.value = response.rows
    Object.assign(usageTotals, response.totals)
  } catch (error) {
    toast(errorMessage(error), 'error')
  } finally {
    usageLoading.value = false
  }
}

function openCreateModal() {
  formError.value = ''
  createForm.username = ''
  createForm.password = ''
  showCreate.value = true
}

function closeCreateModal() {
  showCreate.value = false
}

async function submitCreate() {
  const username = createForm.username.trim()
  if (username.length < 2) {
    formError.value = '用户名至少 2 位'
    return
  }
  if (createForm.password.length < 6) {
    formError.value = '密码至少 6 位'
    return
  }

  try {
    submitting.value = true
    const created = await createAdminUser({
      username,
      password: createForm.password,
    })
    users.value = [created, ...users.value]
    total.value += 1
    showCreate.value = false
    toast('用户已开通')
  } catch (error) {
    formError.value = errorMessage(error)
  } finally {
    submitting.value = false
  }
}

function openResetModal(user: AdminUser) {
  resetTarget.value = user
  resetPassword.value = ''
  formError.value = ''
}

function closeResetModal() {
  resetTarget.value = null
}

async function submitReset() {
  if (!resetTarget.value) return
  if (resetPassword.value.length < 6) {
    formError.value = '密码至少 6 位'
    return
  }

  try {
    submitting.value = true
    await resetAdminUserPassword(resetTarget.value.user_id, resetPassword.value)
    closeResetModal()
    toast('密码已重置')
  } catch (error) {
    formError.value = errorMessage(error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  void loadUsers()
  void loadUsage()
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: #f7f8fa;
  color: #1f2937;
}

.admin-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.header-left,
.header-right,
.toolbar,
.toolbar-summary,
.row-actions,
.admin-badge,
.icon-text-btn,
.primary-btn {
  display: flex;
  align-items: center;
}

.header-left,
.header-right,
.toolbar-summary,
.row-actions {
  gap: 12px;
}

h1 {
  margin: 0;
  font-size: 17px;
  font-weight: 650;
}

.admin-main {
  max-width: 1160px;
  margin: 0 auto;
  padding: 24px;
}

.toolbar {
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.usage-section {
  margin-top: 28px;
}

.section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.section-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 650;
}

.section-header p {
  margin: 5px 0 0;
  color: #6b7280;
  font-size: 13px;
}

.usage-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.usage-filters input,
.usage-filters select {
  height: 34px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #374151;
  padding: 0 9px;
  font-size: 13px;
}

.usage-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.usage-summary span {
  padding: 5px 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  color: #4b5563;
  font-size: 13px;
}

.toolbar-summary {
  flex-wrap: wrap;
  color: #6b7280;
  font-size: 13px;
}

.toolbar-summary span {
  padding: 4px 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
}

.icon-text-btn,
.primary-btn,
.plain-btn,
.icon-btn {
  border: 1px solid #d1d5db;
  background: #fff;
  color: #374151;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.icon-text-btn,
.primary-btn {
  gap: 7px;
  height: 36px;
  padding: 0 12px;
}

.primary-btn {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}

.plain-btn {
  height: 36px;
  padding: 0 14px;
}

.icon-btn {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.icon-text-btn:hover,
.plain-btn:hover,
.icon-btn:hover {
  background: #f3f4f6;
}

.primary-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

button:disabled,
select:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.admin-badge {
  gap: 6px;
  color: #6b7280;
  font-size: 13px;
}

.state-row {
  padding: 48px 0;
  text-align: center;
  color: #6b7280;
}

.table-wrap {
  overflow-x: auto;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
}

.usage-table table {
  min-width: 1040px;
}

th,
td {
  padding: 13px 16px;
  border-bottom: 1px solid #eef0f3;
  text-align: left;
  font-size: 14px;
  vertical-align: middle;
}

th {
  color: #6b7280;
  font-size: 12px;
  font-weight: 650;
  background: #fafafa;
}

tr:last-child td {
  border-bottom: 0;
}

.username-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.username-cell small {
  color: #9ca3af;
  font-size: 11px;
}

.model-name {
  display: inline-block;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.modal input,
.role-badge {
  height: 36px;
}

.modal input {
  height: 36px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #1f2937;
  padding: 0 10px;
  font-size: 14px;
}

.role-badge {
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 13px;
  background: #eef2ff;
  color: #3730a3;
}

.role-badge.user {
  background: #f3f4f6;
  color: #4b5563;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.36);
  z-index: 20;
}

.modal {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 8px;
  padding: 22px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.24);
}

.modal h2 {
  margin: 0 0 18px;
  font-size: 18px;
}

.modal label {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-bottom: 14px;
  color: #374151;
  font-size: 13px;
  font-weight: 600;
}

.modal input {
  width: 100%;
}

.modal-desc {
  margin: -8px 0 16px;
  color: #6b7280;
  font-size: 13px;
}

.form-error {
  margin: 0 0 14px;
  padding: 10px 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #b91c1c;
  font-size: 13px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}

@media (max-width: 720px) {
  .admin-header {
    padding: 0 14px;
  }

  .admin-main {
    padding: 16px;
  }

  .toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .section-header {
    align-items: stretch;
    flex-direction: column;
  }

  .usage-filters {
    justify-content: flex-start;
  }

  .primary-btn {
    justify-content: center;
  }
}
</style>
