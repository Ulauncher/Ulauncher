<template>
  <div id="app" class="noselect">
    <header id="header">
      <NavBar/>
    </header>
    <div class="page-content">
      <router-view></router-view>
    </div>

    <b-modal
      ref="errorModal"
      ok-only
      no-fade
      ok-title="Dismiss"
      hide-header-close
      @ok="onErrorDismiss"
    >
      <template slot="modal-title">
        <i class="fa fa-warning"></i> Error
      </template>

      <div class="selectable">
        <p>An unexpected error has occurred.</p>
        <p>
          Please copy error details and create a bug in
          <a
            href
            @click.prevent="openUrlInBrowser('https://github.com/Ulauncher/Ulauncher/issues')"
          >Github Issues</a>.
        </p>
        <small>
          <i class="fa fa-copy"></i>
          <a
            class="text-muted"
            href
            @click.prevent
            v-clipboard:copy="error && error.details"
          >Copy error details to clipboard</a>
        </small>
      </div>
    </b-modal>
  </div>
</template>

<script>
import fetchData from '@/fetchData'
import bus from '@/event-bus'
import NavBar from '@/components/NavBar'

export default {
  name: 'app',
  components: {
    NavBar
  },
  data() {
    return {
      error: null
    }
  },
  created() {
    this.$store.dispatch('getAllPrefs')
    bus.$on('error', this.onError)
  },
  beforeDestroy() {
    bus.$off('error', this.onError)
  },
  methods: {
    openUrlInBrowser(url) {
      fetchData('prefs:///open/web-url', url)
    },
    onError(err) {
      this.error = err
      this.$refs.errorModal.show()
    },
    onErrorDismiss() {
      this.error = null
    }
  }
}
</script>

<style>
html,
body {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
body {
  color: #3d3d3d;
  background: #f2f2f2;
  border: 1px solid #c7c7c7;
}

/* custom scrollbar */
/* width */
::-webkit-scrollbar {
  width: 10px;
}
/* Track */
::-webkit-scrollbar-track {
  background: #f1f1f1;
  margin-right: 3px;
}
/* Handle */
::-webkit-scrollbar-thumb {
  background: #999;
  border-radius: 9px;
  background-clip: padding-box;
  border: 3px solid rgba(0, 0, 0, 0);
}
/* Handle on hover */
::-webkit-scrollbar-thumb:hover {
}
::-webkit-scrollbar-button {
  width: 0;
  height: 0;
  display: none;
}
::-webkit-scrollbar-corner {
  background-color: transparent;
}

button {
  cursor: pointer;
}
#header {
  height: 69px;
  position: fixed;
  top: 0;
  left: 1px;
  right: 1px;
}
#app {
  height: 100%;
}
.page-content {
  position: relative;
  top: 69px;
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
