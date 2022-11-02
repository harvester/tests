import { Constants } from "../constants/constants";
const yaml = require('js-yaml');
import YAML from 'yaml'
import cypress from "cypress";
const constants = new Constants();
export class EditYamlPage {
    private yamlInput = '.CodeMirror';
    private codeTextArea = '.CodeMirror-code'
    private saveButton = 'Save';
    private cancelButton = 'Cancel';
    private yamlText: string = "";
    private yamlOutput = ""
    
    private clearYaml() {
        cy.get(this.yamlInput)
        .first()
        .then((editor) => {
        //   editor[0].CodeMirror.setValue('');
        });
    }

    private parseYaml() {
        cy.get(this.yamlInput).invoke('text').then((text) => {
            this.yamlText=yaml.load(text);
        });
        console.log(this.yamlText);
        return this.yamlText;
    }

    public insertCustomName(customName:string) {
        // this.parseYaml();
        cy.get(this.codeTextArea).invoke('text').then((tempText) => {
            let temp = JSON.parse(tempText);
            console.log(temp);
            // debugger;
            // let temp = tempText;
            debugger;
            let jsonTemp = yaml.load(tempText);
            debugger;
            cy.log(jsonTemp)
            // jsonTemp.metadata.annotations["harvesterhci.io/host-custom-name"] = customName;
            // this.yamlText = yaml.dump(jsonTemp);
            // this.clearYaml();
            // cy.get(this.yamlInput).type(this.yamlText);
            });
    }


    public parseYamlFile() {
        cy.readFile('fixtures/harvester-master.yaml').then((str) => {
            let temp = yaml.load(str);
            // let temp = YAML.parse(str);
            temp.metadata.annotations["harvesterhci.io/host-custom-name"] = 'Test Custom Name'
            cy.writeFile('fixtures/temp.json', temp);
            let temp2 = yaml.dump(temp);
            cy.writeFile('fixtures/temp.yaml', temp2);
            // YAML.
            // this.yamlText = temp;
        })
        console.log(this.yamlText);
    }

}