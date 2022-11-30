import cookie from 'cookie';

import { Constants } from "@/constants/constants";
import PagePo from '@/utils/components/page.po';
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import TablePo from "@/utils/components/table.po";

const constants = new Constants();

export default class CruResourcePo extends PagePo {
  /**
   * @param type: matches navigation url.
   * @param realType: matches api.
   * @param storeType: matches vuex.
   */
  constructor({ type, realType, storeType}:  {type: string, realType?: string, storeType?: string}) {
    super(`/harvester/c/local/${type}`);

    this.type = type
    this.realType = realType || type
    this.storeType = storeType || realType
  }

  public type = '';
  public realType = '';
  public storeType: string|undefined = undefined;
  public table = new TablePo();;
  public footerButtons = '.cru-resource-footer'
  public confirmRemove = '.card-container.prompt-remove'
  public searchInput = '.search'
  public actionMenu = '.list-unstyled.menu'
  public actionMenuIcon = '.icon-actions'
  public actionButton = '.outlet .actions-container';

  namespace() {
    return new LabeledSelectPo('.labeled-select', `:contains("Namespace")`)
  }

  name() {
    return new LabeledInputPo('.span-3 >.labeled-input', `:contains("Name")`)
  }

  description() {
    return new LabeledInputPo('.labeled-input', `:contains("Description")`)
  }

  clickTab(contains: string) {
    const path = `.resource-container .side-tabs .tab#${contains}`
    cy.get(path).click()
  }

  clickFooterBtn(butText: string = 'save') {
    cy.get(this.footerButtons).find(`[data-testid="form-${butText}"]`).click()
  }

  goToCreatePage(buttonText: string = 'Create') {
    cy.get('.outlet .actions-container .actions').contains(buttonText).click();
  }

  public create(value: any, urlWithNamespace?: boolean) {
    cy.visit(`/harvester/c/local/${this.type}/create`)

    this.setValue(value)
    
    if (urlWithNamespace) {
      this.save({namespace: value.namespace})
    } else {
      this.save()
    }
  }

  public clone(id:string, value:any) {
    cy.visit(`/harvester/c/local/${this.type}/${id}?mode=clone`)

    this.setValue(value)

    this.save()
  }
  

  public save({namespace, buttonText = 'save'} : {namespace?:string, buttonText?:string} = {}) {
    if (namespace) {
      cy.intercept('POST', `/v1/harvester/${this.realType}s/${namespace}`).as('create');
    } else {
      cy.intercept('POST', `/v1/harvester/${this.realType}s`).as('create');
    }
    
    this.clickFooterBtn(buttonText)
    cy.wait('@create').then(res => {
      expect(res.response?.statusCode, `Create ${this.type} success`).to.equal(201);
    })
  }

  public delete(namespace:any, name:string, { id }: { id?: string } = {}) {
    cy.visit(`/harvester/c/local/${this.type}`)

    this.clickAction(name, 'Delete')

    if (id) {
      cy.intercept('DELETE', `/v1/harvester/${this.realType}s/${id}*`).as('delete');
    } else {
      cy.intercept('DELETE', `/v1/harvester/${this.realType}s/${namespace}/${name}*`).as('delete');
    }

    cy.get(this.confirmRemove).contains('Delete').click();
    cy.wait('@delete').then(res => {
      cy.window().then((win) => {
        this.checkDelete(this.storeType as string, `${namespace}/name`);
        expect(res.response?.statusCode, `Delete ${this.type}`).to.be.oneOf([200, 204]);
      })
    })
  }

  async deleteFromStore(id: string, realType: string=this.realType) {
    cy.window().then(async (win: any) => {
      try {
        const resource = await (win as any).$nuxt.$store.dispatch('harvester/find', { type: realType, id: id });
        await resource.remove();
        this.checkDelete(realType, id)
      } catch(e: any) {
        if (e.status === 404) {
          cy.log(`The resource ${realType} does not exist`)
        } else {
          cy.log(e.status)
        }
      }
    })
  }

  public checkDelete(type: string = this.type, id: string) {
    cy.window().then(async (win) => {
      let times = 0;
      await new Cypress.Promise((resolve, reject) => {
        const timer = setInterval(() => {
          times = times + 1;
          if (times > 40) {
            cy.log(`${type} can't removed from the backend`)
            reject()
          }

          const resource = (win as any).$nuxt.$store.getters['harvester/byId'](type, id);

          if (resource === undefined) {
            cy.log(`${type} has been removed from the backend`)
            clearInterval(timer);
            resolve()
          }
        }, 2000)
      })
    })
  }

