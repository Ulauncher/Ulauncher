<template>
  <div class="ext-config">
    <div class="header-info">
      <div class="logo">
        <img :src="extension.icon">
      </div>
      <div class="ext-info">
        <div class="ext-name">{{ extension.name }}</div>
        <div class="authors">by {{ extension.authors }}</div>
        <div class="repo" v-if="extension.url">
          <div v-if="extension.commit_hash"><i class="fa fa-code-fork fa-fw"></i><span class="text-monospace">{{ extension.commit_hash.slice(0, 7) }}</span></div>
          <div v-if="extension.commit_hash"><i class="fa fa-calendar fa-fw"></i>{{ extension.updated_at.slice(0, 10) }}</div>
          <div v-if="extension.browser_url">
            <a class="text-muted" href @click.prevent="openUrl(extension.browser_url)" :title="extension.browser_url">
              <i class="fa fa-external-link"></i> Open repository
            </a>
          </div>
          <div v-if="!extension.browser_url">
            <i class="fa fa-copy"></i>
            <a class="text-muted" href @click.prevent
             v-clipboard:copy="extension.url"
             :title="'Click to copy: ' + extension.url">Copy url</a>
          </div>
        </div>
        <div class="notes">
          <span v-if="extension.is_manageable">User installed</span>
          <span v-if="!extension.is_manageable">Externally managed,</span>
          <a class="text-muted" href @click.prevent
             v-clipboard:copy="extension.path"
             :title="extension.path"><i class="fa fa-copy"></i> copy path</a>
        </div>
        <div class="notes" v-if="extension.duplicate_paths.length > 0">
          Duplicates found,
          <a class="text-muted" href @click.prevent
             :title="extension.duplicate_paths.map((p) => `- ${p}`).join('\n')">
             <i class="fa fa-copy"></i>
             copy paths
          </a>
        </div>
      </div>
      <div class="saved-notif">
        <i v-if="showSavedMsg" class="fa fa-check-circle"/>
      </div>
      <div>
        <b-button-group>
          <b-button @click="save" v-if="canSave && !extension.error_type" title="Save preferences"><i class="fa fa-check"></i></b-button>
          <b-button @click="checkUpdates" v-if="extension.url" title="Check updates"><i class="fa fa-refresh"></i></b-button>
          <b-button @click="openRemoveModal" v-if="isManageable" title="Remove"><i class="fa fa-trash"></i></b-button>
          <b-button
            @click="setIsEnabled(!extension.is_enabled || !!extension.error_type)"
            :variant="(extension.is_enabled && !extension.error_type) ? 'success' : 'outline-secondary'"
            :disabled="!['', 'Terminated'].includes(extension.error_type)"
            :title="(extension.is_enabled && !extension.error_type) ? 'Disable extension' : 'Enable extension'"
          >
            {{ (extension.is_enabled && !extension.error_type) ? 'ON' : 'OFF' }}
          </b-button>
        </b-button-group>
      </div>
    </div>

    <details class="installation-instructions" v-if="extension.instructions" :open="extension.error_type">
      <summary>Installation instructions</summary>
      <div v-html="extension.instructions"></div>
    </details>

    <div class="error-wrapper" v-if="extension.error_type && extension.is_enabled">
      <ext-runtime-error
        :extUrl="extension.browser_url"
        :errorMessage="extension.error_message"
        :errorType="extension.error_type"
      />
    </div>

    <div class="ext-form" v-if="!extension.error_type" ref="ext-form">
      <template v-for="(trigger, id) in extension.triggers">
        <b-form-group
          v-if="trigger.keyword"
          :key="id"
          :description="trigger.description"
          :label="`${trigger.name} keyword`"
        >
          <b-form-input :ref="`trigger_keyword_${id}`" :value="trigger.user_keyword"></b-form-input>
        </b-form-group>
      </template>

      <b-form-group
        v-for="(pref, id) in extension.preferences"
        :key="id"
        :description="pref.description"
        :label="pref.type === 'checkbox' ? '' : pref.name"
      >
        <b-form-input v-if="pref.type === 'input'" :ref="`pref_${id}`" :value="pref.value"></b-form-input>
        <b-form-input v-if="pref.type === 'number'" :ref="`pref_${id}`" :value="pref.value" type="number" :min="pref.min" :max="pref.max"></b-form-input>
        <b-form-checkbox v-if="pref.type === 'checkbox'" :ref="`pref_${id}`" :checked="pref.value">{{ pref.name }}</b-form-checkbox>
        <b-form-textarea v-if="pref.type === 'text'" :ref="`pref_${id}`" :value="pref.value" rows="3" max-rows="5"></b-form-textarea>
        <b-form-select v-if="pref.type === 'select'" :ref="`pref_${id}`" :value="pref.value" :options="pref.options"></b-form-select>
      </b-form-group>
    </div>

    <b-modal
      title="Removing Extension"
      ref="removeExtensionModal"
      close-title="Cancel"
      ok-title="Yes"
      ok-variant="danger"
      no-fade
      hide-header-close
      v-model="removeExtModal"
      @ok="remove"
    >Are you sure?</b-modal>

    <b-modal
      title="Update Extension"
      ref="removeExtensionModal"
      close-title="Close"
      :ok-title="updateOkTitle"
      v-model="updateExtModal"
      :ok-variant="updateOkBtnVariant"
      :ok-only="hideCancelOnUpdateModal"
      :ok-disabled="updateState === 'updating'"
      no-fade
      hide-header-close
      @ok.prevent="onUpdateConfirm"
    >
      <div v-if="updateState == 'checking-updates'">
        <i class="fa fa-spinner fa-spin"></i> Checking for updates...
      </div>
      <div v-if="updateState == 'update-available'">
        <p>
          New version is available:
          &nbsp;&nbsp;&nbsp;
          <i class="fa fa-code-fork"></i>
          {{ commitHash.slice(0, 7) }}
        </p>
      </div>
      <div v-if="updateState == 'no-updates'">No new updates are available</div>
      <div v-if="updateState == 'updating'">
        <i class="fa fa-spinner fa-spin"></i> Updating...
      </div>
      <div v-if="updateState == 'updated'">
        <i class="fa fa-check-circle"></i> Updated
      </div>

      <ext-install-error
        v-if="updateError"
        :extUrl="extension.browser_url"
        :errorMessage="updateError.message"
        :errorType="updateError.type"
      />
    </b-modal>
  </div>
