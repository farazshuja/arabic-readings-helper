'use strict';

const main = document.querySelector('#main');
const dialog = document.querySelector('#vocabulary');
const content = document.querySelector('#word-content');
const cache = new Map();
const revealed = new Set();
let catalog;
let routeRequest = 0;
let toastTimer;
const readingStorageKey = 'qiraah:last-reading';

function lastReading() {
  try {
    const saved = JSON.parse(localStorage.getItem(readingStorageKey));
    if (!saved || typeof saved.storyId !== 'string' || typeof saved.sectionId !== 'string') return null;
    const story = catalog.stories.find(story => story.id === saved.storyId);
    return story ? { story, sectionId: saved.sectionId } : null;
  } catch { return null; } // Storage may be unavailable or contain invalid data.
}

const icons = {
  copy: '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  book: '<path d="M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Zm0 0v15"/>',
};
function icon(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  svg.innerHTML = icons[name]; // Fixed internal SVG paths only; story text is never HTML.
  return svg;
}
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function ar(node) { node.lang = 'ar'; node.dir = 'rtl'; return node; }
function ur(node) { node.lang = 'ur'; node.dir = 'rtl'; return node; }
function notify(message) {
  clearTimeout(toastTimer);
  const toast = document.querySelector('#toast');
  toast.textContent = message;
  toast.classList.add('visible');
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 3500);
}
async function loadJSON(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Could not load ${path}`);
  return response.json();
}
function storyPath(record) {
  // Catalog files stay on the same origin beneath data/.
  if (!/^stories\/[a-zA-Z0-9_-]+\.json$/.test(record.file)) throw new Error('Invalid story path');
  return `data/${record.file}`;
}
function linkFor(storyId, sectionId = '') {
  return `#story/${encodeURIComponent(storyId)}${sectionId ? '/' + encodeURIComponent(sectionId) : ''}`;
}
function focusMain() { main.focus({ preventScroll: true }); window.scrollTo(0, 0); }

function renderLibrary() {
  document.title = 'Qira’ah · Arabic reading';
  const eyebrow = el('div', 'eyebrow', 'YOUR READING LIBRARY');
  const heading = el('h1', '', 'One story. A little more Arabic.');
  const intro = el('p', 'intro', 'Read at your own pace. Reveal the vowels when you need them, and tap highlighted words for their English and Urdu meanings.');
  const label = el('div', 'library-label');
  label.append(el('h2', '', 'Choose a story'), el('span', 'small', `${catalog.stories.length} ${catalog.stories.length === 1 ? 'story' : 'stories'} available`));
  const grid = el('div', 'story-grid');
  for (const story of catalog.stories) {
    const card = el('article', 'story-card');
    const cover = el('div', 'book-spine');
    cover.setAttribute('aria-hidden', 'true');
    cover.append(el('span', 'number', String(story.number).padStart(2, '0')), ar(el('span', 'book-letter', 'اقرأ')), el('span', 'book-foot', 'BEGINNER STORIES'));
    const details = el('div', 'story-details');
    details.append(el('span', 'eyebrow', `STORY ${String(story.number).padStart(2, '0')}`), ar(el('h3', 'arabic arabic-title', story.title)), el('p', 'english-title', story.titleEnglish));
    const meta = el('div', 'meta');
    meta.append(el('span', '', `${story.counts.sections} chapters`), el('span', '', story.wordLookup === 'google' ? 'Google word lookup' : 'English + اردو'));
    if (story.publication?.status === 'partial') details.append(el('p', 'small', story.publication.label));
    const start = el('a', 'primary', 'Read story');
    start.href = linkFor(story.id);
    details.append(meta, start);
    card.append(cover, details); grid.append(card);
  }
  const tip = el('p', 'reading-tip');
  tip.append(icon('book'), document.createTextNode('Start with the lighter text. Each line has its own vowel and copy controls, so you can focus on just the sentence in front of you.'));
  const resume = lastReading();
  const resumeNodes = [];
  if (resume) {
    const banner = el('p', 'resume-reading');
    const link = el('a', '', `Resume reading: ${resume.story.titleEnglish}`);
    link.href = linkFor(resume.story.id, resume.sectionId);
    banner.append(icon('book'), link);
    resumeNodes.push(banner);
  }
  main.replaceChildren(eyebrow, heading, intro, ...resumeNodes, label, grid, tip);
}

function vocabularyCardEntry(token, story) {
  const entry = story.vocabulary?.[token.vocabularyId];
  if (!entry || ['pronoun', 'particle', 'preposition'].includes(entry.partOfSpeech)) return null;
  return entry;
}

