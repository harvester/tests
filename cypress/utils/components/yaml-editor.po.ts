import ComponentPo from './component.po';

export default class YamlEditorPo extends ComponentPo {
  input(string: string | undefined) {
    if (string) {
      this.self()
          .first()
          .then((editor) => {
            editor[0].CodeMirror.setValue('');
          });

      this.self()
          .find('textarea')
          .clear({force: true})
          .type(string, {force: true})
    }

    return
  }
}
