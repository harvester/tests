export default class TablePo {
  clickFlatListBtn() {
    cy.get('.btn-group button .icon-list-flat').parent().click();
  }

  clickFolderBtn() {
    cy.get('.btn-group button .icon-folder').parent().click();
  }
  
  /**
   * 
   * @param name: name
   * @param nameTdNum: name in the tr column
   * @param ns:  namespace
   * @param nsTdNum:  namespace in the tr column
   * @returns the position of tr
   */
  find(name: string, nameTdNum: number, ns: string, nsTdNum: number) {
    let resourceIndex:any;
    return new Cypress.Promise((resolve) => {
      cy.get(`table > tbody > tr > td:nth-child(${nameTdNum})`).each(($e1, index, $list) => {

        const nameText = $e1.text().trim();
  
        if(nameText === name) {
          cy.get(`tr td:nth-child(${nsTdNum})`)
            .eq(index)
            .then(function ($ns) {
              const nsText = $ns.text().trim();
              if (ns === nsText) {
                resourceIndex = index; 
                expect(nsText).to.contains(ns);
                expect(nameText).to.contains(name);

                cy.wait(2000).then(() => {
                  resolve(resourceIndex)
                })
              }
            })
        }
      })
    })
  }
}
