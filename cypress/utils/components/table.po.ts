export default class TablePo {
  clickFlatListBtn() {
    cy.get('.btn-group button .icon-list-flat').parent().click();
  }

  /**
   * 
   * @param name: name
   * @param nameTdNum: name in the tr column
   * @param ns:  namespace
   * @param nsTdNum:  namespace in the tr column
   * @returns tr element
   */
  find(name: string, nameTdNum: number, ns: string, nsTdNum: number) {
    return cy.get('table tbody tr').find('td').eq(nameTdNum).should('contain', name).parent().find('td').eq(nsTdNum).should('contain', ns).parent();
  }
}
