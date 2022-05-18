
import AdmZip from 'adm-zip';
/**
 * This will validate the zip file by checking the contents. Assumes that this is in 
 * the downloads folder
 * @param filename a string of the filename for zip validation
 */
export const validateZip = (filename: string) => {
    const path = require('path');
    const downloadsFolder = Cypress.config('downloadsFolder')
    const downloadedFilename = path.join(downloadsFolder, filename)
    var zip = new AdmZip(downloadedFilename);
    var zipEntries = zip.getEntries(); // an array of ZipEntry records
    zipEntries = zip.getEntries(); // an array of ZipEntry records

    zipEntries.forEach(function (zipEntry) {
        console.log(zipEntry.toString()); // outputs zip entries information
        // if (zipEntry.entryName == "my_file.txt") {
        //     console.log(zipEntry.getData().toString("utf8"));
        // }
    });
}

export const deleteDownloadsFolder = () => {
    const downloadsFolder = Cypress.config('downloadsFolder')
  
    cy.task('deleteFolder', downloadsFolder)
}

export const generateName = (prefix: string) => {
    return `${prefix}-${Date.now()}`
}
