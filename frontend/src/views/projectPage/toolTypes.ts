export const TOOL_TYPES = [
  { type: 'objective_positioning', titleKey: 'ui.objectivePositioning', tooltipKey: 'ui.objectivePositioningTooltip', color: 'cyan', icon: 'positioning', enabled: false },
  { type: 'audience_profile', titleKey: 'ui.audienceProfile', tooltipKey: 'ui.audienceProfileTooltip', color: 'amber', icon: 'audience', enabled: false },
  { type: 'comparative_analysis', titleKey: 'ui.comparativeAnalysis', tooltipKey: 'ui.comparativeAnalysisTooltip', color: 'indigo', icon: 'market', enabled: false },
  { type: 'content_summary', titleKey: 'ui.contentSummary', tooltipKey: 'ui.contentSummaryTooltip', color: 'green', icon: 'summary', enabled: false },
  { type: 'title_suggestion', titleKey: 'ui.titleSuggestion', tooltipKey: 'ui.titleSuggestionTooltip', color: 'purple', icon: 'title', enabled: false },
  { type: 'communication_copy', titleKey: 'ui.communicationCopy', tooltipKey: 'ui.communicationCopyTooltip', color: 'rose', icon: 'copy', enabled: false },
  { type: 'text_to_image', titleKey: 'ui.textToImage', tooltipKey: 'ui.textToImageTooltip', color: 'brown', icon: 'image', enabled: false },
  { type: 'reference_to_image', titleKey: 'ui.imageToImage', tooltipKey: 'ui.imageToImageTooltip', color: 'teal', icon: 'image_ref', enabled: false },
  { type: 'text_to_video', titleKey: 'ui.textToVideo', tooltipKey: 'ui.textToVideoTooltip', color: 'indigo', icon: 'video', enabled: false },
  { type: 'image_to_video', titleKey: 'ui.imageToVideo', tooltipKey: 'ui.imageToVideoTooltip', color: 'rose', icon: 'video_image', enabled: false },
  { type: 'start_end_to_video', titleKey: 'ui.startEndFrameVideo', tooltipKey: 'ui.startEndFrameVideoTooltip', color: 'amber', icon: 'video_frames', enabled: false },
]

export const IMAGE_GENERATION_TYPES = ['text_to_image', 'reference_to_image']
export const VIDEO_GENERATION_TYPES = ['text_to_video', 'image_to_video', 'start_end_to_video']
