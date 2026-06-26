<template>
  <span class="help-tooltip" tabindex="0" role="button" aria-label="Base URL 填写提示">
    <span class="help-tooltip-icon">!</span>
    <span class="tooltip-panel" role="tooltip">
      <strong>填写规则</strong>
      <span>只填服务根地址，不填最终 endpoint。</span>
      <span>OpenAI Chat 会请求 /chat/completions。</span>
      <span>Anthropic Messages 会请求 /v1/messages。</span>
      <strong>常见例子</strong>
      <span>DeepSeek OpenAI: https://api.deepseek.com</span>
      <span>DeepSeek Anthropic: https://api.deepseek.com/anthropic</span>
      <span>Claude 官方: https://api.anthropic.com</span>
      <span>NeoRouter Claude: https://api.neorouter.ai</span>
    </span>
  </span>
</template>

<style scoped>
.help-tooltip {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  border: 1px solid #c7c7c0;
  border-radius: 50%;
  background: #fff;
  color: #666;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  cursor: default;
  user-select: none;
}
.help-tooltip:focus-visible {
  outline: 2px solid #1a1a1a;
  outline-offset: 2px;
}
.help-tooltip::before {
  content: "";
  position: absolute;
  left: -10px;
  bottom: 100%;
  display: none;
  width: min(360px, calc(100vw - 48px));
  height: 12px;
}
.help-tooltip-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.tooltip-panel {
  position: absolute;
  left: -10px;
  bottom: calc(100% + 8px);
  z-index: 10;
  display: none;
  width: min(360px, calc(100vw - 48px));
  padding: 12px 14px;
  border: 1px solid #d8d8d2;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.12);
  color: #333;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.5;
  text-align: left;
  cursor: text;
  user-select: text;
}
.tooltip-panel::after {
  content: "";
  position: absolute;
  left: 14px;
  top: 100%;
  width: 8px;
  height: 8px;
  transform: translateY(-4px) rotate(45deg);
  border-right: 1px solid #d8d8d2;
  border-bottom: 1px solid #d8d8d2;
  background: #fff;
}
.tooltip-panel strong,
.tooltip-panel span {
  display: block;
}
.tooltip-panel strong {
  margin-top: 6px;
  color: #1a1a1a;
  font-weight: 600;
}
.tooltip-panel strong:first-child {
  margin-top: 0;
}
.help-tooltip:hover .tooltip-panel,
.help-tooltip:focus .tooltip-panel,
.help-tooltip:focus-within .tooltip-panel {
  display: block;
}
.help-tooltip:hover::before,
.help-tooltip:focus::before,
.help-tooltip:focus-within::before {
  display: block;
}
</style>
