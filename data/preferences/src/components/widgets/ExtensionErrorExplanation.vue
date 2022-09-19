<template>
  <div class="wrapper selectable">
    <b-alert show :variant="alertVariant()">
      <small>
        <p
          v-if="errorName === 'InvalidGithubUrl'"
        >The URL must look like this: https://github.com/userName/projectName</p>
        <p
          v-else-if="errorName === 'IncompatibleVersion'"
        >This URL is either not an extension or not compatible with your Ulauncher version.</p>
        <p v-else-if="errorName === 'InvalidVersionsJson'">
          There's an error in versions.json:
          <br>
          <b>{{ errorMessage }}</b>
        </p>
        <p v-else-if="errorName === 'InvalidManifestJson'">
          There's an error in manifest.json:
          <br>
          <b>{{ errorMessage }}</b>
        </p>
        <div v-else-if="errorName === 'ExtensionCompatibilityError'">
          <p>
            Version incompatibility error:
            <br>
            <b>{{ errorMessage }}</b>
          </p>
        </div>
        <p
          v-else-if="errorName === 'GithubApiError'"
        >Unable to connect to Github. Please try again later, or install the extension manually.</p>
        <p
          v-else-if="errorName === 'ExtensionAlreadyAdded'"
        >You've already installed this extension.</p>
        <p v-else>An unexpected error occurred.</p>
        <p v-if="extUrl && ['ExtensionCompatibilityError', 'InvalidVersionsJson', 'InvalidManifestJson'].indexOf(errorName) !== -1">
          <span v-if="isUpdatable">
            Try
            <b>updating</b> the extension. If it doesn't help let
          </span>
          <span v-else>Let</span>
          the author know about this problem via
          <a
            href
            @click.prevent="openUrlInBrowser(`${extUrl}/issues`)"
          >Github issues</a>.
        </p>
        <p v-else-if="['InvalidGithubUrl', 'IncompatibleVersion', 'ExtensionAlreadyAdded'].indexOf(errorName) === -1">
          To install extensions you need a working internet connection that can access GitHub's APIs.<br/>
          If you don't have this, or if it doesn't work for other reasons, then you can install extensons manually by putting them in
          <a href @click.prevent="openExtensionsDir()">your extensions directory</a>.
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
  methods: {
    openUrlInBrowser(url) {
      jsonp('prefs://open/web-url', { url: url })
    },
    openExtensionsDir() {
      jsonp('prefs://open/extensions-dir', {})
    },
    alertVariant() {
      if (this.errorName === 'UnexpectedError') {
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
