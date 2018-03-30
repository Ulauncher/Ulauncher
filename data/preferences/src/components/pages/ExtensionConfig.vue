<template>
  <div class="ext-config">
    <div class="row">
      <div class="col-6 ext-header selectable">
        <img :src="extension.icon">
        <h1>{{ extension.name }}</h1>
      </div>
      <div class="col-6 pull-right selectable">
        <small v-if="extension.last_commit">
          <i class="fa fa-code-fork"></i> {{ extension.last_commit.substring(0, 7) }}
          &nbsp;&nbsp;&nbsp;
          <i class="fa fa-calendar"></i> {{ lastCommitDate }}
        </small>
      </div>
    </div>

    <div class="row">
      <div class="col-6 selectable">
        <small>by {{ extension.developer_name }}</small>
      </div>
      <div class="col-6 pull-right">
        <small v-if="extension.url">
          <i class="fa fa-github"></i>
          <a @click.prevent="onLinkClick" :href="extension.url"> {{ githubProjectPath(extension.url) }}</a>
        </small>
      </div>
    </div>

    <div class="ext-form">
      <template v-for="pref in extension.preferences">
        <b-form-fieldset
          v-if="pref.type == 'keyword'"
          :label="`${pref.name} Keyword`"
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

      <hr>

      <b-button-toolbar>
        <div v-if="buttonRowState == 'remove'">
          Are you sure? &nbsp;
          <b-button variant="danger" href="" @click="remove">Yes</b-button>
          <b-button variant="secondary" href="" @click="showActionButtons">No</b-button>
        </div>

        <div v-else-if="buttonRowState == 'update'">
          <div v-if="updateState == 'checking-updates'">
            <i class="fa fa-spinner fa-spin"></i> Checking for updates...
          </div>
          <div v-if="updateState == 'update-available'">
            <p>
              New version is available:
              &nbsp;&nbsp;&nbsp;
              <i class="fa fa-code-fork"></i> {{ newVersionInfo.last_commit.substring(0, 7) }}
              &nbsp;&nbsp;&nbsp;
              <i class="fa fa-calendar"></i> {{ isoDateToHumanDate(newVersionInfo.last_commit_time) }}
            </p>

            <b-button variant="primary" href="" @click="update">Update</b-button>
            <b-button variant="secondary" href="" @click="showActionButtons">Cancel</b-button>
          </div>
          <div v-if="updateState == 'no-updates'">
            <p>
              No new updates are available
            </p>
            <b-button variant="secondary" href="" @click="showActionButtons">OK</b-button>
          </div>
          <div v-if="updateState == 'updating'">
            <i class="fa fa-spinner fa-spin"></i> Updating...
          </div>
          <div v-if="updateState == 'updated'">
            <p>
              <i class="fa fa-check-circle"></i> Updated
            </p>
            <b-button variant="secondary" href="" @click="showActionButtons">OK</b-button>
          </div>
        </div>

        <div v-else>
          <b-button class="save" v-if="extension.preferences.length" variant="primary" href="" @click="save">Save</b-button>
          <b-button class="remove" variant="secondary" href="" @click="askRemoveConfirmation">Remove</b-button>
          <b-button variant="secondary" href="" @click="checkUpdates">Check Updates</b-button>
        </div>

        <div class="saved-msg" v-if="showSavedMsg">
          <i class="fa fa-check-circle"></i> Saved
        </div>
      </b-button-toolbar>

    </div>
  </div>
</template>

<script>
import jsonp from '@/api'
import bus from '@/event-bus'

export default {
  name: 'extension-config',
  props: ['extension'],
  data () {
    return {
      showSavedMsg: false,
      buttonRowState: 'actions', // actions | remove | update
      updateState: 'checking-updates', // checking-updates | update-available | no-updates | updating | updated
      newVersionInfo: null
    }
  },
  computed: {
    lastCommitDate () {
      let isoDate = this.$props.extension.last_commit_time
      return isoDate ? this.isoDateToHumanDate(isoDate) : ''
    }
  },
  methods: {
    isoDateToHumanDate (isoDate) {
      let date = new Date(isoDate)
      return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`
    },
    githubProjectPath (githubUrl) {
      return githubUrl.split('.com/')[1]
    },
    save () {
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
      jsonp('prefs://extension/update-prefs', updates).then(() => {
        this.showSavedMsg = true
        setTimeout(() => {
          this.showSavedMsg = false
        }, 1e3)
      }, (err) => bus.$emit('error', err))
    },
    askRemoveConfirmation () {
      this.buttonRowState = 'remove'
    },
    showActionButtons () {
      this.buttonRowState = 'actions'
    },
    remove () {
      jsonp('prefs://extension/remove', {id: this.extension.id}).then(() => {
        this.$emit('removed', this.extension.id)
        this.showActionButtons()
      }, (err) => {
        bus.$emit('error', err)
        this.showActionButtons()
      })
    },
    checkUpdates () {
      this.newVersionInfo = null
      this.buttonRowState = 'update'
      this.updateState = 'checking-updates'
      jsonp('prefs://extension/check-updates', {id: this.extension.id}).then((data) => {
        if (data) {
          this.newVersionInfo = data
          this.updateState = 'update-available'
        } else {
          this.updateState = 'no-updates'
        }
      }, (err) => {
        bus.$emit('error', err)
        this.showActionButtons()
      })
    },
    update () {
      this.updateState = 'updating'
      jsonp('prefs://extension/update-ext', {id: this.extension.id}).then(() => {
        this.updateState = 'updated'
      }, (err) => {
        bus.$emit('error', err)
        this.showActionButtons()
      })
    },
    onLinkClick (el) {
      let url = el.target.href
      jsonp('prefs://open/web-url', {url: url})
    }
  }
}
</script>

<style lang="scss" scoped>
.pull-right { text-align: right }
.ext-header {
  $iconSize: 30px;
  position: relative;
  min-height: $iconSize + 5px;

  img {
    width: $iconSize;
    height: $iconSize;
    position: absolute;
    left: 15px;
    top: 0;
  }
  h1 {
    display: inline-block;
    margin-bottom: 5px;
    padding-left: $iconSize + 10px;
  }
}
.ext-form {
  padding-top: 30px;

  .row { display: block; }
}
.saved-msg {
  line-height: 37px;
  opacity: .9;
}
.ext-config {
  h1 {
    font-size: 1.3em;
  }
  small {
    font-style: italic
  }
  button {
    margin-right: 10px;
  }
}
</style>
