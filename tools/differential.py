#!/usr/bin/env python3
"""Write tests/differential_tests.nv: seeded sitemaps written by this
package and read back by Python's xml.etree.ElementTree.

The script draws URL sets and indexes from a seeded generator, with
`loc`s holding the five characters the protocol's entity table names,
non-ASCII text, every `lastmod` shape, every `changefreq` and priorities
across the range, and four layouts of the writer's options.  It has
this package write each one, through a temporary suite it runs with
`novo test`, and reads the output with ElementTree.  The script stops
unless ElementTree reads back every value that went in: the root
element and its namespace, each `loc`, `lastmod`, `changefreq` and
`priority`, and no element for an unset one.

The suite it writes pins each verified document: the writer must
produce that text again, and both readers must read it back to the same
values.

Run from the package root:
    python3 tools/differential.py
The output is passed through `novo fmt`.
"""
import os
import random
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

SEED = 20260927
URLSETS = 30
INDEXES = 10
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
FREQS = ['', 'always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never']
PATH_CHARS = list('abcxyz0123456789-_/.~') + ['&', "'", '"', '<', '>', 'é', '%C3%BC', '?q=1', '#top', ' ']
OPTIONS = [('sitemapwrite.options()', 2, True, True),
           ('sitemapwrite.compact()', 0, False, True),
           ('SitemapWriteOptions { indent: 3, declaration: true, namespace: true }', 3, True, True),
           ('sitemapwrite.without_namespace(sitemapwrite.options())', 2, True, False)]


def gen_loc(r):
    host = r.choice(['example.org', 'www.example.com', 'shop.example.net:8080'])
    path = ''.join(r.choice(PATH_CHARS) for _ in range(r.randint(0, 12)))
    return r.choice(['https', 'http']) + '://' + host + '/' + path


def gen_lastmod(r):
    return r.choice(['', '', '2005', '2005-01', '2005-01-01', '2004-12-23T18:00+00:00',
                     '2004-12-23T18:00:15+00:00', '2026-09-27T09:41:00.5Z', '1999-12-31T23:59:59-05:30'])


