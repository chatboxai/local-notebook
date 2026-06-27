export const TOOL_TYPES = [
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

export const IMAGE_GENERATION_TYPES = ['text_to_image', 'reference_to_image']
export const VIDEO_GENERATION_TYPES = ['text_to_video', 'image_to_video', 'start_end_to_video']
