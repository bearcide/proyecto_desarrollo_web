<template>
  <div class="app-root">
    <router-view />
    <ToastContainer />
  </div>
</template>

<script setup>
import ToastContainer from './components/ToastContainer.vue';
</script>

<style>
.app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
