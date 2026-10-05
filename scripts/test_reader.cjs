const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
class Node {
  constructor(tag = '') { this.tag = tag; this.children = []; this.value = ''; }
  set textContent(value) { this.value = value; this.children = []; }
  get textContent() { return this.value + this.children.map(x => x.textContent).join(''); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.value = ''; this.children = nodes; }
  setAttribute() {}
  showModal() { this.open = true; }
}
const nodes = new Map();
const document = {
  querySelector(selector) { if (!nodes.has(selector)) nodes.set(selector, new Node()); return nodes.get(selector); },
  createElement(tag) { return new Node(tag); },
  createTextNode(text) { const n = new Node(); n.textContent = text; return n; }
};
const context = vm.createContext({ document, console });
const source = fs.readFileSync('website/dist/app.js', 'utf8');
vm.runInContext(source.slice(0, source.indexOf('const closeButton =')), context);
const catalog = JSON.parse(fs.readFileSync('data/stories.json', 'utf8'));
let checked = 0, excluded = 0;
for (const record of catalog.stories) {
  context.story = JSON.parse(fs.readFileSync(`data/${record.file}`, 'utf8'));
  for (const section of context.story.sections) for (const line of section.lines) {
    context.line = line;
    for (const full of [false, true]) {
      context.full = full; context.container = new Node();
      vm.runInContext('renderWords(container, line.tokens, line.leading, full, story)', context);
      assert.equal(context.container.textContent, full ? line.vocalized : line.text);
      const expected = line.tokens.filter(t => !['pronoun', 'particle', 'preposition'].includes(context.story.vocabulary[t.vocabularyId].partOfSpeech));
      assert.equal(context.container.children.filter(n => n.tag === 'button').length, expected.length);
    }
    for (const token of line.tokens) {
      context.token = token;
      if (['pronoun', 'particle', 'preposition'].includes(context.story.vocabulary[token.vocabularyId].partOfSpeech)) {
        nodes.get('#vocabulary').open = false;
        vm.runInContext('openWord(token, story)', context);
        assert.equal(nodes.get('#vocabulary').open, false);
        excluded++;
      } else {
        vm.runInContext('openWord(token, story)', context);
        assert.equal(nodes.get('#vocabulary').open, true);
        assert(!nodes.get('#word-content').textContent.includes('Attached words'));
      }
    }
    checked++;
  }
}
console.log(`PASS reader: ${checked} lines in both modes; ${excluded} function-word occurrences cannot open cards.`);
