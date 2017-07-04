<template>
  <div class="page row">

    <div class="left-nav col-4">

      <ul class="ext-list">
        <li><i style="background-image: url('https://assets-cdn.github.com/favicon.ico')"></i> <span>Timer Extension</span></li>
        <li class="active"><i style="background-image: url('https://assets-cdn.github.com/favicon.ico')"></i> <span>Timer Extension</span></li>
        <li><i style="background-image: url('https://assets-cdn.github.com/favicon.ico')"></i> <span>Timer Extension Timer Extension</span></li>
        <li><i style="background-image: url('https://assets-cdn.github.com/favicon.ico')"></i> <span>Timer Extension</span></li>
        <li><i style="background-image: url('https://assets-cdn.github.com/favicon.ico')"></i> <span>Timer Extension</span></li>
        <li><i style="background-image: url('https://assets-cdn.github.com/favicon.ico')"></i> <span>Timer Extension</span></li>
        <li><i style="background-image: url('https://assets-cdn.github.com/favicon.ico')"></i> <span>Timer Extension</span></li>
        <li><i style="background-image: url('https://assets-cdn.github.com/favicon.ico')"></i> <span>Timer Extension</span></li>
        <li class="add-link" @click="addExtDialog"><i class="fa fa-plus"></i> <span>Add extension</span></li>
      </ul>

      <b-modal
        ref="addExtForm"
        ok-title="Add"
        close-title="Cancel"
        hide-header-close
        no-auto-focus
        @shown="focusGithubUrlInput">
          <template slot="modal-title">
            Enter extension URL
          </template>

          <b-form-input
            class="github-url-input"
            ref="githubUrl"
            type="text"
            placeholder="https://github.com/..."></b-form-input>
      </b-modal>

    </div>

    <div class="col-8 ext-view">

      <div class="row">
        <div class="col-6">
          <h1>Timer Extension</h1>
        </div>
        <div class="col-6 pull-right">
          <small>v1.2.4 - <a href="#">update to v2.0.1</a></small>
        </div>
      </div>


      <div class="row">
        <div class="col-6">
          <small>by Aleksandr Gornostal</small>
        </div>
        <div class="col-6 pull-right">
          <small><i class="fa fa-github"></i> <a href="https://github.com/ulauncher/ulauncher-timer">ulauncher/ulauncher-timer</a></small>
        </div>
      </div>


      <div class="ext-form">
        <b-form-fieldset
          label="Name"
          >
          <b-form-input class="name" ></b-form-input>
        </b-form-fieldset>

        <b-form-fieldset
          label="Keyword"
          >
          <b-form-input class="keyword" ></b-form-input>
        </b-form-fieldset>

        <b-form-fieldset
          label="Query or Script"
          >
          <b-form-input class="cmd" textarea :rows="3"></b-form-input>
        </b-form-fieldset>

        <b-form-checkbox>
          Default search (suggest this shortcut when no results found)
        </b-form-checkbox>

        <hr>

        <b-button-toolbar>
          <b-button class="save" variant="primary" href="" @click="save">Save</b-button>
          <b-button class="remove" variant="secondary" href="" @click="remove">Remove</b-button>
        </b-button-toolbar>

      </div>

    </div>
  </div>
</template>

<script>
import jsonp from '@/api'

export default {
  name: 'extensions',
  created () {
    this.fetchData()
  },
  data () {
    return {
      items: []
    }
  },
  methods: {
    fetchData () {
      jsonp('prefs://shortcut/get-all').then((data) => {
        this.items = data
      })
    },
    focusGithubUrlInput () {
      this.$refs.githubUrl.focus()
    },
    addExtDialog () {
      this.$refs.addExtForm.show()
    },
    save () {

    },
    remove () {

    }
  }
}
</script>

<style lang="scss" scoped>
$darkBlue: #015aa7;
$veryLightGrey: #c8c8c8;

.pull-right { text-align: right }
.ext-form {
  padding-top: 30px;

  .row { display: block; }
}
.page {
  padding: 15px;
  padding-left: 25px;
}
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
.ext-view {
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