function renderWords(container, tokens, leading, showHarakat, story) {
  container.replaceChildren(document.createTextNode(leading || ''));
  for (const token of tokens) {
    if (story.wordLookup === 'google') {
      const word = el('a', 'word', showHarakat ? token.vocalized : token.text);
      word.href = googleWordURL(token.vocalized);
      word.target = '_blank'; word.rel = 'noopener noreferrer';
      word.setAttribute('aria-label', `${token.vocalized} — search Google for meaning and forms (new tab)`);
      container.append(word, document.createTextNode(token.after));
      continue;
    }
    if (!vocabularyCardEntry(token, story)) {
      container.append(document.createTextNode((showHarakat ? token.vocalized : token.text) + token.after));
      continue;
    }
    const word = el('button', 'word', showHarakat ? token.vocalized : token.text);
    word.type = 'button';
    word.setAttribute('aria-haspopup', 'dialog');
    word.setAttribute('aria-label', `${token.text} — word meanings`);
    word.onclick = () => openWord(token, story);
    container.append(word, document.createTextNode(token.after));
  }
}

function googleWordURL(word) {
  const query = `What is the meaning of ${word}, provide its madi/mudari/masdar form if its a verb, or sing./pl. forms if its a noun`;
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

function prepareStory(story) {
  if (story.wordLookup !== 'google') return story;
  function passage(vocalized, id) {
    const matches = [...vocalized.matchAll(/[\u0621-\u064a][\u0621-\u064a\u064b-\u0652\u0670]*/g)];
    const lighter = value => value.replace(/[\u064b-\u0650\u0652\u0670]/g, '');
    const tokens = matches.map((m, i) => ({ id: `${id}-w${i + 1}`, vocalized: m[0], text: lighter(m[0]),
      after: vocalized.slice(m.index + m[0].length, matches[i + 1]?.index ?? vocalized.length) }));
    const leading = vocalized.slice(0, matches[0]?.index ?? vocalized.length);
    return { vocalized, text: lighter(vocalized), tokens, leading };
  }
  const title = passage(story.titleVocalized, 'title');
  const sections = story.sections.map(section => {
    const heading = passage(section.titleVocalized, section.id);
    const lines = section.lines.map(line => ({ ...line, ...passage(line.vocalized, line.id) }));
    return { ...section, title: heading.text, titleTokens: heading.tokens, lines };
  });
  for (const section of sections) for (const line of section.lines) revealed.add(`${story.id}:${line.id}`);
  return { ...story, title: title.text, titleTokens: title.tokens, subtitle: story.subtitleVocalized, sections };
}

function openWord(token, story) {
  const entry = vocabularyCardEntry(token, story);
  if (!entry) return;
  const heading = ar(el('h2', 'arabic', token.vocalized));
  heading.id = 'word-heading';
  const posLabels = { properNoun: 'Proper name', noun: 'Noun', adjective: 'Adjective', verb: 'Verb', particle: 'Particle', pronoun: 'Pronoun', adverb: 'Adverb', numeral: 'Number' };
  const nodes = [heading, el('span', 'pos', posLabels[entry.partOfSpeech] || entry.partOfSpeech)];
  if (token.usage) {
    const usage = el('div', 'usage');
    usage.append(el('p', '', `In this line: ${token.usage.en}`), ur(el('p', 'meaning-ur', token.usage.ur)));
    nodes.push(usage);
  }
  const meanings = el('div', 'meanings');
  meanings.append(el('p', 'meaning-en', entry.meanings.en), ur(el('p', 'meaning-ur', entry.meanings.ur)));
  nodes.push(meanings);
  const forms = el('dl', 'form-table');
  function form(label, value) {
    const row = el('div', 'form-row');
    row.append(el('dt', '', label), ar(el('dd', 'arabic', value)));
    forms.append(row);
  }
  if (entry.verb) {
    form('Māḍī · Past', entry.verb.madi);
    form('Muḍāriʿ · Present', entry.verb.mudari || '—');
    form('Maṣdar · Verbal noun', entry.verb.masdar.join('، ') || '—');
  } else if (entry.noun) {
    form('Singular', entry.noun.singular);
    form('Plural', entry.noun.plural.join('، ') || '—');
  } else { form('Dictionary form', entry.lemma); }
  nodes.push(forms);
  if (entry.root) {
    const root = el('div', 'root');
    root.append(el('span', '', 'Root · مادہ'), ar(el('span', 'arabic', entry.root)));
    nodes.push(root);
  }
  const note = entry.formNote || (!entry.root ? entry.rootNote : null);
  if (note) {
    nodes.push(el('p', 'card-note', note.en), ur(el('p', 'meaning-ur card-note', note.ur)));
  }
  const affixes = token.parts.filter(part => part.role !== 'stem' && vocabularyCardEntry(part, story));
  if (affixes.length) {
    const parts = el('div', 'parts');
    parts.append(el('h3', '', 'Attached words'));
    for (const part of affixes) {
      const affix = story.vocabulary[part.vocabularyId];
      const row = el('div', 'part');
      const description = el('div');
      description.append(el('div', '', affix.meanings.en), ur(el('div', 'urdu', affix.meanings.ur)));
      row.append(ar(el('span', 'arabic', affix.lemma)), description);
      parts.append(row);
    }
    nodes.push(parts);
  }
  content.replaceChildren(...nodes);
  dialog.showModal();
}

async function copyText(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      // Fallback for local non-HTTPS origins; must still be triggered by a click.
      const field = el('textarea');
      field.value = text; field.style.position = 'fixed'; field.style.opacity = '0';
      document.body.append(field); field.select();
      const copied = document.execCommand('copy'); field.remove();
      if (!copied) throw new Error('Clipboard unavailable');
    }
    notify('Line copied');
  } catch { notify('Copy wasn’t allowed. Select the line and copy it manually.'); }
}

