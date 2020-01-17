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

<style lang="scss" scoped>
$headerHeight: 60px;
$underlineHeight: 4px;
$darkBlue: #006890;
$veryLightGrey: #c8c8c8;

.stripe {
  background: #4B71A5 url('../assets/stripe.png') no-repeat;
  height: 9px;
}

.main-header {
  box-sizing: border-box;
  height: $headerHeight;
  padding: 0 15px 0 25px;
  border-bottom: 1px solid $veryLightGrey;
  background: #e4e4e4;
  font-size: 0.95em;
  letter-spacing: 0.04px;
  position: relative;

  .close-btn {
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

  &:hover {
    color: #4675ab;
    text-decoration: none !important;
  }

  &.router-link-exact-active {
    color: $darkBlue;

    &:after {
      content: '';
      position: absolute;
      top: $headerHeight - $underlineHeight;
      left: 0;
      display: inline-block;
      height: $underlineHeight;
      width: 100%;
      background: $darkBlue;
    }
  }
}

i {
  padding: 5px;
  font-size: 15px;
}
</style>
