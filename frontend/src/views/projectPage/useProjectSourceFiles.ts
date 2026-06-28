import { computed, ref, watch } from 'vue'
import { getModelOutputLanguage } from '@/i18n'
import {
  deleteFile,
  getFiles,
  getFilesStatusBatch,
  updateFile,
  uploadFile,
} from '@/services/api'
import type { FileInfo } from '@/types'
import type { UploadingFile } from '@/components/project/source/types'
import { checkFileSize, isImageFile, MAX_FILE_COUNT } from './fileHelpers'

type ToastType = 'success' | 'error' | 'info' | 'warning'

interface ConfirmOptions {
  title: string
  message: string
  type?: 'info' | 'warning' | 'danger'
  confirmText?: string
  cancelText?: string
}

interface UseProjectSourceFilesOptions {
  projectId: string
  showToast: (message: string, type?: ToastType, duration?: number) => void
  showConfirm: (options: ConfirmOptions) => Promise<boolean>
  onFileDeleted?: (fileId: string) => void
}

export function useProjectSourceFiles({
  projectId,
  showToast,
  showConfirm,
  onFileDeleted,
}: UseProjectSourceFilesOptions) {
  const files = ref<FileInfo[]>([])
  const selectedFileIds = ref<string[]>([])
  const hoveringFileId = ref<string | null>(null)
  const pollingFileIds = ref<Set<string>>(new Set())
  const openMenuFileId = ref<string | null>(null)
  const showUploadModal = ref(false)
  const isUploading = ref(false)
  const uploadingFiles = ref<UploadingFile[]>([])
  let filePollingTimer: ReturnType<typeof setInterval> | null = null

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
  const isAllSelected = computed(() =>
    readyFiles.value.length > 0 && selectedFileIds.value.length === readyFiles.value.length
  )

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

  function toggleFileSelection(fileId: string, event?: Event) {
    event?.stopPropagation()
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

  function triggerFileUpload() {
    showUploadModal.value = true
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
        const uploaded = await uploadFile(
          projectId,
          file,
          (progress) => {
            uploadItem.progress = progress
          },
          getModelOutputLanguage()
        )
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
      const uploaded = await uploadFile(projectId, file, undefined, getModelOutputLanguage())
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
              error_message: fileStatus.error_message ?? undefined,
              processing_current: fileStatus.processing_current ?? null,
              processing_total: fileStatus.processing_total ?? null,
              processing_message: fileStatus.processing_message ?? null
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
      onFileDeleted?.(fileId)
    } catch (error) {
      console.error('Failed to delete file:', error)
    }
  }

  async function renameFile(fileId: string, newName: string) {
    await updateFile(fileId, { file_name: newName })
    const file = files.value.find(f => f.id === fileId)
    if (file) file.file_name = newName
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

  return {
    files,
    sortedFiles,
    readyFiles,
    hasReadyFiles,
    selectedFileIds,
    hoveringFileId,
    pollingFileIds,
    openMenuFileId,
    showUploadModal,
    isUploading,
    uploadingFiles,
    isAllSelected,
    maxFileCount: MAX_FILE_COUNT,
    loadFiles,
    toggleFileSelection,
    toggleSelectAll,
    triggerFileUpload,
    handleUploadFiles,
    handleInsertText,
    pollFileStatus,
    startFilePolling,
    stopFilePolling,
    handleDeleteFile,
    renameFile,
    toggleFileMenu,
    handleClickOutside,
  }
}
