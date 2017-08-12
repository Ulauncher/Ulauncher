<template>
  <div id="app" class="noselect">
    <header id="header">
      <NavBar />
    </header>
    <div class="page-content">
      <router-view></router-view>
    </div>

    <b-modal
        ref="errorModal"
        ok-only
        ok-title="Dismiss"
        hide-header-close
        @ok="onErrorDismiss">
          <template slot="modal-title">
            <i class="fa fa-warning"></i> Error
          </template>

          <div class="selectable">{{ error }}</div>
      </b-modal>
  </div>
</template>

<script>
import bus from '@/event-bus'
import NavBar from '@/components/NavBar'

export default {
  name: 'app',
  components: {
    NavBar
  },
  data () {
    return {
      error: ''
    }
  },
  created () {
    bus.$on('error', this.onError)
  },
  beforeDestroy () {
    bus.$off('error', this.onError)
  },
  methods: {
    onError (err) {
      this.error = err
      this.$refs.errorModal.show()
    },
    onErrorDismiss () {
      this.error = ''
    }
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
button {
  cursor: pointer;
}
#header {
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
