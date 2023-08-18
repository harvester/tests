import { Constants } from "@/constants/constants";
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import LabeledTextAreaPo from '@/utils/components/labeled-textarea.po';
import { HCI } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';
import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { generateName } from '@/utils/utils';
import CheckboxPo from '@/utils/components/checkbox.po';

const constants = new Constants();
const vms = new VmsPage();

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  cpu?: string,
  memory?: string,
  image?: string,
}

interface Volume {
  buttonText: string,
  create?: boolean,
  [index: string]: any
}

export default class TemplatePage extends CruResourcePo {
  constructor() {
    super({
      type: HCI.VM_VERSION,
      realType: HCI.VM_TEMPLATE,
    });
  }

  public save({type = this.type, namespace = 'default'}: {type?:string, namespace:string}): Promise<string> {
    return new Cypress.Promise((resolve, reject) => {
      const interceptName = generateName('create');

      cy.intercept('POST', `/v1/harvester/${type}s/${namespace}`).as(interceptName);
      this.clickFooterBtn()
      cy.wait(`@${interceptName}`).then(res => {
        expect(res.response?.statusCode, `Create ${this.type} success`).to.equal(201);
        console.log(res.response?.body?.metadata?.name);
        resolve(res.response?.body?.metadata?.name || '');
      })
      .end();
    });
  }

  image() {
    return new LabeledSelectPo('.labeled-select', `:contains("Image")`)
  }

  createNewVersion(name: string) {
    this.goToList()
    this.clickAction(name, 'Add templateVersion')
  }

  setBasics(cpu?: string, memory?: string, ssh?: {id?: string, createNew?: boolean, value?: string}) {
    this.clickTab('Basics');
    vms.cpu().input(cpu);
    vms.memory().input(memory);

    if (ssh && ssh.id) {
      new LabeledSelectPo('.labeled-select', `:contains("SSHKey")`).select({option: ssh.id});
    } else if (ssh && ssh.createNew) {
      new LabeledSelectPo('.labeled-select', `:contains("SSHKey")`).select({option: 'Create a New...'});
      new LabeledTextAreaPo('.v--modal-box .card-container .labeled-input', `:contains("SSH-Key")`).input(ssh.value, {
        delay: 0,
      });

      cy.get('.v--modal-box .card-container').contains('Create').click();
    }
  }

  setVolumes(volumes: Array<Volume>) {
    this.clickTab('Volume');
    cy.wrap('async').then(() => {
      volumes.map((volume) => {
        if (volume.create) {
          cy.get('.tab-container button').contains(volume.buttonText).click()
        }
      });

      volumes.map((volume, index) => {
        let imageEl: any;
        let volumeEl: any;
        cy.get('.info-box').eq(index).within(() => {
            if (volume.image) {
              imageEl = new LabeledSelectPo('.labeled-select', `:contains("Image")`);
            }

            if (volume.size) {
              new LabeledInputPo('.labeled-input', `:contains("Size")`).input(volume.size);
            }

            if (volume.volume) {
              volumeEl = new LabeledSelectPo('.labeled-select', `:contains("Volume")`);
            }
        }).then(() => {
          if (imageEl) {
            imageEl.select({option: volume.image});
          }

          if (volumeEl) {
            volumeEl.select({option: volume.volume});
          }
        })
      })
    })
  }

  setAdvancedOption(option: {[index: string]: any}) {
    this.clickTab('advanced');

    if (option.runStrategy) {
      new LabeledSelectPo('.labeled-select', `:contains("Run Strategy")`).select({option: option.runStrategy});
    }

    if ([true, false].includes(option.efiEnabled)) {
      this.efiEnabled().check(option.efiEnabled)
    }
  }

  efiEnabled() {
    return new CheckboxPo('.checkbox-container', `:contains("Booting in EFI mode")`)
  }
}
