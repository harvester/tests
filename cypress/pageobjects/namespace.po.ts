import { HCI } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';

export default class NamespacePage extends CruResourcePo {
  constructor() {
    super({
      type: HCI.NAMESPACE
    });
  }

  setNameDescription(name: string, description?: string | undefined): void {
    if (name) {
      this.name().input(name)
    }

    if (description) {
      this.description().input(description)
    }
  }

  public create(value: any) {
    if (value.projectName) {
      cy.window().then(async (window: any) => {
        const store = window.$nuxt.$store

        await store.dispatch('management/findAll', {
          type: 'management.cattle.io.project'
        })

        const projects = store.getters['management/all']('management.cattle.io.project')
        const project = projects.find(p => p.spec.displayName === value.projectName)
        const projectId = project?.metadata?.name

        cy.visit(`/harvester/c/${Cypress.config('clusterId')}/${this.type}/create?projectId=${projectId}`)
      })
    } else {
      cy.visit(`/harvester/c/${Cypress.config('clusterId')}/${this.type}/create`)
    }

    this.setValue(value)
    
    this.save()
  }
}
