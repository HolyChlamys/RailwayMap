<script setup lang="ts">
import { NLayout, NLayoutHeader, NLayoutContent } from 'naive-ui'
import AppHeader from './components/common/AppHeader.vue'
</script>

<template>
  <n-layout style="height:100vh;display:flex;flex-direction:column">
    <n-layout-header bordered>
      <AppHeader />
    </n-layout-header>
    <n-layout-content style="flex:1;overflow:hidden">
      <router-view />
    </n-layout-content>
  </n-layout>
</template>
