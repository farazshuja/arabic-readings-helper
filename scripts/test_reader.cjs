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
  createElementNS(ns, tag) { return new Node(tag); },
  createTextNode(text) { const n = new Node(); n.textContent = text; return n; }
};
const context = vm.createContext({ document, console });
const source = fs.readFileSync('website/dist/app.js', 'utf8');
vm.runInContext(source.slice(0, source.indexOf('const closeButton =')), context);
const catalog = JSON.parse(fs.readFileSync('data/stories.json', 'utf8'));
let checked = 0, excluded = 0;
for (const record of catalog.stories) {
  context.story = JSON.parse(fs.readFileSync(`data/${record.file}`, 'utf8'));
  vm.runInContext('story = prepareStory(story)', context);
  if (context.story.wordLookup === 'google') {
    assert(!context.story.vocabulary);
    for (const section of context.story.sections) {
    context.requestedSection = section.id;
    vm.runInContext('renderReader(story, requestedSection)', context);
    const reader = nodes.get('#main');
    function descendants(node) { return [node, ...node.children.flatMap(descendants)]; }
    const rendered = descendants(reader);
    const paragraphs = rendered.filter(n => n.className === 'arabic line-text');
    assert.deepEqual(paragraphs.map(n => n.textContent), section.lines.map(l => l.vocalized));
    assert.equal(rendered.filter(n => n.className === 'reading-line passage-footnote').length, section.lines.filter(l => l.kind === 'footnote').length);
    }
  }
  for (const section of context.story.sections) for (const line of section.lines) {
    context.line = line;
    for (const full of [false, true]) {
      context.full = full; context.container = new Node();
      vm.runInContext('renderWords(container, line.tokens, line.leading, full, story)', context);
      assert.equal(context.container.textContent, full ? line.vocalized : line.text);
      if (context.story.wordLookup === 'google') {
        const links = context.container.children.filter(n => n.tag === 'a');
        assert.equal(links.length, line.tokens.length);
        for (const [i, link] of links.entries()) {
          assert.equal(link.target, '_blank');
          assert.equal(link.rel, 'noopener noreferrer');
          const url = new URL(link.href);
          assert.equal(url.origin, 'https://www.google.com');
          assert.equal(url.searchParams.get('q'), `What is the meaning of ${line.tokens[i].vocalized}, provide its madi/mudari/masdar form if its a verb, or sing./pl. forms if its a noun`);
        }
        continue;
      }
      const expected = line.tokens.filter(t => !['pronoun', 'particle', 'preposition'].includes(context.story.vocabulary[t.vocabularyId].partOfSpeech));
      assert.equal(context.container.children.filter(n => n.tag === 'button').length, expected.length);
    }
    for (const token of line.tokens) {
      if (context.story.wordLookup === 'google') continue;
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
