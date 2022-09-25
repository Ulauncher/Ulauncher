<template>
  <div class="page" v-if="prefsLoaded">
    <b-media>
      <div
        :class="{'icon-container': true, 'no-icon': !localIcon}"
        slot="aside"
        @click="selectIcon"
      >
        <img v-if="localIcon" :src="expandUserPath(localIcon)" />
      </div>

      <b-form-group label="Name" :state="nameState">
        <b-form-input class="name" v-model="localName"></b-form-input>
      </b-form-group>

      <b-form-group label="Keyword" :state="keywordState">
        <b-form-input class="keyword" v-model="localKeyword"></b-form-input>
      </b-form-group>

      <b-form-group label="Query or Script" :state="cmdState">
        <b-form-textarea class="cmd" :rows="3" v-model="localCmd"></b-form-textarea>
        <small class="form-text text-muted">
          <p>
            Use <code>%s</code> as the placeholder for the query.
            <a
              @click.prevent="cmdDescriptionExpanded = !cmdDescriptionExpanded"
              href
            >(show script example)</a>
          </p>
          <div v-if="cmdDescriptionExpanded">
            <pre class="selectable"><code>#!/bin/bash
# Scripts must start with a shebang string ^
# Run Ulauncher in verbose mode to log the output of the script (for debugging)
# %s is supported for scripts as of Ulauncher v6
# You can also use shell arguments
echo "You wrote: %s"
echo "This also works: $@"</code></pre>
          </div>
        </small>
      </b-form-group>

      <b-form-group>
        <b-form-checkbox v-model="localIsDefaultSearch">Default search</b-form-checkbox>
        <small class="form-text text-muted">
          <p>Suggest this shortcut when no results found</p>
        </small>
      </b-form-group>

      <b-form-group>
        <b-form-checkbox v-model="localRunWithoutArgument">Run without arguments</b-form-checkbox>
        <small class="form-text text-muted">
          <p>Allows you to type in a keyword and press Enter to run a shortcut</p>
        </small>
      </b-form-group>

      <b-button-toolbar>
        <b-button class="save" variant="primary" href @click="save">Save</b-button>
        <b-button class="cancel" variant="secondary" href @click="hide">Cancel</b-button>
      </b-button-toolbar>
    </b-media>
  </div>
</template>


<script>
import fetchData from '@/fetchData'
import bus from '@/event-bus'
import { mapState, mapGetters } from 'vuex'

const shortcutIconEventName = 'shortcut-icon-event'

export default {
  name: 'edit-shortcut',
  props: ['added', 'id', 'icon', 'name', 'keyword', 'cmd', 'is_default_search', 'run_without_argument'],
  created() {
    bus.$on(shortcutIconEventName, this.onIconSelected)
  },
  beforeDestroy() {
    bus.$off(shortcutIconEventName, this.onIconSelected)
  },
  data() {
    return {
      localIcon: this.icon,
      localName: this.name,
      localKeyword: this.keyword,
      localCmd: this.cmd,
      localIsDefaultSearch: !!this.is_default_search,
      localRunWithoutArgument: !!this.run_without_argument,
      validate: false,
      cmdDescriptionExpanded: false
    }
  },
  computed: {
    ...mapState(['prefs']),
    ...mapGetters(['prefsLoaded']),
    nameState() {
      return this.validate && !this.localName ? 'danger' : ''
    },
    keywordState() {
      return this.validate && !this.localKeyword ? 'danger' : ''
    },
    cmdState() {
      return this.validate && !this.localCmd ? 'danger' : ''
    }
  },
  methods: {
    expandUserPath(path) {
      return path.indexOf('~') === 0 ? path.replace('~', this.prefs.env.user_home, 1) : path
    },
    selectIcon() {
      const filter = {'Image files': 'image/*'}
      fetchData('prefs:///show/file-chooser', shortcutIconEventName, filter).then(null, err =>
        bus.$emit('error', err)
      )
    },
    onIconSelected(data) {
      this.localIcon = data.value
    },
    save() {
      this.validate = true
      if (!this.localName || !this.localKeyword || !this.localCmd) {
        return
      }

      const shortcut = {
        added: Number(this.added) || Math.floor(new Date().getTime() / 1000),
        id: this.id || Array(20).fill().map(n=>(Math.random()*36|0).toString(36)).join(''),
        icon: this.localIcon || '',
        name: this.localName,
        keyword: this.localKeyword.trim(),
        cmd: this.localCmd,
        is_default_search: this.localIsDefaultSearch,
        run_without_argument: this.localRunWithoutArgument
      }
      fetchData('prefs:///shortcut/update', shortcut).then(this.hide, err => bus.$emit('error', err))
    },
    hide() {
      this.$router.push({ path: '/shortcuts' })
    }
  }
}
</script>

<style lang="css" scoped>
.page {
  padding: 15px;
}
.row {
  display: block;
}
.name,
.keyword {
  width: 400px;
}
.cmd {
  font-family: monospace;
}
.save,
.cancel {
  margin-right: 20px;
  margin-top: 10px;
  cursor: pointer;
}
fieldset p {
  margin-bottom: 4px;
}
.icon-container {
  cursor: pointer;
  width: 120px;
  height: 100px;
  box-sizing: border-box;
  padding-top: 37px;
  position: relative;
}

.icon-container img {
    display: block;
    width: 100px;
    height: 100px;
    margin-left: 10px;
}

.icon-container:hover:before,
.icon-container.no-icon:before {
    z-index: 1;
    content: '\f093';
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
.icon-container.no-icon:after {
    content: 'Click to select icon';
    font-size: 0.7em;
    display: block;
    position: absolute;
    text-align: center;
    width: 100px;
    left: 10px;
    top: 140px;
}
.icon-container.no-icon.validate:before {
    color: #d9534f;
}
.icon-container.no-icon.validate:after {
    content: 'Please select an icon';
    font-weight: bold;
}
</style>
