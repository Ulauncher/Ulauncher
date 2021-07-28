import Vue from 'vue'
import EditableTextList from '@/components/widgets/EditableTextList'

describe('widget/EditableTextList.vue', () => {
  function construct(config) {
    const Constructor = Vue.extend(EditableTextList)
    return new Constructor(config).$mount()
  }

  it('renders correct inputs', () => {
    let vm = construct({
      propsData: {
        value: ['/var', '/tmp']
      }
    })
    expect(vm.$el.querySelector('li:nth-child(1) input').value).to.equal('/var')
    expect(vm.$el.querySelector('li:nth-child(2) input').value).to.equal('/tmp')
    expect(vm.$el.querySelector('li:nth-child(3) input').value).to.equal('')
  })
})
