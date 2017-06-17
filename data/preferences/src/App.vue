<template>
  <div id="app" class="noselect">
    <header>
      <NavBar />
    </header>
    <div class="page-content">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>

import NavBar from '@/components/NavBar'

export default {
  name: 'app',
  components: {
    NavBar
  }
}
</script>

<style>
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
html {
  font-family: 'Ubuntu', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f2f2f2;
}
body {
  color: #3d3d3d;
  background: #f2f2f2;
  border: 1px solid #e4e4e4;
}
header {
  width: 100%;
  height: 60px;
  position: fixed;
  top: 0;
}
#app {
  height: 100%;
}
.page-content {
  margin-top: 60px;
  max-height: calc(100% - 60px);
  overflow-y: auto;
  overflow-x: hidden;
}
.noselect {
  -webkit-user-select: none;
  user-select: none;
}
.selectable {
  -webkit-user-select: auto;
  user-select: auto;
}

</style>
