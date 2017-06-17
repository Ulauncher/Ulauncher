<template>
  <div class="edit-shortcut-page">
    <b-media>
      <div :class="{'icon-container': true, 'no-icon': !localIcon, validate}" slot="aside" @click="selectIcon">
        <img v-if="localIcon" :src="localIcon">
      </div>

      <b-form-fieldset
        label="Name"
        :state="nameState"
        >
        <b-form-input class="name" v-model="localName"></b-form-input>
      </b-form-fieldset>

      <b-form-fieldset
        label="Keyword"
        :state="keywordState"
        >
        <b-form-input class="keyword" v-model="localKeyword"></b-form-input>
      </b-form-fieldset>

      <b-form-fieldset
        label="Query or Script"
        :state="cmdState"
        >
        <b-form-input class="cmd" textarea :placeholder="cmdPlaceholder" :rows="7" v-model="localCmd"></b-form-input>
      </b-form-fieldset>

      <b-button-toolbar>
        <b-button class="save" variant="primary" href="" @click="save">Save</b-button>
        <b-button class="cancel" variant="secondary" href="" @click="hide">Cancel</b-button>
      </b-button-toolbar>
    </b-media>

  </div>
</template>


<script>
import jsonp from '@/api'
import bus from '@/event-bus'

const shortcutIconEventName = 'shortcut-icon-event'

export default {
  name: 'edit-shortcut',
  props: ['id', 'icon', 'name', 'keyword', 'cmd'],
  created () {
    bus.$on(shortcutIconEventName, this.onIconSelected)
  },
  beforeDestroy () {
    bus.$off(shortcutIconEventName, this.onIconSelected)
  },
  data () {
    return {
      localIcon: this.icon,
      localName: this.name,
      localKeyword: this.keyword,
      localCmd: this.cmd,
      validate: false,
      cmdPlaceholder: `Use %s as a placeholder for a user query in URL.

Or write a script in a language of your choise.
In this case query will be passed as a first arg. Example:

#!/usr/bin/env node
console.log("Query is:", process.argv[1]);`
    }
  },
  computed: {
    nameState () {
      return this.validate && !this.localName ? 'danger' : ''
    },
    keywordState () {
      return this.validate && !this.localKeyword ? 'danger' : ''
    },
    cmdState () {
      return this.validate && !this.localCmd ? 'danger' : ''
    }
  },
  methods: {
    selectIcon () {
      jsonp('prefs://show/file-browser', {type: 'image', name: shortcutIconEventName}).then(null, (error) => {
        console.error(error)
      })
    },
    onIconSelected (data) {
      this.localIcon = data.value
    },
    save () {
      this.validate = true
      if (!this.localName || !this.localKeyword || !this.localCmd || !this.localIcon) {
        return
      }

      let shortcut = {
        id: this.id,
        icon: this.localIcon,
        name: this.localName,
        keyword: this.localKeyword,
        cmd: this.localCmd
      }
      let method = shortcut.id ? 'update' : 'add'
      jsonp(`/shortcut/${method}`, shortcut).then(this.hide, (error) => {
        console.error(error)
      })
    },
    hide () {
      this.$router.push({path: '/shortcuts'})
    }
  }
}
</script>

<style lang="scss" scoped>
.edit-shortcut-page { padding: 15px }
.name, .keyword { width: 400px }
.save, .cancel {
  margin-right: 20px;
  margin-top: 40px;
  cursor: pointer
}
.icon-container {
  cursor: pointer;
  width: 120px;
  height: 100px;
  box-sizing: border-box;
  padding-top: 37px;
  position: relative;

  img {
    display: block;
    width: 100px;
    height: 100px;
    margin-left: 10px;
  }

  &:hover:before,
  &.no-icon:before {
    z-index: 1;
    content: "\f093";
    font: 64px FontAwesome;
    display: block;
    position: absolute;
    left: 10px;
    top: 36px;
    width: 100px;
    height: 100px;
    border: 1px solid #555;
    color: #555;
    text-align: center;
    line-height: 100px;
  }
  &.no-icon:after {
    content: "Click to select icon";
    font-size: 0.7em;
    display: block;
    position: absolute;
    text-align: center;
    width: 100px;
    left: 10px;
    top: 140px;
  }
  &.no-icon.validate:before {
    color: #d9534f;
  }
}
</style>
