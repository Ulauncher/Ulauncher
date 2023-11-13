<template>
  <div class="wrapper selectable">
    <b-alert show variant="warning">
      <small>
        <p
          v-if="errorName === 'Terminated'"
        >The extension crashed. Ensure that you read and followed the instructions on the extension <a href @click.prevent="openUrlInBrowser(`${extUrl}`)">Github</a> page, and check the error log and report the error otherwise.</p>
        <p
          v-else-if="errorName === 'Incompatible'"
        >The extension is not compatible with this version of Ulauncher. Please report this issue to the extension developer, and attach the logs for details.</p>
        <p v-else-if="errorName === 'MissingModule'">
          The extension crashed because it could not import module
          <code>{{ errorMessage }}</code>.
          <br />Try installing this module manually:
          <code>pip3 install {{ errorMessage }} --user</code> and then restart Ulauncher.
          <br />If that doesn't help, report the issue on
          <a href @click.prevent="openUrlInBrowser(`${extUrl}/issues`)">extension issue tracker</a>.
        </p>
        <p v-else>{{ errorMessage }}</p>
        <p v-if="extUrl && errorName !== 'MissingModule'">
          You can let the author know about this problem by creating an
          <a
            href
            @click.prevent="openUrlInBrowser(`${extUrl}/issues`)"
          >issue</a>.
        </p>
      </small>
    </b-alert>
  </div>
</template>

<script>
import fetchData from '@/fetchData'

export default {
  name: 'ext-runtime-error',
  props: {
    errorMessage: String,
    errorName: String,
    extUrl: String
  },
  methods: {
    openUrlInBrowser(url) {
      fetchData('prefs:///open/web-url', url)
    }
  }
}
</script>

<style lang="css" scoped>
.wrapper {
  margin-bottom: 5px;
}
p:last-of-type {
  margin-bottom: 0;
}
</style>
