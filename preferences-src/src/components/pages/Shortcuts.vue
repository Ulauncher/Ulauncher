<template>
  <div class="page" v-if="prefsLoaded">

    <b-table striped small hover show-empty :items="items" :fields="fields">
      <template slot="cell(name)" slot-scope="item">
        <div class="limited-width">{{ item.value }}</div>
      </template>
      <template slot="cell(keyword)" slot-scope="item">
        <div class="limited-width">{{ item.value }}</div>
      </template>
      <template slot="cell(icon)" slot-scope="item">
        <img class="icon" :src="item.value ? expandUserPath(item.value) : defaultIcon" />
      </template>
      <template slot="cell(cmd)" slot-scope="item">
        <div class="cmd">
          <div class="text-wrapper">
            <div class="text">{{ item.value }}</div>
          </div>
          <div class="actions">
            <b-btn size="sm" @click="edit(item.item)"><i class="fa fa-pencil"></i></b-btn>
            <b-btn size="sm" @click="remove(item.item)"><i class="fa fa-trash"></i></b-btn>
          </div>
        </div>
      </template>
      <template slot="empty">
        <td class="empty-text" colspan="4">There are no shortcuts</td>
      </template>
    </b-table>

    <a class="add-link" href="" @click.prevent="add">
      <i class="fa fa-plus"></i> Add shortcut
    </a>
  </div>
</template>

<script>
import fetchData from '@/fetchData'
import bus from '@/event-bus'
import { mapState, mapGetters } from 'vuex'
import defaultIcon from '../../assets/executable-icon.png'

export default {
  name: 'shortcuts',
  created () {
    this.fetchData()
  },
  data () {
    return {
      items: [],
      defaultIcon: defaultIcon,
      fields: [
        {key: 'icon', label: ''},
        {key: 'name', label: 'Name'},
        {key: 'keyword', label: 'Keyword'},
        {key: 'cmd', label: 'Query or Script'}
      ]
    }
  },
  computed: {
    ...mapState(['prefs']),
    ...mapGetters(['prefsLoaded'])
  },
  methods: {
    fetchData () {
      fetchData('prefs:///shortcut/get-all').then((data) => {
        this.items = data
      })
    },
    expandUserPath (path) {
      return path.indexOf('~') === 0 ? path.replace('~', this.prefs.env.user_home, 1) : path
    },
    edit (item) {
      // Workaround because otherwise Vue converts bools to strings "true" or "false",
      // then evaluate both to "true" on the other side.
      item.is_default_search = item.is_default_search ? true : undefined;
      item.run_without_argument = item.run_without_argument ? true : undefined;
      this.$router.push({path: 'edit-shortcut', query: item, params: item})
    },
    remove (item) {
      fetchData('prefs:///shortcut/remove', item.id).then(() => {
        this.items = this.items.filter((i) => item.id === i.id ? null : i)
      }, (err) => bus.$emit('error', err))
    },
    add () {
      this.$router.push({name: 'edit-shortcut'})
    }
  }
}
</script>

<style lang="css" scoped>
.page { padding: 15px; }
button { cursor: pointer }
.empty-text { text-align: center }
.icon { width: 20px; height: 20px }
.add-link {
  color: #555;
  font-style: italic;
  display: inline-block;
  padding-left: 8px;
}
.add-link i {
    margin-right: 5px;
    display: inline-block;
}

.add-link:hover {
    color: #015aa7;
    text-decoration: underline;
}
.limited-width {
  white-space: nowrap;
  max-width: 150px;
  min-width: 100px;
  text-overflow: ellipsis;
  overflow: hidden;
}
.cmd {
  position: relative;
}
.cmd .text-wrapper {
    display: table;
    table-layout: fixed;
    width:100%;
}

.cmd .text-wrapper .text {
      display: table-cell;
      text-overflow: ellipsis;
      overflow: hidden;
      white-space: nowrap;
      font-family: monospace;
}

.cmd .actions {
    position: absolute;
    display: none;
    top: -4px;
    right: 0;
}
tr:hover .actions {
  display: block;
}
</style>
