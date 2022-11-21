import { Constants } from "@/constants/constants";
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import { HCI, STORAGE_CLASS } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';
import RadioButtonPo from '@/utils/components/radio-button.po';

const constants = new Constants();

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  replicas?: string,
  staleReplicaTimeout?: string,
  migratable?: string,
  reclaimPolicy?: string,
  allowVolumeExpansion?: any,
  volumeBindingMode?: string,
}

//TODO: The Host/Disk Tags selector will add after hosts.spec.ts implement Host/Disk Tags
export default class StoragePage extends CruResourcePo {
  constructor() {
    super({
      type: HCI.STORAGE_CLASS,
      realType: STORAGE_CLASS,
    });
  }

  private customizeTab = '.tab#customize';

  public setValue(value: ValueInterface) {
    this.name().input(value?.name)
    this.description().input(value?.description)
    this.replicas().input(value?.replicas)
    this.staleReplicaTimeout().input(value?.staleReplicaTimeout)
    this.migratable().input(value?.migratable)

    cy.get(this.customizeTab).click()
    this.reclaimPolicy().input(value?.reclaimPolicy)
    this.allowVolumeExpansion().input(value?.allowVolumeExpansion)
    this.volumeBindingMode().input(value?.volumeBindingMode)
  }

  replicas() {
    return new LabeledInputPo('.labeled-input', `:contains("Number Of Replicas")`)
  }

  staleReplicaTimeout() {
    return new LabeledInputPo('.labeled-input', `:contains("Stale Replica Timeout")`)
  }

  migratable() {
    return new RadioButtonPo('.radio-group', ':contains("Migratable")')
  }

  reclaimPolicy() {
    return new RadioButtonPo('.radio-group', ':contains("Reclaim Policy")')
  }

  allowVolumeExpansion() {
    return new RadioButtonPo('.radio-group', ':contains("Allow Volume Expansion")')
  }

  volumeBindingMode() {
    return new RadioButtonPo('.radio-group', ':contains("Volume Binding Mode")')
  }

  checkValue(value: ValueInterface) {
    cy.window().then((window: any) => {
      const store = window.$nuxt.$store

      const resource = store.getters['harvester/byId']('storage.k8s.io.storageclass', value.name)
      
      expect(resource?.parameters?.numberOfReplicas, 'Number Of Replicas').to.equal(value.replicas)
      expect(resource?.parameters?.staleReplicaTimeout, 'Stale Replica Timeout').to.equal(value.staleReplicaTimeout)
      expect(resource?.parameters?.migratable, 'Migratable').to.equal(value.migratable)
      expect(resource?.reclaimPolicy, 'Reclaim Policy').to.equal(value.reclaimPolicy)
      expect(resource?.allowVolumeExpansion, 'Allow Volume Expansion').to.equal(value.allowVolumeExpansion)
      expect(resource?.volumeBindingMode, 'Volume Binding Mode').to.equal(value.volumeBindingMode)
    })
  }

  public delete({ 
    name 
  } : {
    name:string
  }) {
    cy.visit(`/harvester/c/local/${this.type}`)

    this.clickAction(name, 'Delete')

    cy.intercept('DELETE', `/v1/harvester/${this.realType}s/${name}*`).as('delete');

    cy.get(this.confirmRemove).contains('Delete').click();
    cy.wait('@delete').then(res => {
      expect(res.response?.statusCode, `Delete ${this.type}`).to.be.oneOf([200, 204]);
    })
  }
}
