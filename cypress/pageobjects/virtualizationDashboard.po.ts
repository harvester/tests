export default class VirtualizationDashboard {

    private clusterName = '.cluster-name';
    private productName = '.product-name';

    public validateClusterName() {
        cy.get(this.clusterName).should('exist').then(() => {
            cy.log('Cluster Name Exists');
            cy.get(this.clusterName).then((elem) => {
                const textValue = elem.text();
                cy.log('Cluster Name is ' + textValue)
            });
        });
    }

    public validateProductName() {
        cy.get(this.productName).should('exist').then(() => {
            cy.log('Product Name Exists');
            cy.get(this.productName).then((elem) => {
                const textValue = elem.text();
                cy.log('Product Name is ' + textValue)
            });
        });
    }
}