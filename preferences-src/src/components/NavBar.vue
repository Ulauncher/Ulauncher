<template>
  <div>
    <div class="stripe"></div>
    <div class="main-header">
      <ul>
        <li><router-link to="/preferences"><i class="fa fa-cog"></i> Preferences</router-link></li>
        <li><router-link to="/shortcuts"><i class="fa fa-external-link-square"></i>Shortcuts</router-link></li>
        <li><router-link to="/extensions"><i class="fa fa-cubes"></i>Extensions</router-link></li>
        <li><router-link to="/help"><i class="fa fa-support"></i>Help</router-link></li>
        <li><router-link to="/about"><i class="fa fa-info-circle"></i>About</router-link></li>
      </ul>
      <div class="close-btn" @click="closeWindow"></div>
    </div>
  </div>
</template>

<script>
import jsonp from '@/api'
import bus from '@/event-bus'

export default {
  name: 'navbar',
  methods: {
    closeWindow () {
      jsonp('prefs://close').then(null, (err) => bus.$emit('error', err))
    }
  }
}
</script>

<style lang="css" scoped>
:root {
  --header-height: 60px;
  --underline-height: 4px;
  --dark-blue: #006890;
  --very-light-grey: #c8c8c8;
}

.stripe {
  background: #4B71A5 url('../assets/stripe.png') no-repeat;
  height: 9px;
}

.main-header {
  box-sizing: border-box;
  height: var(--header-height);
  padding: 0 15px 0 25px;
  border-bottom: 1px solid var(--very-light-grey);
  background: #e4e4e4;
  font-size: 0.95em;
  letter-spacing: 0.04px;
  position: relative;
}

.main-header .close-btn {
    position: absolute;
    top: 11px;
    right: 14px;
    cursor: pointer;
    width: 38px;
    height: 38px;
    background: url('../assets/close-sign.png') no-repeat;
    background-size: 38px 38px;
    opacity: 0.35;
}

ul, li {
  margin: 0;
  padding: 0;
  list-style: none;
  display: block;
}
li {
  display: inline-block;
}
a {
  outline: 0 !important;

  position: relative;
  display: inline-block;
  height: 100%;
  padding: 20px 10px 20px 5px;
  cursor: pointer;
  text-decoration: none !important;
  color: #6b6b6b;
  text-transform: uppercase;
  margin-right: 15px;
}

a:hover {
    color: #4675ab;
    text-decoration: none !important;
}

a.router-link-exact-active {
    color: var(--dark-blue);
}

a.router-link-exact-active:after {
      content: '';
      position: absolute;
      top: calc(var(--header-height) - var(--underline-height));
      left: 0;
      display: inline-block;
      height: var(--underline-height);
      width: 100%;
      background: var(--dark-blue);
}

i {
  padding: 5px;
  font-size: 15px;
}
</style>
