<template>
  <div class="ext-config">
    <div class="row">
      <div class="col-6 ext-header selectable">
        <img :src="extension.icon">
        <h1>{{ extension.name }}</h1>
      </div>
      <div class="col-6 pull-right">
        <small>{{ extension.version }}</small>
      </div>
    </div>

    <div class="row">
      <div class="col-6 selectable">
        <small>by {{ extension.developer_name }}</small>
      </div>
      <div class="col-6 pull-right">
        <small>
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
          >
          <b-form-input :ref="pref.id" :value="pref.value"></b-form-input>
        </b-form-fieldset>

        <b-form-fieldset
          v-if="pref.type == 'input'"
          :label="pref.name"
          >
          <b-form-input :ref="pref.id" :value="pref.value"></b-form-input>
        </b-form-fieldset>

        <b-form-fieldset
          v-if="pref.type == 'text'"
          :label="pref.name"
          >
          <b-form-input textarea :ref="pref.id" :value="pref.value" :rows="3"></b-form-input>
        </b-form-fieldset>
      </template>

      <hr>

      <b-button-toolbar>
        <b-button class="save" v-if="extension.preferences.length" variant="primary" href="" @click="save">Save</b-button>
        <b-button class="remove" variant="secondary" href="" @click="remove">Remove</b-button>
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
      showSavedMsg: false
    }
  },
  methods: {
    githubProjectPath (githubUrl) {
      return githubUrl.split('.com/')[1]
    },
    save () {
      let prefs = {}
      for (let i = 0; i < this.extension.preferences.length; i++) {
        let pref = this.extension.preferences[i]
        prefs[pref.id] = this.$refs[pref.id][0].$el.value
      }
      let updates = {
        url: this.extension.url,
        preferences: prefs
      }
      jsonp('prefs://extension/update', updates).then(() => {
        this.showSavedMsg = true
        setTimeout(() => {
          this.showSavedMsg = false
        }, 1e3)
      }, (err) => bus.$emit('error', err))
    },
    remove () {
      jsonp('prefs://extension/remove', {url: this.extension.url}).then(() => {
        this.$emit('removed', this.extension.url)
      }, (err) => bus.$emit('error', err))
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

  img {
    width: $iconSize;
    height: $iconSize;
    margin-right: 10px;
  }
  img, h1 {
    display: inline-block;
    margin-bottom: 5px
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
  .keyword-input {
    width: 300px;
  }
}
</style>
