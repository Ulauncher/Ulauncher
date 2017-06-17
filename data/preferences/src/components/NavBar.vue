<template>
  <div class="main-header">
    <ul>
      <li><router-link to="/general"><i class="fa fa-cog"></i> General</router-link></li>
      <li><router-link to="/shortcuts"><i class="fa fa-external-link-square"></i>Shortcuts</router-link></li>
      <li><router-link to="/help"><i class="fa fa-support"></i>Help</router-link></li>
      <li><router-link to="/about"><i class="fa fa-info-circle"></i>About</router-link></li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'navbar'
}
</script>

<style lang="scss" scoped>
$headerHeight: 60px;
$underlineHeight: 4px;
$darkBlue: #015aa7;
$veryLightGrey: #c8c8c8;

.main-header {
  box-sizing: border-box;
  height: $headerHeight;
  padding: 0 15px 0 25px;
  border-bottom: 1px solid $veryLightGrey;
  background: #e4e4e4;
  font-size: 0.95em;
  letter-spacing: 0.04px;
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
  padding: 20px 25px 20px 0;
  cursor: pointer;
  text-decoration: none !important;
  color: #6b6b6b;
  text-transform: uppercase;

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
      left: -1.5px;
      display: inline-block;
      height: $underlineHeight;
      width: 82%;
      background: $darkBlue;
    }
  }
}

i {
  padding: 5px;
  font-size: 15px;
}
</style>