</template>

<script>
import fetchData from '@/fetchData'
import bus from '@/event-bus'
import ExtensionInstallError from '@/components/widgets/ExtensionInstallError'
import ExtensionRuntimeError from '@/components/widgets/ExtensionRuntimeError'

export default {
  components: {
    'ext-install-error': ExtensionInstallError,
    'ext-runtime-error': ExtensionRuntimeError
  },
  name: 'extension-preferences',
  props: ['extension'],
  data() {
    return {
      updateExtModal: false,
      removeExtModal: false,
      showSavedMsg: false,
      updateError: null,
      updateState: null, // null | checking-updates | update-available | no-updates | updating | updated
      commitHash: null
    }
  },
  computed: {
    canSave() {
      const { preferences, triggers } = this.$props.extension
      return Boolean(Object.keys(triggers).length || Object.keys(preferences).length)
    },
    isManageable() {
      return this.$props.extension.is_manageable
    },
    updateOkBtnVariant() {
      if (this.updateState === 'checking-updates') {
        return 'secondary'
      }
      return 'primary'
    },
    hideCancelOnUpdateModal() {
      return !this.updateState || this.updateState !== 'update-available'
    },
    updateOkTitle() {
      if (this.updateState === 'update-available') {
        return 'Update'
      }
      return 'OK'
    }
  },
  methods: {
    save() {
      let triggers = {}
      let preferences = {}
      Object.entries(this.extension.triggers).forEach(([id, trigger]) => {
        triggers[id] = {}
        let { $el } = this.$refs[`trigger_keyword_${id}`][0]
        if (trigger.keyword) {
          triggers[id].keyword = trigger.user_keyword = $el.value.trim()
        }
      });
      Object.entries(this.extension.preferences).forEach(([id, pref]) => {
        let { $el } = this.$refs[`pref_${id}`][0]
        if (pref.type === 'checkbox') {
          pref.value = $el.firstChild.checked
        } else if (pref.type === 'keyword') {
          pref.value = $el.value.trim()
        } else if (pref.type === 'number') {
          pref.value = $el.valueAsNumber
        } else {
          pref.value = $el.value
        }
        preferences[id] = pref.value
      });

      fetchData('prefs:///extension/set-prefs', this.extension.id, {triggers, preferences}).then(
        () => {
          this.showSavedMsg = true
          setTimeout(() => {
            this.showSavedMsg = false
          }, 1e3)
        },
        err => bus.$emit('error', err)
      )
    },
    openRemoveModal() {
      this.removeExtModal = true
    },
    onUpdateConfirm() {
      switch (this.updateState) {
        case 'update-available':
          this.update()
          break
        default:
          this.updateState = null
          this.updateExtModal = false
      }
    },
    remove() {
      fetchData('prefs:///extension/remove', this.extension.id).then(
        () => {
          this.$emit('removed', this.extension.id)
          bus.$emit('extension/remove', this.extension.id)
        },
        err => {
          bus.$emit('error', err)
        }
      )
    },
    checkUpdates() {
      this.updateError = null
      this.updateExtModal = true
      this.commitHash = null
      this.updateState = 'checking-updates'
      fetchData('prefs:///extension/check-update', this.extension.id)
        .then(
          ([hasUpdate, commitHash]) => {
            this.commitHash = commitHash
            this.updateState = hasUpdate ? 'update-available' : 'no-updates'
          },
          err => {
            this.updateState = null
            this.updateError = err
          }
        )
    },
    update() {
      this.updateError = null
      this.updateState = 'updating'
      fetchData('prefs:///extension/update-ext', this.extension.id).then(
        (extension) => {
          this.updateState = 'updated'
          bus.$emit('extension/update-extension', extension)
        },
        err => {
          this.updateState = null
          this.updateError = err
        }
      )
    },
    openUrl(url) {
      fetchData('prefs:///open/web-url', url)
    },
    setIsEnabled(enable) {
      fetchData('prefs:///extension/toggle-enabled', this.extension.id, enable).then(() => {
          this.$emit('reload')
        },
        err => {
          bus.$emit('error', err)
        }
      )
    },
  }
}
</script>