function renderReader(story, requestedSection) {
  const section = story.sections.find(s => s.id === requestedSection) || story.sections[0];
  const sectionIndex = story.sections.indexOf(section);
  document.title = `${section.titleEnglish} · Qira’ah`;
  const back = el('a', 'back-link', 'All stories'); back.href = '#';
  const heading = el('div', 'reader-heading');
  const titleBlock = el('div');
  const title = ar(el('h1', 'arabic'));
  renderWords(title, story.titleTokens, '', story.wordLookup === 'google', story);
  titleBlock.append(el('div', 'eyebrow', `STORY ${String(story.number).padStart(2, '0')}`), title, el('p', '', `${story.titleEnglish} · ${story.subtitle}`));
  const wordNotes = Object.keys(story.vocabulary || {}).filter(vocabularyId => vocabularyCardEntry({ vocabularyId }, story)).length;
  heading.append(titleBlock, el('span', 'count', `${story.counts.sections} chapters · ${story.wordLookup === 'google' ? 'Google word lookup' : `${wordNotes} word notes`}`));
  if (story.publication?.status === 'partial') titleBlock.append(el('p', 'small', story.publication.label));
  const layout = el('div', 'reader-layout');
  const contents = el('nav', 'contents'); contents.setAttribute('aria-label', 'Story chapters');
  contents.append(el('p', 'contents-label', 'IN THIS STORY'));
  for (const s of story.sections) {
    const link = el('a', 'section-link'); link.href = linkFor(story.id, s.id);
    if (s.id === section.id) link.setAttribute('aria-current', 'true');
    link.append(el('span', 'section-no', String(s.number).padStart(2, '0')), el('span', '', s.titleEnglish));
    contents.append(link);
  }
  const column = el('div', 'reading-column');
  const mobile = el('label', 'mobile-select', 'Chapter');
  const select = el('select'); select.setAttribute('aria-label', 'Choose chapter');
  for (const s of story.sections) {
    const option = el('option', '', `${s.number}. ${s.titleEnglish}`); option.value = s.id; option.selected = s.id === section.id; select.append(option);
  }
  select.onchange = () => { location.hash = linkFor(story.id, select.value); };
  mobile.append(select);
  const tools = el('div', 'reader-tools');
  const key = el('div', 'tool-key');
  key.append(el('span', 'badge arabic', 'أَ'), el('span', '', 'Reveal vowels'), icon('copy'), el('span', '', 'Copy line'));
  tools.append(key, el('span', '', story.wordLookup === 'google' ? 'Tap a word → Google; select AI Mode there' : 'Tap a word to learn'));
  const page = el('article', 'reading-page'); page.setAttribute('aria-label', section.titleEnglish);
  const chapter = el('header', 'chapter-header');
  const chapterTitles = el('div');
  const chapterTitle = ar(el('h2', 'arabic'));
  renderWords(chapterTitle, section.titleTokens, '', story.wordLookup === 'google', story);
  chapterTitles.append(chapterTitle, el('p', '', section.titleEnglish));
  chapter.append(el('span', 'chapter-number', String(section.number).padStart(2, '0')), chapterTitles); page.append(chapter);
  for (const [index, line] of section.lines.entries()) {
    const row = el('div', `reading-line${line.kind === 'heading' ? ' passage-heading' : line.kind === 'footnote' ? ' passage-footnote' : ''}`);
    const controls = el('div', 'line-controls');
    const stateKey = `${story.id}:${line.id}`;
    const toggle = el('button', 'icon-button harakat-button', 'أَ'); toggle.type = 'button';
    toggle.setAttribute('aria-pressed', String(revealed.has(stateKey)));
    toggle.setAttribute('aria-label', `Show or hide vowels for line ${index + 1}`);
    toggle.title = 'Show / hide harakat';
    const copy = el('button', 'icon-button'); copy.type = 'button'; copy.append(icon('copy'));
    copy.title = 'Copy line'; copy.setAttribute('aria-label', `Copy line ${index + 1}`);
    copy.onclick = () => copyText(revealed.has(stateKey) ? line.vocalized : line.text);
    controls.append(el('span', 'line-number', String(index + 1).padStart(2, '0')), toggle, copy);
    const body = el('div', 'line-body');
    const text = ar(el('p', 'arabic line-text')); text.id = `${story.id}-${line.id}`;
    toggle.setAttribute('aria-controls', text.id);
    renderWords(text, line.tokens, line.leading, revealed.has(stateKey), story);
    toggle.onclick = () => {
      if (revealed.has(stateKey)) revealed.delete(stateKey); else revealed.add(stateKey);
      toggle.setAttribute('aria-pressed', String(revealed.has(stateKey)));
      renderWords(text, line.tokens, line.leading, revealed.has(stateKey), story);
    };
    body.append(text);
    if (line.references.length) {
      const references = el('div', 'references');
      for (const ref of line.references) {
        const link = el('a', '', `Quran ${ref.surah}:${ref.ayah}`);
        link.href = `https://quran.com/${Number(ref.surah)}/${Number(ref.ayah)}`;
        link.target = '_blank'; link.rel = 'noopener noreferrer'; references.append(link);
      }
      body.append(references);
    }
    row.append(controls, body); page.append(row);
  }
  const navigation = el('nav', 'chapter-navigation'); navigation.setAttribute('aria-label', 'Chapter navigation');
  const previous = el('a', 'secondary', sectionIndex ? 'Previous chapter' : 'Story library');
  previous.href = sectionIndex ? linkFor(story.id, story.sections[sectionIndex - 1].id) : '#';
  const next = el('a', 'secondary', sectionIndex < story.sections.length - 1 ? 'Next chapter' : 'Back to stories');
  next.href = sectionIndex < story.sections.length - 1 ? linkFor(story.id, story.sections[sectionIndex + 1].id) : '#';
  navigation.append(previous, el('span', 'small', `${section.number} of ${story.sections.length}`), next);
  const footer = el('p', 'reader-footer', 'The lighter text keeps a few marks to clarify the reading. Full vowels include grammatical endings; you may drop the final short vowel when pausing.');
  column.append(mobile, tools, page, navigation, footer); layout.append(contents, column);
  main.replaceChildren(back, heading, layout);
  try {
    localStorage.setItem(readingStorageKey, JSON.stringify({ storyId: story.id, sectionId: section.id }));
  } catch { /* Reading still works when browser storage is unavailable. */ }
}

