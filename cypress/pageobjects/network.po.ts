import PagePo from '@/utils/components/page.po';

export default class NetworkPage extends PagePo {
  static type: string = 'k8s.cni.cncf.io.networkattachmentdefinition'
  static url: string = `/c/local/harvester/${this.type}`

  constructor() {
    super(NetworkPage.url);
  }

  public goToList() {
    cy.intercept('GET', `/v1/harvester/k8s.cni.cncf.io.network-attachment-definitions`).as('goToList');
    cy.visit(NetworkPage.url);
    cy.wait('@goToList')
    expect(cy.url().should('eq', NetworkPage.url));
  }
}