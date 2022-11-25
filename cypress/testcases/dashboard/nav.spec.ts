import { Navbar } from '@/utils/components/page.po';
import { MenuNav } from "@/constants/constants";

const navBar = new Navbar();

describe("UI url", () => {
  beforeEach(() => {
    cy.login()
  })

  // https://harvester.github.io/tests/manual/ui/verify-url/
  it("Verify the Harvester UI UR (all)", () => {
    Object.values(MenuNav).forEach((nav) => {
      // @ts-ignore
      navBar.clickMenuNav(...nav);
    })
  })

  it("Verify the Harvester icon on the left top corner", () => {
    cy.get('.dashboard-content header .menu-spacer').find('img', {timeout: 4000}).then(($el) => {
      const src = $el.attr('src');
      expect(src).include('providers/harvester.svg')
    })
  })
})