function showError(message) {
  const box = el('div', 'error');
  box.setAttribute('role', 'alert');
  const retry = el('button', 'primary', 'Try again'); retry.type = 'button'; retry.onclick = route;
  const library = el('a', 'secondary', 'Story library'); library.href = '#';
  box.append(el('h1', '', 'Couldn’t open the stories'), el('p', '', message), retry, document.createTextNode(' '), library);
  main.replaceChildren(box);
}

async function route() {
  const request = ++routeRequest;
  if (dialog.open) dialog.close();
  try {
    if (!catalog) catalog = await loadJSON('data/stories.json');
    if (request !== routeRequest) return;
    const parts = location.hash.slice(1).split('/').map(decodeURIComponent);
    if (!parts[0]) { renderLibrary(); focusMain(); return; }
    if (parts[0] !== 'story') throw new Error('That page does not exist. Return to the story library.');
    const record = catalog.stories.find(s => s.id === parts[1]);
    if (!record) throw new Error('That story is not in the library yet.');
    let story = cache.get(record.id);
    if (!story) {
      main.replaceChildren(el('div', 'loading', 'Opening the story…'));
      story = prepareStory(await loadJSON(storyPath(record)));
      cache.set(record.id, story);
    }
    if (request !== routeRequest) return;
    renderReader(story, parts[2]); focusMain();
  } catch (error) {
    if (request !== routeRequest) return;
    showError(error.message.includes('story') || error.message.includes('page') ? error.message : 'Please check your connection and try again.');
  }
}

const closeButton = document.querySelector('.close-card');
closeButton.append(icon('close')); closeButton.onclick = () => dialog.close();
document.querySelector('.skip').onclick = event => {
  event.preventDefault();
  focusMain();
};
dialog.addEventListener('click', event => {
  const bounds = dialog.getBoundingClientRect();
  if (event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) dialog.close();
});
window.addEventListener('hashchange', route);
route();
