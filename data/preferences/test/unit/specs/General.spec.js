import Vue from 'vue'
import General from '@/components/pages/General'

describe('General.vue', () => {
  it('should render correct contents', () => {
    const Constructor = Vue.extend(General)
    const vm = new Constructor().$mount()
    expect(vm.$el.querySelector('.General .form-container').textContent)
      .to.contain('Hotkey')
  })
})
