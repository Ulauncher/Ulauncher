<template>
  <div class="wrapper selectable">
    <b-alert show :variant="alertVariant()">
      <small>
        <p
          v-if="errorName === 'InvalidUrl'"
        >The URL should be a GitHub or Gitea-compatible extension repository link.
        <br>Examples: https://github.com/user/repo or https://codeberg.org/user/repo</p>
        <p
          v-else-if="errorName === 'MissingVersionDeclaration'"
        >This repository does not provide a Ulauncher extension version declaration. It is probably not a Ulauncher extension</p>
        <p v-else-if="errorName === 'InvalidVersionDeclaration'">
          There's an error in versions.json:
          <br>
          <b>{{ errorMessage }}</b>
        </p>
        <p v-else-if="errorName === 'InvalidManifest'">
          There's an error in manifest.json:
          <br>
          <b>{{ errorMessage }}</b>
        </p>
        <div v-else-if="errorName === 'Incompatible'">
          <p>
            Version incompatibility error:
            <br>
            <b>{{ errorMessage }}</b>
          </p>
          <p v-if="extUrl">
            Please make sure that you are running the latest version of Ulauncher app.
            If problem persists, report this issue on the
            <a
              href
              @click.prevent="openUrlInBrowser(`${extUrl}/issues`)"
            >extension issue page</a>.
          </p>
        </div>
        <p
          v-else-if="errorName === 'AlreadyAdded'"
        >You've already installed this extension.</p>
        <p
          v-else-if="errorName === 'Network'"
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
        <p v-if="extUrl && reportableErrors.indexOf(errorName) > -1">
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
import jsonp from '@/api'

export default {
  name: 'ext-error-explanation',
  props: {
    isUpdatable: Boolean,
    errorMessage: String,
    errorName: String,
    extUrl: String
  },
  data: () => ({
    reportableErrors: ['MissingVersionDeclaration', 'Incompatible', 'InvalidVersionDeclaration', 'InvalidManifest']
  }),
  methods: {
    openUrlInBrowser(url) {
      jsonp('prefs:///open/web-url', { url: url })
    },
    openExtensionsDir() {
      jsonp('prefs:///open/extensions-dir')
    },
    alertVariant() {
      if (this.errorName === 'Other') {
        return 'danger'
      }
      return 'warning'
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
