# Changelog

All notable changes to sitemap-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## 0.1.0 — 2026-09-27

The first implementation of the interface published as 0.0.1.

### Changed

These change the interface's declarations, so a program written against
0.0.x may need the edits named here.

- The writing functions take their buffer as `var out: [u8]`, since a
  list is a reference type that is written through a `var` name
  (SPEC section 4).  A caller passing `[]` changes nothing.
- `SitemapWriteOptions` is a `@value` struct.  A changed option is a
  new literal.
- `sitemapwrite.index_byte_length` is new: the size of an index under
  given options, which `sitemapdoc.check_index` measures by.
- `sitemaperror.is_writer_fault` is true for `SitemapUnwritable` alone.
  `SitemapBadLoc` comes from the reader and the writer both.
- The signatures spell the package's own types without a module name,
  `SitemapSet` rather than `sitemapurl.SitemapSet`.  They are the same
  types.
- The dependency is xml-nv `^0.1.0`, and the toolchain floor is 0.13.0.

### Behaviour the interface left open

- The writer escapes the five characters of the protocol's entity
  table, `&`, `'`, `"`, `>` and `<`, and refuses a character xml-nv's
  `is_xml_char` refuses, with its offset and code point.
- The layout is one element per line, indented `indent` spaces per
  level, with a line feed after each; an indent of `0` writes one line.
  The protocol's samples, written with an indent of three, come back as
  the protocol prints them.
- `sitemapdoc.check` measures the size under `sitemapwrite.options()`,
  and its `files_needed` is the number of files `split` makes.  `split`
  fills each file up to both limits in order, and gives a URL too large
  for a file on its own a file to itself.
- `sitemapdoc.check_prefix` takes the prefix as the sitemap's address up
  to and including its last `/`.
- `sitemapurl.is_datetime_shaped` accepts the six forms of the W3C
  Datetime note, `YYYY` and `YYYY-MM` included, and checks each number
  against its range.
- `sitemapurl.priority_of` accepts `1`, `.5` and `1.000`, and refuses
  anything above 1.0.  `priority_text` answers `""` for a value outside
  0 to 1000.
- `sitemapurl.loc_problem` answers `"is empty"`, `"is longer than 2,048
  characters"`, `"is not an absolute URL"` or `"has no host"`.
- The readers tolerate a prefix the file never declared, and match
  elements by their local name.  Text around a value is trimmed.

## [0.0.1] — 2026-09-17

**The interface, published before anyone implements it.** Every public
type and function carries its full signature, its effect row and its
doc comment; every body is `todo()`; the release is recorded
`implemented = false`.

### Added

- `sitemapurl` — one `url` element with its three optional children
  typed. An absent element is distinguishable from a present one with a
  low value, so the writer emits neither a default `priority` nor a
  default `changefreq`. A priority is an integer count of thousandths,
  because the element is a decimal in the file and a float does not
  round-trip. A `lastmod` is the text it will carry, because a package
  with no effects holds no calendar.
- `sitemapdoc` — the 50,000-entry and 50 MB limits as a `SitemapReport`
  rather than a `Result`. A site with more pages than fit has a sitemap
  to split, not a sitemap that is broken, and a `Result` would make the
  ordinary case look like a failure. `split` keeps the order and always
  answers a list, and `check_prefix` applies the cross-submission rule
  against the address the file will be published at.
- `sitemapread` — two readers rather than a mode flag: `read` refuses
  every fault, for a site generator reading back its own output, and
  `read_lenient` drops a broken entry and records it, for a crawler
  reading somebody else's.
- `sitemapwrite` — the document appended to a buffer the caller owns,
  with the byte count available per entry so a split can be planned
  without writing anything.
- `sitemaperror` — eight faults, with `is_entry_fault` dividing the
  ones a lenient reader survives from the two about the whole document,
  and `is_writer_fault` dividing this program's bug from somebody
  else's file.

### Known

- `novo test` is red, and that is the release's expected state: every
  assertion in the API suite reaches `not implemented:
  sitemap-nv.<module>.<fn>`.
- **xml-nv is itself an interface at 0.0.2.** This package cannot be
  implemented before its parser and writer have bodies. The escaping is
  the reason it is a dependency: an unescaped ampersand in a `loc` is
  the most common defect in a hand-written sitemap, and xml-nv already
  refuses what it cannot escape.
