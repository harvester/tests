import YAML from 'js-yaml'

import sshPage from "@/pageobjects/sshKey.po";
import { LoginPage } from "@/pageobjects/login.po";
import {sshKey as sshKeyExample} from '@/fixtures/ssh-key.js'
import {generateName} from '@/utils/utils';


const ssh = new sshPage();
const login = new LoginPage();

/**
 * 1. Login
 * 2. Navigate to the ssh create page
 * 3. click Create button
 * Expected Results
 * 1. Create ssh success
*/
export function CheckCreateSsh() {}
describe('Create a ssh key', () => {
  it('Create a ssh key', () => {
    cy.login();

    const name = generateName('test-ssh-create');
    const namespace = 'default'

    ssh.create({
      name,
      namespace,
      sshKey: sshKeyExample,
    })

    const cloneName = generateName('test-ssh-clone');
    ssh.clone(`${namespace}/${ name }`, {
      name: cloneName,
      namespace,
    })
    
    ssh.delete(namespace, name)
    ssh.delete(namespace, cloneName)
  });
});
