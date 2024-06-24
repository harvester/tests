import { HCI, PVC } from "@/constants/types";
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import CruResourcePo from "@/utils/components/cru-resource.po";

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  source?: string,
  image?: string,
  size?: string,
}

export class VolumePage extends CruResourcePo {
  private exportImageActions: string = ".card-actions";

  constructor() {
    super({
      type: HCI.VOLUME,
      realType: PVC,
    });
  }

  exportImageName() {
    return new LabeledInputPo(
      ".card-container .labeled-input",
      `:contains("Name")`
    );
  }

  source() {
    return new LabeledSelectPo(".labeled-select", `:contains("Source")`);
  }

  size() {
    return new LabeledInputPo(".labeled-input", `:contains("Size")`);
  }

  image() {
    return new LabeledSelectPo(".labeled-select", `:contains("Image"):last`);
  }

  checkState(name:  string, state: string = 'Ready', namespace: string = 'default') {
    this.goToList();
    this.censorInColumn(name, 3, namespace, 4, state, 2);
  }

  checkSnapshotCount(volumeName: string, count: number, namespace: string = 'default') {
    this.goToList();
    this.censorInColumn(volumeName, 3, namespace, 4, count, 8);
  }

  clickVolumeSnapshotAction(name: string, snapshotName: string) {
    this.clickAction(name, 'Take Snapshot');
    cy.get('.v--modal-box').find('.card-title').contains('Take Snapshot');

    new LabeledInputPo('.v--modal-box .labeled-input', `:contains("Name")`).input(snapshotName)
    cy.get('.v--modal-box button').contains('Create').click();
    cy.get('.growl-container .growl-list').find('.growl-text div').contains('Succeed');
  }

  setBasics({source, image, size} : { source?: string, image?: string, size: string }) {
    this.clickTab('basic');

    if (source) {
      this.source().select({option: source});
    }

    if (image) {
      this.image().select({option: image});
    }

    this.size().input(size);
  }

  checkVMAttached(ns: string, name: string, vmName: string) {
    cy.get(this.searchInput).type(name);
    cy.wait(2000)
    cy.wrap('async').then(() => {
      this.table.find(name, 3, ns, 4).then((index: any) => {
        if (typeof index === 'number') {
          cy.get(`[data-testid="sortable-table-${index}-row"]`).find('td').eq(6).should(($el: any) => {
            expect($el).to.contain(vmName)
          })
        }
      })
    })
  }

  public exportImage(volumeName: string, imageName: string) {
    this.clickAction(volumeName, 'Export Image')
    this.exportImageName().input(imageName);

    cy.intercept(
      "POST",
      `v1/harvester/persistentvolumeclaims/*/${volumeName}?action=export`
    ).as("exportImage");
    cy.get(this.exportImageActions).contains("Create").click();
    cy.wait("@exportImage").then((res) => {
      expect(res.response?.statusCode).to.be.oneOf([200, 204]);
      expect(cy.contains("Succeed"));
    });
  }

  public setValue(value: ValueInterface) {
    this.namespace().select({option: value?.namespace})
    this.size().input(value?.size);
    this.name().input(value?.name);

    if (!!value.image) {
      this.source().select({option: "VM Image"});
      this.image().select({option: value?.image});
    }
  }

  public deleteVolumeByVM(vmName: string) {
    this.goToList();
    cy.get(this.searchInput).type(vmName);

    const volume = cy.contains(vmName);

    volume.should("be.visible");

    // Get volume name from attahched VM in name field of Volume page
    volume
      .parentsUntil("tbody", "tr")
      .find("td")
      .eq(2)
      .invoke("text")
      .then((volumeName) => {
        this.delete("default", volumeName.trim());
      });
  }

  basePath() {
    return Cypress.env('NODE_ENV') === 'dev' ? Cypress.env('baseUrl') : `${Cypress.env('baseUrl')}/dashboard`;
  }
}
