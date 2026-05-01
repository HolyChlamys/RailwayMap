<script setup lang="ts">
import MapContainer from '../components/map/MapContainer.vue'
import SearchPanel from '../components/search/SearchPanel.vue'
import MapLegend from '../components/map/MapLegend.vue'
</script>

<template>
  <div style="position:relative;width:100%;height:100%">
    <MapContainer />
    <SearchPanel />
    <MapLegend />
  </div>
</template>
