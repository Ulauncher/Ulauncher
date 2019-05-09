<template>
  <div class="ext-config">
    <div class="header-info">
      <div class="logo">
        <img :src="extension.icon">
      </div>
      <div class="ext-info">
        <div class="ext-name">{{ extension.name }}</div>
        <div class="developer-name">by {{ extension.developer_name }}</div>
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
          <b-dropdown-item @click="checkUpdates" v-if="canCheckUpdates && canSave">Check Updates</b-dropdown-item>
          <b-dropdown-item @click="openRemoveModal">Remove</b-dropdown-item>
          <b-dropdown-divider/>
          <b-dropdown-item v-if="extension.url" @click="reportIssue">Report Issue</b-dropdown-item>
          <b-dropdown-item v-if="extension.url" @click="openGithub">Open Github</b-dropdown-item>
          <b-dropdown-item disabled v-if="extension.last_commit">
            <i class="fa fa-calendar fa-fw"></i>
            {{ lastCommitDate }}
          </b-dropdown-item>
          <b-dropdown-item disabled v-if="extension.last_commit">
            <i class="fa fa-code-fork fa-fw"></i>
            <span class="text-monospace">{{ extension.last_commit.substring(0, 7) }}</span>
          </b-dropdown-item>
        </b-dropdown>
      </div>
    </div>

    <div class="error-wrapper" v-if="extension.error">
      <ext-error-explanation
        is-update
        :extUrl="extension.url"
        :errorMessage="extension.error.message"
        :errorName="extension.error.errorName"
      />
    </div>

    <div class="ext-form" v-if="!extension.error">
      <template v-for="pref in extension.preferences">
        <b-form-fieldset
          v-if="pref.type == 'keyword'"
          :label="`${pref.name} keyword`"
          class="keyword-input"
          :description="pref.description"
        >
          <b-form-input :ref="pref.id" :value="pref.value"></b-form-input>
        </b-form-fieldset>

        <b-form-fieldset
          v-if="pref.type == 'input'"
          :label="pref.name"
          :description="pref.description"
        >
          <b-form-input :ref="pref.id" :value="pref.value"></b-form-input>
        </b-form-fieldset>

        <b-form-fieldset
          v-if="pref.type == 'text'"
          :label="pref.name"
          :description="pref.description"
        >
          <b-form-input textarea :ref="pref.id" :value="pref.value" :rows="3"></b-form-input>
        </b-form-fieldset>

        <b-form-fieldset
          v-if="pref.type == 'select'"
          :label="pref.name"
          :description="pref.description"
        >
          <b-form-select :ref="pref.id" :value="pref.value" :options="pref.options"></b-form-select>
        </b-form-fieldset>
      </template>
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
          {{ newVersionInfo.last_commit.substring(0, 7) }}
          &nbsp;&nbsp;&nbsp;
          <i
            class="fa fa-calendar"
          ></i>
          {{ isoDateToHumanDate(newVersionInfo.last_commit_time) }}
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
        :errorName="updateError.errorName"
      />
    </b-modal>
  </div>
</template>

<script>
import jsonp from '@/api'
import bus from '@/event-bus'
import ExtensionErrorExplanation from '@/components/widgets/ExtensionErrorExplanation'

export default {
  components: {
    'ext-error-explanation': ExtensionErrorExplanation
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
      newVersionInfo: null
    }
  },
  computed: {
    lastCommitDate() {
      let isoDate = this.$props.extension.last_commit_time
      return isoDate ? this.isoDateToHumanDate(isoDate) : ''
    },
    canSave() {
      const { preferences } = this.$props.extension
      return !this.$props.extension.error && preferences && !!preferences.length
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
    isoDateToHumanDate(isoDate) {
      let date = new Date(isoDate)
      return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`
    },
    githubProjectPath(githubUrl) {
      return githubUrl.split('.com/')[1]
    },
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
    openGithub() {
      this.openUrl(this.extension.url)
    },
    save() {
      let updates = {
        id: this.extension.id
      }
      for (let i = 0; i < this.extension.preferences.length; i++) {
        let pref = this.extension.preferences[i]
        let value = this.$refs[pref.id][0].$el.value
        if (pref.type === 'keyword') {
          value = value.trim()
        }
        updates[`pref.${pref.id}`] = value
      }
      jsonp('prefs://extension/update-prefs', updates).then(
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
      jsonp('prefs://extension/remove', { id: this.extension.id }).then(
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
      this.newVersionInfo = null
      this.updateState = 'checking-updates'
      jsonp('prefs://extension/check-updates', { id: this.extension.id }).then(
        data => {
          if (data) {
            this.newVersionInfo = data
            this.updateState = 'update-available'
          } else {
            this.updateState = 'no-updates'
          }
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
      jsonp('prefs://extension/update-ext', { id: this.extension.id }).then(
        () => {
          this.updateState = 'updated'
        },
        err => {
          this.updateState = null
          this.updateError = err
        }
      )
    },
    openUrl(url) {
      jsonp('prefs://open/web-url', { url })
    }
  }
}
</script>

<style lang="scss" scoped>
.header-info {
  display: flex;

  .logo {
    flex: 0 0 70px;

    img {
      width: 55px;
    }
  }

  .ext-info {
    flex: 1 0 0;

    .ext-name {
      font-size: 1.3em;
    }
    .developer-name {
      font-style: italic;
      opacity: 0.8;
    }
  }

  .saved-notif {
    flex: 0 0 20px;
    font-size: 20px;
    position: relative;
    right: 0;
    top: 10px;
    opacity: 0.9;
  }

  .menu {
    flex: 0 0 0;
  }
}
.menu-button {
  white-space: nowrap !important;
}
.menu-button a {
  outline: none;
}
.ext-form {
  padding-top: 30px;

  .row {
    display: block;
  }
}
.error-wrapper {
  margin-top: 20px;
}
.ext-config {
  h1 {
    font-size: 1.3em;
  }
  small {
    font-style: italic;
  }
  button {
    margin-right: 10px;
  }
}
</style>
