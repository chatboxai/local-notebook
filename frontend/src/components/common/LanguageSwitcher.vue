<template>
  <div class="language-switcher" :aria-label="t('language')">
    <button
      class="language-switcher-btn"
      :class="{ active: locale === 'zh' }"
      type="button"
      @click="setLocale('zh')"
    >
      {{ t('chinese') }}
    </button>
    <button
      class="language-switcher-btn"
      :class="{ active: locale === 'en' }"
      type="button"
      @click="setLocale('en')"
    >
      {{ t('english') }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { locale, setLocale, t } from '../../i18n'
</script>

<style scoped>
.language-switcher {
  display: inline-flex;
  flex-shrink: 0;
  padding: 3px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
}

.language-switcher-btn {
  min-width: 58px;
  height: 28px;
  padding: 0 12px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.language-switcher-btn.active {
  background: #111827;
  color: #fff;
}

@media (max-width: 640px) {
  .language-switcher-btn {
    min-width: 50px;
    padding: 0 10px;
  }
}
</style>
