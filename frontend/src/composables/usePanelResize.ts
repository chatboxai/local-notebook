import { onUnmounted, type Ref } from 'vue'

export interface PanelResizeConfig {
    
    width: Ref<number>
    
    isResizing: Ref<boolean>
    
    resizingSide: Ref<'left' | 'right' | null>
    
    side: 'left' | 'right'
    
    getConstraints: () => { minWidth: number; maxWidth: number }
}


export function usePanelResize(config: PanelResizeConfig) {
    const { width, isResizing, resizingSide, side, getConstraints } = config

    function handleMouseMove(e: MouseEvent) {
        if (!isResizing.value || resizingSide.value !== side) return

        const constraints = getConstraints()
        let newWidth: number

        if (side === 'left') {
            newWidth = e.clientX
        } else {
            newWidth = window.innerWidth - e.clientX
        }

        if (newWidth >= constraints.minWidth && newWidth <= constraints.maxWidth) {
            width.value = newWidth
        }
    }

    function handleMouseUp() {
        if (resizingSide.value === side) {
            isResizing.value = false
            resizingSide.value = null
        }
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
    }

    
    function startResize(e: MouseEvent) {
        e.preventDefault()
        isResizing.value = true
        resizingSide.value = side
        document.addEventListener('mousemove', handleMouseMove)
        document.addEventListener('mouseup', handleMouseUp)
    }

    
    onUnmounted(() => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
    })

    return {
        startResize
    }
}
