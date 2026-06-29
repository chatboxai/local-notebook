import common from './common'
import ui from './ui'
import workflowPrompts from './workflowPrompts'

export default {
  ...common,
  ui,
  workflowPrompts,
} as const
