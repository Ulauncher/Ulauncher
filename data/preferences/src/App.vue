<template>
  <div id="app" class="noselect">
    <NavBar />
    <router-view></router-view>
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

html {
  font-family: 'Ubuntu', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f2f2f2;
  border: 1px solid #e4e4e4;
}
body {
  color: #3d3d3d;
  background: #f2f2f2;
  overflow: hidden;
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
