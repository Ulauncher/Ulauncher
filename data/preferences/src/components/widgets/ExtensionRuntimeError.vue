<template>
  <div class="wrapper selectable">
    <b-alert show variant="warning">
      <small>
        <p v-if="errorName === 'NoExtensionsFlag'">
          You ran ulauncher with
          <code>--no-extensions</code> flag.
          You have to manually start this extension by running
          <br>
          <code>{{ errorMessage }}</code>
        </p>
        <p
          v-else-if="errorName === 'Terminated'"
        >The extension was terminated. Please check the logs</p>
        <p
          v-else-if="errorName === 'ExitedInstantly'"
        >The extension exited instantly. Please check the logs.</p>
        <p v-else>{{ errorMessage }}</p>
        <p v-if="extUrl && errorName !== 'NoExtensionsFlag'">
          You can let the author know about this problem by creating a
          <a
            href
            @click.prevent="openUrlInBrowser(`${extUrl}/issues`)"
          >Github issue</a>.
        </p>
      </small>
    </b-alert>
  </div>
</template>

<script>
import jsonp from '@/api'

export default {
  name: 'ext-runtime-error',
  props: {
    errorMessage: String,
    errorName: String,
    extUrl: String
  },
  methods: {
    openUrlInBrowser(url) {
      jsonp('prefs://open/web-url', { url: url })
    }
  }
}
</script>

<style lang="scss" scoped>
.wrapper {
  margin-bottom: 5px;
}
p:last-of-type {
  margin-bottom: 0;
}
</style>
