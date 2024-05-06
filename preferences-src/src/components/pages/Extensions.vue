<template>
  <div class="page row">
    <div class="left-nav col-4">
      <ul class="ext-list">
        <li
          v-for="ext in extensions"
          v-bind:key="ext.id"
          :class="{active: ext.id == activeExtId}"
          @click="selectExtension(ext)"
        >
          <i class="ext-icon" :style="{'background-image': `url('${ext.icon}')`}"></i>
          <b-badge v-if="!ext.is_enabled">Disabled</b-badge>
          <b-badge v-else-if="ext.error_type" variant="warning">
            Error
          </b-badge>
          <b-badge v-else-if="ext.is_stopped">Stopped</b-badge>
          <span>{{ ext.name }}</span>
        </li>
        <li class="link" style="margin-top:25px" @click="addExtDialog">
          <b>
            <i class="fa fa-plus"></i>
            <span>Add extension</span>
          </b>
        </li>
        <li class="link" @click="reload">
          <i
            :class="{
            fa: true,
            ['fa-refresh']: !reloading,
            ['fa-spinner']: reloading,
            ['fa-spin']: reloading
          }"
          ></i>
          <span>Reload extensions</span>
        </li>
        <li class="link" @click="openUrlInBrowser('https://ext.ulauncher.io')">
          <i class="fa fa-external-link"></i>
          <span>Discover extensions</span>
        </li>
        <li class="link" @click="openUrlInBrowser('https://docs.ulauncher.io')">
          <i class="fa fa-external-link"></i>
          <span>Create your own</span>
        </li>
        <li v-if="prefsLoaded" class="api-version">Extension API v{{ this.prefs.env.api_version }}</li>
      </ul>

      <b-modal
        ref="addExtForm"
        ok-title="Add"
        close-title="Cancel"
        hide-header-close
        no-fade
        no-auto-focus
        size="lg"
        @shown="onAddExtFormShown"
        @ok="onModalOk"
      >
        <template slot="modal-title">Enter extension URL</template>

        <b-form @submit.prevent="onUrlSubmit">
          <b-form-input
            class="repo-url-input"
            ref="repoUrl"
            type="text"
            placeholder="https://github.com/user/repo.git"
          ></b-form-input>
        </b-form>

        <div v-if="extensionIsInstalling" class="adding-ext-msg">
          <i class="fa fa-spinner fa-spin"></i> Installing extension...
        </div>

        <div class="error-wrapper" v-if="error && error.type">
          <ext-install-error
            :extUrl="extUrlToDownload"
            :errorMessage="error.message"
            :errorType="error.type"
          />
        </div>

        <small v-if="error && error.details">
          <i class="fa fa-copy"></i>
          <a
            class="text-muted"
            href
            @click.prevent
            v-clipboard:copy="error.details"
          >Copy error details to clipboard</a>
        </small>
      </b-modal>
    </div>

    <div class="col-8 ext-view">
      <extension-config v-if="activeExtId" @removed="removeExtension" v-on:reload="reload" :extension="extensions[activeExtId]"></extension-config>
    </div>
  </div>
</template>

<script>
import fetchData from '@/fetchData'
import bus from '@/event-bus'
import { mapState, mapGetters } from 'vuex'
import ExtensionConfig from '@/components/pages/ExtensionConfig'
import ExtensionInstallError from '@/components/widgets/ExtensionInstallError'

export default {
  name: 'extensions',
  created() {
    this.fetchData()
    bus.$on('extension/get-all', this.fetchData)
    bus.$on('extension/update-extension', this.updateExtension)
    bus.$on('extension/remove', this.removeExtension)
  },
  beforeDestroy() {
    bus.$off('extension/get-all', this.fetchData)
    bus.$off('extension/update-extension', this.updateExtension)
    bus.$off('extension/remove', this.removeExtension)
  },
  components: {
    'extension-config': ExtensionConfig,
    'ext-install-error': ExtensionInstallError
  },
  computed: {
    ...mapState(['prefs']),
    ...mapGetters(['prefsLoaded'])
  },
  data() {
    return {
      extUrlToDownload: '',
      activeExtId: null,
      extensionIsInstalling: false,
      reloading: false,
      error: null,
      extensions: {}
    }
  },
  methods: {
    updateExtension(extension) {
      this.extensions[extension.id] = extension
    },
    fetchData(reload = false) {
      fetchData('prefs:///extension/get-all', reload).then(
        extensions => {
          this.extensions = extensions;
          if (!(this.activeExtId in extensions)) {
            this.activeExtId = Object.keys(extensions)[0]
          }
          setTimeout(() => {
            this.reloading = false
          }, 500)
        },
        err => bus.$emit('error', err)
      )
    },
    onAddExtFormShown() {
      this.$nextTick(() => this.$refs.repoUrl.focus())
      this.error = null
    },
    addExtDialog() {
      this.$refs.addExtForm.show()
    },
    // force reload = try to start any extensions that are not disabled but not running
    reload(force = false) {
      this.reloading = true
      this.fetchData(force)
    },
    openUrlInBrowser(url) {
      fetchData('prefs:///open/web-url', url)
    },
    selectExtension(ext) {
      this.activeExtId = ext.id
    },
    removeExtension(id) {
      this.$delete(this.extensions, id)
      this.activeExtId = Object.keys(this.extensions)[0]
    },
    onModalOk(e) {
      let input = this.$refs.repoUrl.$el
      if (input.value) {
        this.addExtension(input)
      }
      return e.preventDefault()
    },
    onUrlSubmit() {
      let input = this.$refs.repoUrl.$el
      if (input.value) {
        this.addExtension(input)
      }
    },
    addExtension(input) {
      this.extUrlToDownload = input.value
      this.extensionIsInstalling = true
      this.error = null
      fetchData('prefs:///extension/add', input.value).then(
        extension => {
          this.extensionIsInstalling = false
          this.activeExtId = extension.id
          this.extensions[extension.id] = extension;
          input.value = ''
          this.$refs.addExtForm.hide()
        },
        err => {
          this.extensionIsInstalling = false
          this.error = err
        }
      )
    }
  }
}
</script>

<style lang="css" scoped>
.page {
  padding: 20px 15px 15px 25px;
}
.adding-ext-msg {
  overflow: auto;
  color: #555;
  padding-top: 15px;
}
.warning {
  color: #b30000;
}
.left-nav {
  flex: 0 0 250px;
}
.ext-view {
  flex: 1;
  max-width: none;
  min-height: 350px;
}
.error-wrapper {
  margin-top: 20px;
}
.ext-list {
  --list-icon-size: 17px;

  list-style: none;
  padding: 0;
  margin: 0;
  margin-bottom: 10px;
}
.ext-list li {
    cursor: pointer;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    text-align: left;
    position: relative;
    padding: 3px 0;
    margin: 3px 0;
    color: #555;
}

.ext-list li i {
      margin-right: 5px;
      width: var(--list-icon-size);
      height: var(--list-icon-size);
}

.ext-list li .ext-icon {
      display: inline-block;
      background-repeat: no-repeat;
      background-size: var(--list-icon-size) var(--list-icon-size);
      position: relative;
      top: 3px;
}

.ext-list li.active,
.ext-list li:active,
.ext-list li:hover {
      color: var(--dark-blue);
}

.ext-list li.active span,
.ext-list li:active span,
.ext-list li:hover span {
      text-decoration: underline;
}

.ext-list li.api-version {
      cursor: default;
      font-size: 15px;
      color: #888;
      text-shadow: 1px 1px 1px #fff;
}

.ext-list .link {
    font-style: italic;
}
</style>
