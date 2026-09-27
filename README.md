# sitemap-nv

A sitemap is an XML file listing the pages of a site, so that a search
engine knows what is there without following every link. The format is
the [sitemaps.org protocol, version 0.9](https://www.sitemaps.org/protocol.html),
which Google, Bing and Yandex jointly publish and all of them read.
This package reads such a file into typed values and writes one back.

## What a sitemap is

A sitemap is a `urlset` element holding one `url` element per page.
Each `url` has a required `loc` and three optional children.

| Element | Meaning |
| --- | --- |
| `loc` | The page's absolute URL, at most 2,048 characters. Required |
| `lastmod` | When the page last changed, as a W3C Datetime |
| `changefreq` | How often it is likely to change |
| `priority` | How important it is relative to other pages on the same site, from 0.0 to 1.0, default 0.5 |

`changefreq` has exactly seven values: `always`, `hourly`, `daily`,
`weekly`, `monthly`, `yearly`, `never`. All three children are hints. A
search engine may crawl on whatever schedule it likes, and `priority`
compares pages within one site and never across sites.

One file may hold at most **50,000 URLs** and must be at most **50 MB**
uncompressed. A site with more pages than that writes several files and
a **sitemap index**: a `sitemapindex` element holding one `sitemap`
element per file, each with its own `loc` and optional `lastmod`. An
index is capped the same way, and an index may not name another index.

A sitemap may only name URLs that begin with the same path as the
sitemap file itself. A file at `https://example.org/shop/sitemap.xml`
may list `https://example.org/shop/…` and nothing else. A search engine
ignores the URLs that break that rule, without saying so.

## Install

```
novo pkg add sitemap-nv
```

## Example

```novo
use sitemapdoc
use sitemapurl
use sitemapwrite

fn main() [io]
    // Two pages, one of them with all three optional elements.
    let home = sitemapurl.with_priority(
                   sitemapurl.with_changefreq(
                       sitemapurl.with_lastmod(sitemapurl.url("https://example.org/"),
                                               "2026-09-17"),
                       SitemapDaily),
                   1000)
    let about = sitemapurl.url("https://example.org/about")
    let set = sitemapurl.urlset([home, about])

    // How the document measures against the protocol's two limits.
    // Being over one is a report, not an error: a large site has a
    // sitemap to split, not a sitemap that is broken.
    let report = sitemapdoc.check(set, sitemapdoc.limits())
    println("${report.entries} URLs, ${report.bytes} bytes, ${report.files_needed} file(s)")

    // Write it. The answer is an error when a `loc` is not an absolute
    // URL or holds a character XML cannot carry.
    match sitemapwrite.to_str(set, sitemapwrite.options())
        Ok(document) => println(document)
        Err(fault)   => println("cannot write the sitemap: ${fault.message()}")
```

Build and test with `novo pkg build` and `novo test tests/`.

## What the package contains

| Module | Contents |
| --- | --- |
| `sitemaperror` | Why a sitemap is refused, whether the fault is in a file or in a document being built, and whether a reader could carry on past it. |
| `sitemapurl` | One `url` element with its three optional children typed, and the `urlset` around them. |
| `sitemapdoc` | The index form, the two limits, the report a document measures to, and splitting. |
| `sitemapread` | Reading a file, strictly or leniently, into those values. |
| `sitemapwrite` | Writing them back into a buffer the caller owns, and the byte count a split is planned with. |

## How to choose an entry point

**`sitemapread.read` refuses every fault.** A site generator reading
back its own output wants it: a bad `priority` there is its own bug.

**`sitemapread.read_lenient` drops a broken entry and records it.** A
crawler reading somebody else's sitemap wants it: one bad entry in
fifty thousand should not cost the other 49,999.

**`sitemapwrite.to_str` produces the whole document.**
`sitemapwrite.write_urlset` appends to a buffer the caller owns, and
the three streaming calls write a document one URL at a time. A sitemap
at the limit is fifty megabytes, which is why all three exist.

**`sitemapdoc.check` measures a document against the limits, and
`sitemapdoc.split` divides one that is over.** `sitemapdoc.index_for`
then names the files that came out.

## The rules a user needs

1. **An absent element is not a default.** `changefreq` absent is
   `SitemapUnstated` and `priority` absent is `-1`, and the writer
   emits neither. A writer that wrote `0.5` for every URL would be
   telling a search engine that the site had ranked its pages when it
   had not.
2. **A priority is an integer count of thousandths.** `500` is `0.5`.
   The element is a decimal in the file, which is a float, and a float
   does not round-trip. A value outside 0 to 1000 is clamped rather
   than refused.
3. **A `lastmod` is text.** It is a W3C Datetime, and this package
   performs no input or output, so it holds no calendar and reads no
   clock. `sitemapurl.is_datetime_shaped` checks the shape only:
   `2026-02-30` is shaped and is not a day.
4. **`changefreq` has seven values and an eighth is a fault.**
   `sitemapurl.changefreq_named` answers `None` for one, so a site
   generator finds its own typo instead of having it silently dropped.
5. **Exceeding a limit is a report, not an error.**
   `sitemapdoc.check` answers how far over a document is and how many
   files it would take. A `Result` would make a large site look like a
   failure.
6. **The byte count depends on the write options.** A document's size
   changes with indentation and with how much escaping each URL needs.
   `sitemapdoc.check` and `sitemapdoc.split` measure the document as
   `sitemapwrite.options()` writes it, and `sitemapwrite.byte_length`
   measures it under any options.
7. **`sitemapdoc.split` always answers a list.** A conforming set
   answers a list of one, so a caller writes the same loop either way,
   and the order of the URLs is kept across the files.
8. **An index may not name another index**, so an index over 50,000
   entries means the sitemaps have to be larger rather than more
   numerous. `sitemapdoc.check_index` is where that shows.
9. **The cross-submission rule is checked against the file's own
   address.** `sitemapdoc.check_prefix` takes where the sitemap will be
   published and answers the URLs that break it, because a search
   engine drops those without saying so.
10. **The protocol's five entities are escaped.** `&`, `'`, `"`, `>`
    and `<` are written `&amp;`, `&apos;`, `&quot;`, `&gt;` and `&lt;`.
    A URL with a query string has an ampersand, and an unescaped one is
    a file that looks right and that no parser will read.
11. **A character XML 1.0 section 2.2 does not admit is refused**, with
    its offset, rather than written into a file a search engine will
    reject without explanation.
12. **The namespace is tolerated on the way in and written on the way
    out.** A file with the 0.9 namespace, with an older one, or with
    none at all reads; a file this package writes declares the 0.9 one.
13. **Elements from the news, image and video extensions are ignored,
    not refused.** So are comments, unknown attributes and a prefix the
    file never declared, and elements are matched by their local name.
    A reader that insisted would refuse files every search engine
    accepts.
14. **Nothing is fetched.** A sitemap index names other files and this
    package never follows one. A sitemap is written by whoever owns the
    site, and its `loc` elements are not addresses a library should
    visit on a caller's behalf.

## What is not included

- **Fetching anything**, including the files a sitemap index names. See
  rule 14.
- **Gzip.** A sitemap is often served compressed, and the 50 MB limit
  is on the uncompressed file. Compressing is
  [flate-nv](https://novo-lang.org/packages/flate-nv)'s.
- **The news, image and video extensions.** Each is its own namespace
  with its own elements, and each is a package-sized piece of work.
  They are read past rather than refused.
- **The plain-text and RSS sitemap formats.** The protocol admits a
  file of one URL per line and an RSS or Atom feed as a sitemap. Both
  are other formats that happen to be accepted in the same place.
- **`robots.txt`.** The `Sitemap:` directive that points at a sitemap
  is read by [robots-nv](https://novo-lang.org/packages/robots-nv).
- **Validating a URL beyond its shape.** `sitemapurl.loc_problem`
  checks that a `loc` is absolute and within the length limit. Parsing
  one properly is
  [url-nv](https://novo-lang.org/packages/url-nv)'s.

## Related packages

- [xml-nv](https://novo-lang.org/packages/xml-nv) is the XML
  underneath, in both directions. This package depends on it.
- [robots-nv](https://novo-lang.org/packages/robots-nv) reads the file
  that points a crawler at a sitemap, and decides what it may fetch.
- [url-nv](https://novo-lang.org/packages/url-nv) parses and normalises
  the URLs a sitemap lists.

## Tests

```bash
novo test tests/protocol_tests.nv       #  4 tests: the protocol's own samples
novo test tests/differential_tests.nv   # 40 tests: seeded documents ElementTree read back
novo test tests/sitemapurl_tests.nv     #  6 tests: the three optional children, typed
novo test tests/sitemapdoc_tests.nv     #  6 tests: the limits, the split and the index
novo test tests/sitemapread_tests.nv    #  5 tests: strict and lenient reading
novo test tests/sitemapwrite_tests.nv   #  7 tests: what is left out, and what is refused
novo test tests/sitemaperror_tests.nv   #  4 tests: which faults a reader survives
novo test tests/corners_tests.nv        #  7 tests: every refusal and every shape
bash tests/coverage.sh                  # line coverage over src/
```

The normative source is the sitemaps.org protocol version 0.9, and XML
1.0 section 2.2 for the characters a document may carry.
`tests/protocol_tests.nv` holds the protocol page's three samples and
its escaping example: each sample is read to its values and written
back, with a three-space indent, as the page prints it.

The second oracle is Python's `xml.etree.ElementTree`.
`tools/differential.py` draws seeded URL sets and indexes, with every
character the entity table names in their URLs, every `lastmod` shape,
and four layouts, has this package write each, and stops unless
ElementTree reads every value back. It writes the verified documents
into `tests/differential_tests.nv`, where the writer must produce them
again and both readers must read them back.

## Licence

Apache-2.0. See `LICENSE`.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
