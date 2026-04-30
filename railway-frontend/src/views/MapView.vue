<script setup lang="ts">
import MapContainer from '../components/map/MapContainer.vue'
import SearchPanel from '../components/search/SearchPanel.vue'
import MapLegend from '../components/map/MapLegend.vue'
</script>

<template>
  <div class="relative w-full h-full">
    <MapContainer />
    <SearchPanel />
    <MapLegend />
  </div>
</template>
