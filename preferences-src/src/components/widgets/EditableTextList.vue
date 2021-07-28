<template>
  <ul :style="{width: width}">
    <li v-for="(item, index) in items" class="item">
      <b-form-input
        size="sm"
        :readonly="true"
        :value="item"></b-form-input>
      <i class="delete fa fa-remove" @click="remove(item)"></i>
    </li>
    <li class="new-item">
      <b-form @submit.native.prevent="onSubmit">
        <b-form-input
          ref="newItem"
          :placeholder="newItemPlaceholder"
          size="sm"></b-form-input>
      </b-form>
    </li>
  </ul>
</template>

<script>

export default {
  name: 'editable-text-list',
  props: {
    value: {
      type: Array,
      default: []
    },
    width: String,
    newItemPlaceholder: {
      type: String,
      default: 'Add new...'
    }
  },
  data () {
    return {
      dataItems: null
    }
  },
  computed: {
    items () {
      return this.dataItems !== null ? this.dataItems : this.value
    }
  },
  methods: {
    remove (value) {
      this.dataItems = this.items.filter((item) => value !== item)
      this.$emit('input', this.dataItems)
    },
    onSubmit () {
      let value = this.$refs.newItem.$el.value
      if (!value) {
        return
      }

      if (!this.dataItems) {
        this.dataItems = [...this.value]
      }

      this.dataItems.push(value)
      this.$emit('input', this.dataItems)
      this.$refs.newItem.$el.value = ''
    }
  }
}
</script>

<style lang="css" scoped>
ul, li {
  margin: 0;
  padding: 0;
  list-style: none;
  display: block;
  box-sizing: border-box;
}
li {
  display: block;
  margin-bottom: 5px;
  position: relative;
  padding-right: 20px;
}
li i {
    position: absolute;
    top: 4px;
    right: 0;
    cursor: pointer;
}
.delete {
  color: #888;
}
</style>