def priority_text(milli):
    if milli < 0:
        return ''
    frac = ('%03d' % (milli % 1000)).rstrip('0') or '0'
    return '%d.%s' % (milli // 1000, frac)


def nv(text):
    out = []
    for ch in text:
        if ch == '\\':
            out.append('\\\\')
        elif ch == '"':
            out.append('\\"')
        elif ch == '$':
            out.append('\\$')
        elif ch == '\n':
            out.append('\\n')
        else:
            out.append(ch)
    return '"' + ''.join(out) + '"'


def url_expr(u):
    e = 'sitemapurl.url(%s)' % nv(u['loc'])
    if u['lastmod']:
        e = 'sitemapurl.with_lastmod(%s, %s)' % (e, nv(u['lastmod']))
    if u['freq']:
        e = 'sitemapurl.with_changefreq(%s, Sitemap%s)' % (e, u['freq'].capitalize())
    if u['milli'] >= 0:
        e = 'sitemapurl.with_priority(%s, %d)' % (e, u['milli'])
    return e


def ref_expr(x):
    return 'sitemapdoc.ref_with_lastmod(sitemapdoc.sitemap_ref(%s), %s)' % (nv(x['loc']), nv(x['lastmod']))


def cases():
    r = random.Random(SEED)
    out = []
    for _ in range(URLSETS):
        urls = [{'loc': gen_loc(r), 'lastmod': gen_lastmod(r), 'freq': r.choice(FREQS),
                 'milli': r.choice([-1, -1, 0, 1000, 500, r.randint(0, 1000)])}
                for _ in range(r.randint(0, 6))]
        out.append(('urlset', urls, r.choice(OPTIONS)))
    for _ in range(INDEXES):
        refs = [{'loc': gen_loc(r) + '.xml', 'lastmod': gen_lastmod(r)} for _ in range(r.randint(0, 4))]
        out.append(('sitemapindex', refs, r.choice(OPTIONS)))
    return out


def value_expr(kind, items):
    if kind == 'urlset':
        return 'sitemapurl.urlset([%s])' % ', '.join(url_expr(u) for u in items)
    return 'sitemapdoc.index([%s])' % ', '.join(ref_expr(x) for x in items)


def write_expr(kind, items, opt):
    if kind == 'urlset':
        return 'text_of(sitemapwrite.write_urlset([], %s, %s))' % (value_expr(kind, items), opt[0])
    return 'text_of(sitemapwrite.write_index([], %s, %s))' % (value_expr(kind, items), opt[0])


HEADER = '''use std.test
use std.list
use std.bytes
use sitemapdoc
use sitemapread
use sitemapurl
use sitemapwrite

fn text_of(r: Result<[u8], SitemapFault>) -> Str
    match r
        Ok(b)  => bytes.byte_list_to_str(list.map(b, int_of))
        Err(f) => f.message()

fn int_of(b: u8) -> Int
    b as Int
'''


def dump(all_cases, here):
    lines = [HEADER, '@test', 'fn test_dump() [io]']
    for k, (kind, items, opt) in enumerate(all_cases):
        lines.append('    println("<<<%d>>>")' % k)
        lines.append('    print(%s)' % write_expr(kind, items, opt))
        lines.append('    println("<<<end>>>")')
    path = os.path.join(here, 'tests', 'zz_etree_dump_tests.nv')
    with open(path, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    try:
        run = subprocess.run([os.environ.get('NOVO', 'novo'), 'test', path], cwd=here,
                             capture_output=True, text=True)
    finally:
        os.remove(path)
    docs = {}
    for m in re.finditer(r'<<<(\d+)>>>\n(.*?)<<<end>>>', run.stdout, re.S):
        docs[int(m.group(1))] = m.group(2)
    if len(docs) != len(all_cases):
        sys.exit('the dump run answered %d of %d documents:\n%s' % (len(docs), len(all_cases), run.stdout + run.stderr))
    return docs


def check(kind, items, opt, text):
    _, indent, declaration, namespace = opt
    assert text.startswith('<?xml') == declaration, text
    root = ET.fromstring(text.encode())
    q = '{%s}' % NS if namespace else ''
    assert root.tag == q + kind, (root.tag, text)
    entry = 'url' if kind == 'urlset' else 'sitemap'
    got = list(root)
    assert len(got) == len(items), text
    for el, item in zip(got, items):
        assert el.tag == q + entry
        assert el.find(q + 'loc').text == item['loc'], (el.find(q + 'loc').text, item['loc'])
        lm = el.find(q + 'lastmod')
        assert (lm.text if lm is not None else '') == item['lastmod']
        if kind == 'urlset':
            cf = el.find(q + 'changefreq')
            assert (cf.text if cf is not None else '') == item['freq']
            pr = el.find(q + 'priority')
            assert (pr.text if pr is not None else '') == priority_text(item['milli'])
            if pr is not None:
                assert int(round(float(pr.text) * 1000)) == item['milli']
    if indent == 0:
        assert '\n' not in text


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    all_cases = cases()
    docs = dump(all_cases, here)
    for k, (kind, items, opt) in enumerate(all_cases):
        check(kind, items, opt, docs[k])
    lines = ['// differential_tests.nv — seeded sitemaps this package writes, as',
             '// Python\'s xml.etree.ElementTree read them.',
             '//',
             '// Written by tools/differential.py; do not edit by hand.  Seed %d,' % SEED,
             '// %d URL sets and %d indexes.  ElementTree read every value back from' % (URLSETS, INDEXES),
             '// each document below before it was written here.  The writer must',
             '// produce the same text again, and both readers must read it back to',
             '// the same number of entries with nothing skipped.',
             '']
    lines += HEADER.split('\n')
    for k, (kind, items, opt) in enumerate(all_cases):
        lines += ['@test',
                  'fn test_case_%02d() [io]' % k,
                  '    let text = %s' % nv(docs[k]),
                  '    test.assert_eq(%s, text)' % write_expr(kind, items, opt),
                  '    match sitemapread.read(text)',
                  '        Err(f) => test.fail(f.message())',
                  '        Ok(doc) =>',
                  '            test.assert_eq(list.len(doc.%s), %d)' % (
                      'urls.urls' if kind == 'urlset' else 'index.refs', len(items)),
                  '            test.assert_eq(sitemapdoc.kind_name(doc.kind), %s)' % nv(kind),
                  '    match sitemapread.read_lenient(text)',
                  '        Err(f) => test.fail(f.message())',
                  '        Ok(doc) => test.assert_eq(list.len(doc.skipped), 0)',
                  '']
    out = os.path.join(here, 'tests', 'differential_tests.nv')
    with open(out, 'w') as fh:
        fh.write('\n'.join(lines))
    subprocess.run([os.environ.get('NOVO', 'novo'), 'fmt', out], check=True, capture_output=True)
    print('wrote %s: %d documents, each read back by ElementTree' % (out, len(all_cases)))


if __name__ == '__main__':
    main()
