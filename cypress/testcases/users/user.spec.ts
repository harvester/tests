import { RancherPageUrl, PageUrl } from "@/constants/constants";
import UserPage from "@/pageobjects/rancher/user.po";
import ClusterMemberPage from "@/pageobjects/clusterMember.po";
import Project from "@/pageobjects/project.po";
import Namespace from "@/pageobjects/namespace.po";

const user = new UserPage();
const clusterMember = new ClusterMemberPage();
const project = new Project();
const namespace = new Namespace();

describe("Setup users", () => {
  it("Setup users", () => {
    cy.login({
      username: 'admin',
      isRancher: true,
    });

    user.create({
      username: 'rancher-admin',
      newPassword: 'password1234',
      confirmPassword: 'password1234',
      administrator: true,
    })

    user.create({
      username: 'cluster-member',
      newPassword: 'password1234',
      confirmPassword: 'password1234',
    })

    user.create({
      username: 'project-owner',
      newPassword: 'password1234',
      confirmPassword: 'password1234',
    })

    user.create({
      username: 'project-member',
      newPassword: 'password1234',
      confirmPassword: 'password1234',
    })
  })
})

describe("Add users to cluster or project", () => {
  beforeEach(() => {
    cy.login({      
      username: "admin",
      url: PageUrl.clusterMember
    });
  });

  it('Add users to cluster', () => {
    clusterMember.create({
      selectMember: 'cluster-member',
      clusterPermissions: 'Member'
    })
  }) 
})

describe("Setup rancher admin", () => {
  it("Setup namespace", () => {
    cy.login({
      username: 'rancher-admin',
    }); 

    namespace.create({
      name: 'rancher-admin-namespace',
      projectName: 'Default',
    })
  })
})

describe("cluster-member create project", () => {
  beforeEach(() => {
    cy.login({      
      username: 'cluster-member',
    });
  });

  it('Create a Project', () => {
    project.create({
      name: 'cluster-member-project',
    })

    namespace.create({
      name: 'cluster-member-namespace',
      projectName: 'cluster-member-project',
    })
  }) 

  it('Add user to project', () => {
    project.create({
      name: 'project-owner-project',
      members: [{
        name: 'project-owner',
        permissions: 'Owner'
      }, {
        name: 'project-member',
        permissions: 'Member'
      }]
    })
  }) 
})

describe("project-owner create namespace", () => {
  beforeEach(() => {
    cy.login({      
      username: 'project-owner',
    });
  });

  it('Create a namespace', () => {
    namespace.create({
      name: 'project-owner-namespace',
      projectName: 'project-owner-project',
    })
  })
})

describe("project-member create namespace", () => {
  beforeEach(() => {
    cy.login({      
      username: 'project-member',
    });
  });

  it('Create a namespace', () => {
    namespace.create({
      name: 'project-member-namespace',
      projectName: 'project-owner-project',
    })
  })
})
