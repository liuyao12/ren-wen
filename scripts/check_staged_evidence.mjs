/** Verify that evidence links resolve in the files that will be published. */
import assert from 'node:assert/strict';
import {readFileSync, readdirSync, statSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

assert(process.argv[2], 'Usage: node check_staged_evidence.mjs <staged site>');
const root = resolve(process.argv[2]);
const json = path => JSON.parse(readFileSync(join(root, path), 'utf8'));
const {sourcePassageURL} = await import(pathToFileURL(join(root, 'assets/corpus-reader.js')));
const {nativeTableURL} = await import(pathToFileURL(join(root, 'assets/native-table-links.js')));
const chapterPaths = new Map();
for (const work of json('data/corpus/works.json').works) {
    if (!work.catalog_path) continue;
    for (const chapter of json(work.catalog_path).chapters) {
        if (chapter.path) chapterPaths.set(chapter.chapter_id, chapter.path);
    }
}
const chapters = new Map();
const tables = new Map(json('data/historical-tables/index.json').tables.map(table => {
    const source = json(table.path);
    const cells = source.fragments.flatMap(fragment => fragment.rows.flatMap(row => row.cells));
    return [table.id, new Set(cells.map(cell => cell.id))];
}));
for (const page of ['reader.html', 'shiji.html']) assert(statSync(join(root, page)).isFile(), page);

function* evidenceIn(node) {
    if (!node || typeof node !== 'object') return;
    if (Array.isArray(node)) {
        for (const item of node) yield* evidenceIn(item);
        return;
    }
    for (const ref of Array.isArray(node.evidence) ? node.evidence : []) {
        if (ref?.chapter_id || ref?.table_id) yield ref;
    }
    for (const [field, value] of Object.entries(node)) {
        if (field !== 'evidence' && field !== 'sources') yield* evidenceIn(value);
    }
}

function* profileCitations(profile) {
    yield* evidenceIn(profile);
    yield* (profile.occurrences || []);
    yield* (profile.person_references || []);
    for (const ref of profile.table_occurrences || []) {
        yield {...ref, kind: 'table_cell', table_cell_id: ref.cell_id};
    }
    const personIDs = new Set([profile.id, ...(profile.person_ids || [])]);
    for (const item of profile.source_reading_cases || []) {
        if (!['witness_collation', 'primary_source_comparison'].includes(item.kind)
                || !personIDs.has(item.person_id) || !item.paragraph_id
                || ![item.source_quote, item.reading, item.reference].every(s => typeof s === 'string' && s.trim())) continue;
        const source = (profile.sources || []).find(s => s.source_id === item.source_id && s.chapter_id === item.chapter_id);
        if (source) yield {...source, paragraph_id: item.paragraph_id, quote: item.source_quote};
    }
}

function checkParagraph(ref) {
    const path = chapterPaths.get(ref.chapter_id);
    assert(path, 'Chapter absent from staged reader catalog');
    if (!chapters.has(ref.chapter_id)) {
        const {id, work_id, book_id, source_id, source, paragraphs} = json(path);
        assert.equal(id, ref.chapter_id, 'Catalog points to a different chapter');
        assert.match(source.permalink, /^https?:\/\//, 'External witness link missing');
        const passages = new Map(paragraphs.map(p => [p.id, p.text]));
        const mentions = new Map(paragraphs.flatMap(p => p.mentions.map(m => [m.id, p.id])));
        chapters.set(id, {work_id, book_id, source_id, passages, mentions});
    }
    const chapter = chapters.get(ref.chapter_id);
    for (const key of ['work_id', 'book_id', 'source_id']) {
        if (ref[key]) assert.equal(ref[key], chapter[key], `Incorrect ${key}`);
    }
    const href = sourcePassageURL(ref);
    assert(href, 'No link generated for chapter evidence');
    const [page, fragment] = href.split('#');
    const route = new URLSearchParams(fragment);
    if (chapter.work_id === 'w-shiji') {
        assert.equal(page, 'shiji.html', 'Shiji evidence opens the wrong reader');
        assert.equal(route.get('chapter'), String(Number(/shiji-(\d{3})/.exec(ref.chapter_id)?.[1])));
    } else {
        assert.equal(page, 'reader.html', 'Evidence opens the wrong reader');
        assert.equal(route.get('work'), chapter.work_id);
        assert.equal(route.get('chapter'), ref.chapter_id);
        if (route.has('book')) assert.equal(route.get('book'), chapter.book_id);
        if (ref.mention_id) assert.equal(route.get('mention'), ref.mention_id);
    }
    if (ref.paragraph_id) {
        assert.equal(route.get('passage'), ref.paragraph_id);
        const paragraph = chapter.passages.get(ref.paragraph_id);
        assert(typeof paragraph === 'string', 'Paragraph absent from staged chapter');
        if (ref.quote) assert(paragraph.includes(ref.quote), 'Quote absent from cited paragraph');
    }
    if (ref.mention_id) {
        const passage = chapter.mentions.get(ref.mention_id);
        assert(passage && (!ref.paragraph_id || passage === ref.paragraph_id), 'Mention absent at citation');
    }
}

function checkTable(ref) {
    const locations = ref.subject_table_cell_id ? [ref.table_cell_id, ref.subject_table_cell_id] : [ref.table_cell_id];
    for (const cell of locations) {
        const href = nativeTableURL({...ref, cell_id: cell});
        assert(href, 'No link generated for table evidence');
        const route = new URLSearchParams(href.split('#')[1]);
        assert.equal(route.get('cell'), cell);
        assert(tables.get(ref.table_id)?.has(cell), 'Cell absent from staged table');
    }
}

const profiles = 'data/corpus/profiles';
let people = 0;
let references = 0;
let problems = 0;
for (const file of readdirSync(join(root, profiles))) {
    if (!file.endsWith('.json') || file === 'index.json') continue;
    people++;
    const profile = json(join(profiles, file));
    for (const ref of profileCitations(profile)) {
        references++;
        try {
            if (ref.kind === 'table_cell') checkTable(ref);
            else checkParagraph(ref);
        } catch (error) {
            if (++problems <= 20) {
                const locus = ref.paragraph_id || ref.table_cell_id || ref.chapter_id;
                console.error(`${profile.id} ${locus} ${error.message}`);
            }
        }
    }
}
assert(people && references, 'No staged person evidence found');
assert.equal(problems, 0, 'Staged person evidence has unresolved links');
console.log(`已核對 ${people} 份人物資料中的 ${references} 筆引文連結。`);