<style lang="css" scoped>
.header-info {
  display: flex;
  margin-bottom: 15px;
}

.header-info .logo {
  flex: 0 0 70px;
}

.header-info .logo img {
  width: 55px;
}

.header-info .ext-info {
  flex: 1 0 0;
  line-height: 1.75;
}

.header-info .ext-info .ext-name {
  font-size: 1.3em;
}
.header-info .ext-info .authors {
  font-style: italic;
  opacity: 0.8;
}
.header-info .ext-info .repo {
  font-size: 0.9em;
  opacity: 0.8;
  display: flex;
  position: relative;
  left: -4px;
}
.header-info .ext-info .repo > div {
  margin-right: 8px;
}
.header-info .ext-info .notes {
  font-size: smaller;
  font-style: italic;
  opacity: 0.8;
}

.header-info .saved-notif {
  flex: 0 0 20px;
  font-size: 20px;
  position: relative;
  right: 0;
  top: 10px;
  opacity: 0.9;
}

.menu-button {
  white-space: nowrap !important;
}
.menu-button a {
  outline: none;
}
.installation-instructions {
  font-size: 14px;
  margin-bottom: 5px;
}
.installation-instructions summary {
  font-weight: 500;
}

.ext-form {
  padding-top: 15px;
}
.ext-form .row {
  display: block;
}
.error-wrapper {
  margin-top: 20px;
}
.ext-config h1 {
  font-size: 1.3em;
}
.ext-config small {
  font-style: italic;
}
</style>
