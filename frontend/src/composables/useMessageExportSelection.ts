import { ref, type Ref } from 'vue'
import { exportChatMessagesToWord } from '../services/api'
import type { Message, Session } from '../types'

type ToastType = 'success' | 'error' | 'info' | 'warning'
type ShowToast = (message: string, type?: ToastType, duration?: number) => void

interface UseMessageExportSelectionOptions {
  messages: Ref<Message[]>
  currentSession: Ref<Session | null>
  isStreaming: Ref<boolean>
  showToast: ShowToast
}

export function useMessageExportSelection({
  messages,
  currentSession,
  isStreaming,
  showToast
}: UseMessageExportSelectionOptions) {
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
    selectedUserMessageIds.value = userMessageId ? [userMessageId] : []
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

    selectedUserMessageIds.value = selectedUserMessageIds.value.length === userMsgIds.length
      ? []
      : userMsgIds
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

  return {
    isExportSelectionMode,
    selectedUserMessageIds,
    isExportingMessages,
    toggleExportSelectionMode,
    enterExportModeWithSelection,
    toggleMessageSelection,
    isMessageInSelectedConversation,
    toggleConversationSelection,
    toggleSelectAllUserMessages,
    handleExportSelectedMessages,
  }
}
