<template>
  <div class="ext-config">
    <div class="header-info">
      <div class="logo">
        <img :src="extension.icon">
      </div>
      <div class="ext-info">
        <div class="ext-name">{{ extension.name }}</div>
        <div class="authors">by {{ extension.authors }}</div>
      </div>
      <div class="saved-notif">
        <i v-if="showSavedMsg" class="fa fa-check-circle"/>
      </div>
      <div class="menu">
        <b-dropdown
          right
          split
          class="m-2 menu-button"
          @click="onDropdownClick"
          :text="(canSave && 'Save') || (canCheckUpdates && 'Check Updates') || 'Remove'"
        >
          <b-dropdown-item @click="checkUpdates" v-if="canCheckUpdates && canSave">Check updates</b-dropdown-item>
          <b-dropdown-item @click="openRemoveModal">Remove</b-dropdown-item>
          <b-dropdown-divider v-if="extension.url"/>
          <b-dropdown-item v-if="extension.url" @click="openRepo">Open repository</b-dropdown-item>
          <b-dropdown-item v-if="extension.url && extension.url.includes('https://')" @click="reportIssue">Report issue</b-dropdown-item>
          <b-dropdown-item disabled v-if="extension.last_commit">
            <i class="fa fa-calendar fa-fw"></i>
            {{ extension.updated_at.slice(0, 10) }}
          </b-dropdown-item>
          <b-dropdown-item disabled v-if="extension.last_commit">
            <i class="fa fa-code-fork fa-fw"></i>
            <span class="text-monospace">{{ extension.last_commit.slice(0, 7) }}</span>
          </b-dropdown-item>
        </b-dropdown>
      </div>
    </div>

    <details class="installation-instructions" v-if="extension.instructions" :open="extension.runtime_error">
      <summary>Installation instructions</summary>
      <div v-html="extension.instructions"></div>
    </details>

    <div class="error-wrapper" v-if="extension.runtime_error">
      <ext-runtime-error
        :extUrl="extension.url"
        :errorMessage="extension.runtime_error.message"
        :errorName="extension.runtime_error.name"
      />
    </div>

    <div class="error-wrapper" v-if="extension.error">
      <ext-error-explanation
        is-updatable
        :extUrl="extension.url"
        :errorMessage="extension.error.message"
        :errorName="extension.error.name"
      />
    </div>

    <b-alert variant="dark" show v-if="extension.error && extension.error.name === 'ExtensionManifestError'">
      <small>
        To find out how to migrate Ulauncher extensions to the latest API version, see
        <a
          href
          @click.prevent="openUrl('https://docs.ulauncher.io/en/latest/extensions/migration.html')"
        >extension migration docs</a>.
      </small>
    </b-alert>

    <div class="ext-form" v-if="!extension.error && extension.is_running" ref="ext-form">
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

      <ext-error-explanation
        v-if="updateError"
        :extUrl="extension.url"
        :errorMessage="updateError.message"
        :errorName="updateError.name"
      />
    </b-modal>
  </div>
</template>

<script>
import fetchData from '@/fetchData'
import bus from '@/event-bus'
import ExtensionErrorExplanation from '@/components/widgets/ExtensionErrorExplanation'
import ExtensionRuntimeError from '@/components/widgets/ExtensionRuntimeError'

export default {
  components: {
    'ext-error-explanation': ExtensionErrorExplanation,
    'ext-runtime-error': ExtensionRuntimeError
  },
  name: 'extension-config',
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
    canCheckUpdates() {
      return !!this.$props.extension.url
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
    onDropdownClick() {
      switch (true) {
        case this.canSave:
          return this.save()
        case this.canCheckUpdates:
          return this.checkUpdates()
        default:
          return this.openRemoveModal()
      }
    },
    reportIssue() {
      this.openUrl(`${this.extension.url}/issues`)
    },
    openRepo() {
      this.openUrl(this.extension.url)
    },
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
        () => {
          this.updateState = 'updated'
          bus.$emit('extension/get-all')
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
}

.header-info .ext-info .ext-name {
      font-size: 1.3em;
}
.header-info .ext-info .authors {
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

.header-info .menu {
    flex: 0 0 0;
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
.ext-config button {
    margin-right: 10px;
}
</style>
