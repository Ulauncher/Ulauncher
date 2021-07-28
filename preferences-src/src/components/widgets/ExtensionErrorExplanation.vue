<template>
  <div class="wrapper selectable">
    <b-alert show :variant="alertVariant()">
      <small>
        <p
          v-if="errorName === 'InvalidGithubUrl'"
        >The URL must look like this: https://github.com/userName/projectName</p>
        <p
          v-else-if="errorName === 'IncompatibleVersion'"
        >The author of this extension does not provide a version compatible with your Ulauncher version.</p>
        <p
          v-else-if="errorName === 'VersionsJsonNotFound'"
        >It looks like this extension is not compatible with the new version of Ulauncher.</p>
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
          <p v-if="extUrl">
            Please make sure that you are running the latest version of Ulauncher app.
            If problem persists, report this issue to the author of the extension via
            <a
              href
              @click.prevent="openUrlInBrowser(`${extUrl}/issues`)"
            >Github issues</a>.
          </p>
        </div>
        <p
          v-else-if="errorName === 'GithubApiError'"
        >It looks like there's an issue with Github API. Please try again later.</p>
        <p
          v-else-if="errorName === 'ExtensionAlreadyAdded'"
        >You've already installed this extension.</p>
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
          the author know about this problem via
          <a
            href
            @click.prevent="openUrlInBrowser(`${extUrl}/issues`)"
          >Github issues</a>.
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
    reportableErrors: ['IncompatibleVersion', 'VersionsJsonNotFound', 'InvalidVersionsJson', 'InvalidManifestJson']
  }),
  methods: {
    openUrlInBrowser(url) {
      jsonp('prefs://open/web-url', { url: url })
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
