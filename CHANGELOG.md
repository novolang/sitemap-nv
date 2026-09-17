# Changelog

All notable changes to sitemap-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

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
- **xml-nv is itself an interface at 0.0.1.** This package cannot be
  implemented before its parser and writer have bodies. The escaping is
  the reason it is a dependency: an unescaped ampersand in a `loc` is
  the most common defect in a hand-written sitemap, and xml-nv already
  refuses what it cannot escape.
