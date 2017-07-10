<template>
  <div class="page row">

    <div class="left-nav col-4">

      <ul class="ext-list">
        <li
          v-for="(ext, idx) in extensions"
          :class="{active: ext.url == activeExt.url}"
          @click="selectExtension(ext)"
          >
          <i :style="{'background-image': `url('${ext.icon}')`}"></i>
          <span>{{ ext.name }}</span>
        </li>
        <li class="add-link" @click="addExtDialog"><i class="fa fa-plus"></i> <span>Add extension</span></li>
      </ul>

      <b-modal
        ref="addExtForm"
        ok-title="Add"
        close-title="Cancel"
        hide-header-close
        no-auto-focus
        @shown="onAddExtFormShown"
        @ok="onAdd">
          <template slot="modal-title">
            Enter extension URL
          </template>

          <b-form-input
            class="github-url-input"
            ref="githubUrl"
            type="text"
            placeholder="https://github.com/org-name/project-name"></b-form-input>

          <div v-if="addingExtension" class="adding-ext-msg">
            <i class="fa fa-spinner fa-spin"></i> Downloading extension...
          </div>

          <div v-if="addingExtensionError" class="adding-ext-msg warning selectable">
            <i class="fa fa-warning"></i> {{ addingExtensionError }}
          </div>
      </b-modal>

    </div>

    <div class="col-8 ext-view">
        <extension-config
          v-if="activeExt"
          @removed="onRemoved"
          :extension="activeExt"></extension-config>

        <div v-if="!activeExt" class="no-extensions-msg">
          No Extensions Installed
        </div>
    </div>
  </div>
</template>

<script>
import jsonp from '@/api'
import bus from '@/event-bus'
import ExtensionConfig from '@/components/pages/ExtensionConfig'

export default {
  name: 'extensions',
  created () {
    this.fetchData()
  },
  components: {
    'extension-config': ExtensionConfig
  },
  data () {
    return {
      activeExt: null,
      addingExtension: false,
      addingExtensionError: '',
      extensions: []
    }
  },
  methods: {
    fetchData () {
      jsonp('prefs://extension/get-all').then((data) => {
        this.extensions = data
        this.activeExt = data[0]
      }, (err) => bus.$emit('error', err))
    },
    onAddExtFormShown () {
      this.$refs.githubUrl.focus()
      this.addingExtensionError = ''
    },
    addExtDialog () {
      this.$refs.addExtForm.show()
    },
    selectExtension (ext) {
      this.activeExt = ext
    },
    onRemoved (url) {
      for (let i = 0; i < this.extensions.length; i++) {
        if (this.extensions[i].url === url) {
          this.$delete(this.extensions, i)
          this.activeExt = this.extensions.length ? this.extensions[0] : null
          break
        }
      }
    },
    setActiveByUrl (url) {
      for (let i = 0; i < this.extensions.length; i++) {
        if (this.extensions[i].url === url) {
          this.activeExt = this.extensions[i]
          break
        }
      }
    },
    onAdd (e) {
      let input = this.$refs.githubUrl.$el
      this.addingExtension = true
      this.addingExtensionError = ''
      jsonp('prefs://extension/add', {url: input.value}).then((data) => {
        this.extensions = data
        this.addingExtension = false
        this.setActiveByUrl(input.value)
        input.value = ''
        this.$refs.addExtForm.hide()
      }, (err) => {
        this.addingExtension = false
        this.addingExtensionError = err
      })

      return e.cancel()
    }
  }
}
</script>

<style lang="scss" scoped>
$darkBlue: #015aa7;
$veryLightGrey: #c8c8c8;

.page {
  padding: 15px;
  padding-left: 25px;
}
.no-extensions-msg {
  text-align: center;
  color: #555;
  line-height: 40px;
}
.adding-ext-msg {
  color: #555;
  padding-top: 10px;
}
.warning {color: #b30000}
.ext-list {
  $listIconSize: 15px;

  list-style: none;
  padding: 0;
  margin: 0;
  margin-bottom: 10px;

  .add-link {
    font-style: italic;
  }

  li {
    cursor: pointer;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    text-align: left;
    position: relative;
    padding: 3px 0;
    margin: 3px 0;
    color: #555;

    i {
      margin-right: 5px;
      display: inline-block;
      background-repeat: no-repeat;
      background-size: $listIconSize $listIconSize;
      width: $listIconSize;
      height: $listIconSize;
    }

    &.active,
    &:hover {
      color: $darkBlue;
    }

    &.active span,
    &:hover span {
      text-decoration: underline;
    }
  }
}
</style>
