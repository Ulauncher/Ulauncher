<template>
  <div class="wrapper selectable">
    <b-alert show variant="warning">
      <small>
        <p
          v-if="errorName === 'InvalidExtensionUrlWarning'"
        >The URL should be a HTTPS git repository link or a path to a local git repository.
        <br>Examples: https://github.com/user/repo.git or https://codeberg.org/user/repo.git</p>
        <p v-else-if="errorName === 'ExtensionManifestError'">
          There's an error in manifest.json:
          <br>
          <b>{{ errorMessage }}</b>
        </p>
        <div v-else-if="errorName === 'ExtensionIncompatibleWarning'">
          <p>
            Version incompatibility error:
            <br>
            <b>{{ errorMessage }}</b>
          </p>
          <p>
            Please make sure that you are running the latest version of Ulauncher app.
          </p>
        </div>
        <p
          v-else-if="errorName === 'ExtensionAlreadyInstalledWarning'"
        >You've already installed this extension.</p>
        <p
          v-else-if="errorName === 'ExtensionNetworkError'"
        >
          A network error occurred: <b>{{ errorMessage }}</b>
          <br><br>Please check that your network is ok, that the repository is not private, and that the extension has all the required files.
          <br><br>You can also install extensions manually by adding them to 
          <a
            href
            @click.prevent="openExtensionsDir()"
          >your extension directory</a>.
        </p>
        <p v-else>
          An unexpected error occurred.
          <br>Please copy the technical details and report this problem via
          <a
            href
            @click.prevent="openUrlInBrowser('https://github.com/Ulauncher/Ulauncher/issues')"
          >Github issues</a>.
        </p>
        <p v-if="extUrl && !errorName.endsWith('Warning')">
          <br />
          <span v-if="isUpdatable">
            Try
            <b>updating</b> the extension. If the doesn't help let
          </span>
          <span v-else>Let</span>
          the author know about this problem on the
          <a
            href
            @click.prevent="openUrlInBrowser(`${extUrl}/issues`)"
          >extension issue page</a>.
        </p>
      </small>
    </b-alert>
  </div>
</template>

<script>
import fetchData from '@/fetchData'

export default {
  name: 'ext-error-explanation',
  props: {
    isUpdatable: Boolean,
    errorMessage: String,
    errorName: String,
    extUrl: String
  },
  methods: {
    openUrlInBrowser(url) {
      fetchData('prefs:///open/web-url', url)
    },
    openExtensionsDir() {
      fetchData('prefs:///open/extensions-dir')
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
