<template>
  <div>
    <div class="main-header">
      <ul>
        <li><router-link to="/preferences"><i class="fa fa-cog"></i> Preferences</router-link></li>
        <li><router-link to="/shortcuts"><i class="fa fa-external-link-square"></i>Shortcuts</router-link></li>
        <li><router-link to="/extensions"><i class="fa fa-cubes"></i>Extensions</router-link></li>
        <li><router-link to="/help"><i class="fa fa-support"></i>Help</router-link></li>
        <li><router-link to="/about"><i class="fa fa-info-circle"></i>About</router-link></li>
      </ul>
    </div>
  </div>
</template>

<script>

export default {
  name: 'navbar',
}
</script>
<style lang="css" scoped>
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
  padding: 15px 10px 20px 5px;
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
