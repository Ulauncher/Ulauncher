<template>
  <div class="about-container row" v-if="prefsLoaded">
    <div class="col-4">
      <div class="logo">
        <svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
             width="48px" height="48px" viewBox="0 0 48 48" enable-background="new 0 0 48 48" xml:space="preserve">
        <g>
            <g>
                <g id="MPATH5">
                    <path fill="#599CCD" d="M32.453,24.713V6.501l10.854-4.634v23.595c0,2.846-10.854,3.176-10.854-0.754V24.713z"/>
                </g>
            </g>
            <g>
                <g id="MPATH6">
                    <path fill="#7EC183" d="M23.319,45.268c-3.396,0-6.335-0.479-8.806-1.434c-2.471-0.955-3.17-2.752-4.711-4.397
                        c-0.827-0.878,6.884,0.514,12.022-0.616c4.932-1.027,7.311-4.429,8.132-5.239c1.665-1.64,2.491-4.424,2.491-8.354V8.408
                        c4.476,1.746,10.126,7.706,10.855,14.179v3.391c0,2.845-0.395,5.456-1.186,7.829s-2.005,4.413-3.633,6.108
                        c-1.635,1.701-3.704,3.016-6.222,3.945c-2.517,0.936-5.496,1.396-8.949,1.396L23.319,45.268z"/>
                </g>
            </g>
            <g>
                <g id="MPATH7">
                    <path fill="#4675AB" d="M29.529,34.608c-1.026,1.952-5.753,7.81-14.795,8.733l-1.305,0.034c-1.988-0.908-3.668-2.079-5.03-3.522
                        c-1.608-1.7-2.795-3.725-3.56-6.078c-0.771-2.353-1.156-4.953-1.156-7.793v-6.612l10.855-4.824v10.686
                        c0,1.968,0.221,3.643,0.668,5.021c0.441,1.381,1.053,2.5,1.829,3.368c0.776,0.87,1.711,1.49,2.81,1.86
                        c1.1,0.375,2.307,0.561,3.617,0.561c2.667,0,4.834-0.823,6.5-2.461l-0.428,1.027H29.529z"/>
                </g>
            </g>
        </g>
        </svg>
      </div>
      <p class="logo-label">Ulauncher v{{ this.prefs.env.version }}</p>
      <p class="api-version">Extension API v{{ this.prefs.env.api_version }}</p>
    </div>
    <div class="col-8">
      <section class="text-container copyright-text" v-if="!isCreditsShown">
        <div class="selectable">
          <p>Copyright (C) Aleksandr Gornostal &lt;ulauncher.app@gmail.com&gt;</p>
          <p>Ulauncher is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License version 3, as published by the Free Software Foundation.</p>
          <p>This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY. See the GNU General Public License for more details.</p>
        </div>

        <a href="#" class="toggle" @click.prevent="toggleCredits">Credits</a>
      </section>

      <section class="text-container credits-text" v-if="isCreditsShown">
        <div class="selectable">
          <h2>Maintainers:</h2>
          <p>
            <ul>
              <li>@friday &lt;github.com/friday&gt;</li>
              <li>@troycurtisjr &lt;github.com/troycurtisjr&gt;</li>
              <li>Aleksandr Gornostal &lt;ulauncher.app@gmail.com&gt; </li>
            </ul>
          </p>

          <h2>Contributors:</h2>
          <p>
            <ul>
              <li>Igor Yatsenko &lt;yatsenko.igor@gmail.com&gt;</li>
              <li>Eugene Chulkov &lt;genechulkov@gmail.com&gt;</li>
            </ul>
          </p>
        </div>

        <a href="#" class="toggle" @click.prevent="toggleCredits">Copyright</a>
      </section>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex'

export default {
  name: 'about',
  data () {
    return {
      isCreditsShown: false
    }
  },
  computed: {
    ...mapState(['prefs']),
    ...mapGetters(['prefsLoaded'])
  },
  methods: {
    toggleCredits () {
      this.isCreditsShown = !this.isCreditsShown
    }
  }
}
</script>

<style lang="css" scoped>
.about-container {
  padding: 33px;
  padding-top: 80px;
  padding-bottom: 0;
  text-align: center;
}

.about-container .logo-label {
    margin: 20px 0 5px 0;
    font-size: 20px;
    color: #507caf;
}

.about-container .api-version {
    font-size: 15px;
    color: #888;
    text-shadow: 1px 1px 1px #fff;
}

.about-container .text-container {
    padding: 30px 35px 30px 35px;
    border: 1px solid #7ec183;
    border-radius: 8px;
    font-size: 0.95em;
    color: #858585;
}

.about-container .credits-text {
    text-align: left;
}

.about-container .logo svg {
    width: 190px;
    height: 190px;
}
</style>
