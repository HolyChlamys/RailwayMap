<script setup lang="ts">
import { NLayout, NLayoutHeader, NLayoutContent } from 'naive-ui'
import AppHeader from './components/common/AppHeader.vue'
</script>

<template>
  <n-layout class="h-screen">
    <n-layout-header bordered>
      <AppHeader />
    </n-layout-header>
    <n-layout-content>
      <router-view />
    </n-layout-content>
  </n-layout>
</template>
