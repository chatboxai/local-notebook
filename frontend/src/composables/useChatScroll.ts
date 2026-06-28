import { nextTick, onMounted, onUnmounted, ref, watch, type Ref } from 'vue'

interface UseChatScrollOptions {
  messages: Ref<unknown[]>
  streamingParts: Ref<unknown[]>
  messagesRef: Ref<HTMLDivElement | null>
  textareaRef: Ref<HTMLTextAreaElement | null>
  inputWrapperRef: Ref<HTMLDivElement | null>
  hasMoreMessages: Ref<boolean>
  isLoadingMoreMessages: Ref<boolean>
  loadOlderMessages: () => Promise<void> | void
}

export function useChatScroll({
  messages,
  streamingParts,
  messagesRef,
  textareaRef,
  inputWrapperRef,
  hasMoreMessages,
  isLoadingMoreMessages,
  loadOlderMessages,
}: UseChatScrollOptions) {
  const isMessagesScrollable = ref(false)
  const isUserScrolling = ref(false)
  const showScrollToBottom = ref(false)
  const scrollBtnBottom = ref(100)

  function checkMessagesScrollable() {
    nextTick(() => {
      if (messagesRef.value) {
        isMessagesScrollable.value = messagesRef.value.scrollHeight > messagesRef.value.clientHeight
      }
    })
  }

  function updateScrollBtnPosition() {
    const wrapper = inputWrapperRef.value
    if (wrapper) {
      scrollBtnBottom.value = wrapper.offsetHeight + 20
    }
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

  function resetTextareaHeight() {
    const textarea = textareaRef.value
    if (textarea) {
      textarea.style.height = 'auto'
    }

    nextTick(() => updateScrollBtnPosition())
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
      void loadOlderMessages()
    }
  }

  watch(messages, () => {
    checkMessagesScrollable()
  }, { flush: 'post' })

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

  onMounted(() => {
    nextTick(() => updateScrollBtnPosition())
    window.addEventListener('resize', checkMessagesScrollable)
    checkMessagesScrollable()
  })

  onUnmounted(() => {
    window.removeEventListener('resize', checkMessagesScrollable)
  })

  return {
    isMessagesScrollable,
    isUserScrolling,
    showScrollToBottom,
    scrollBtnBottom,
    checkMessagesScrollable,
    updateScrollBtnPosition,
    autoResizeTextarea,
    resetTextareaHeight,
    scrollToBottom,
    forceScrollToBottom,
    handleMessagesScroll,
  }
}