  setNameNsDescription(name: string, ns: string, description?: string) {
    this.namespace().select({ option: ns })
    this.name().input(name)
    this.description().input(description)
  }

  public setValue(value: any) {
    this.namespace().select({option: value?.namespace})
    this.name().input(value?.name)
    this.description().input(value?.description)
  }

  public update(id:string, type?: string) {
    const _type = type || this.realType
    cy.intercept('PUT', `/v1/harvester/${_type}s/${id}`).as('update');
    cy.get(this.footerButtons).contains('Save').click()
    cy.wait('@update').then(res => {
      expect(res.response?.statusCode, `Check edit ${id}`).to.equal(200);
    })
  }

  public hasAction({name, nameIndex = 3, ns, nsIndex = 4, action, expect = true, nameSelector}: { name:string, nameIndex?:number, ns:string, nsIndex?:number, action: string, expect?:boolean, nameSelector?:string }) {
    this.search(name);
    cy.wait(2000);
    cy.wrap('async').then(() => {
      this.table.find(name, nameIndex, ns, nsIndex, nameSelector).then((rowIndex: any) => {
        if (typeof rowIndex === 'number') {
          cy.get(`[data-testid="sortable-table-${rowIndex}-row"]`).find(this.actionMenuIcon).click();
          cy.get(this.actionMenu).should(`${expect ? '' : 'not.'}contain`, action);
          // click outside to close action menu
          cy.get('body').click(0,0);
        }
      })
    });
  }

  public clickAction(name:string, action: string) {
    this.search(name);
    const record = cy.contains(name)
    expect(record.should('be.visible'))
    record.parentsUntil('tbody', 'tr').find(this.actionMenuIcon).click()
    return cy.get(this.actionMenu).contains(action).click()
  }

  public checkEdit(name:string, namespace?:string, value?:any, action:string = 'Edit Config') {
    this.clickAction(name, action)
  
    this.setValue(value)
    
    if (namespace) {
      this.update(`${namespace}/${name}`)
    } else {
      this.update(`${name}`)
    }
  }

  public checkClone(name:string, namespace?:string, value?:any, action:string = 'Clone') {
    this.clickAction(name, action)
  
    this.setValue(value)
    
    this.save()
  }

  // make sure that current page is the list page.
  public search(queryString: any) {
    cy.get('.sortable-table-header .search-box').should('be.visible');
    cy.get(this.searchInput).find('input').clear().type(queryString);
  }

  public searchClear() {
    cy.get('.sortable-table-header .search-box').should('be.visible');
    cy.get(this.searchInput).find('input').clear();
  }


  /**
   *
   * @param name: resource name
   * @param value: expected value in the column of table
   * @param pos:  the coordinate of the column
   * @param options: additional options
   * @returns null
   */
  public censorInColumn(name: string, nameIndex: number, ns: string, nsIndex: number, columnValue: any, columnIndex: number = 2, options: any = {}) {
    this.search(name);
    cy.wait(2000);
    cy.wrap('async').then(() => {
      this.table.find(name, nameIndex, ns, nsIndex, options?.nameSelector).then((rowIndex: any) => {
        if (typeof rowIndex === 'number') {
          cy.get(`[data-testid="sortable-table-${rowIndex}-row"]`).find('td').eq(columnIndex - 1, {timeout: options?.timeout || constants.timeout.timeout}).should('contain', columnValue);
        }
      })
    });
  }

  public goToList() {
    cy.intercept('GET', `/v1/harvester/${this.realType}s`).as('goToList');
    cy.visit(`/harvester/c/local/${this.type}`)
    cy.wait('@goToList');
  }

  public goToCreate() {
    this.goToList();
    cy.get(this.actionButton).find('a').contains(' Create ').click();
  }

  public goToEdit(name: string) {
    this.goToList()
    this.clickAction(name, 'Edit Config');
  }

  public goToDetail({name, nameIndex = 3, ns, nsIndex = 4, nameSelector}: { name:string, nameIndex?:number, ns:string, nsIndex?:number, nameSelector?:string }) {
    this.goToList();
    this.search(name);
    cy.wait(2000);
    cy.wrap('async').then(() => {
      this.table.find(name, nameIndex, ns, nsIndex, nameSelector).then((rowIndex: any) => {
        if (typeof rowIndex === 'number') {
          cy.get(`[data-testid="sortable-table-${rowIndex}-row"]`).contains(name).click();
        }
      })
    })
  }
}
