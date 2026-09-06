# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Raised the minimum Scrapy version to 2.7 (async downloader middlewares,
  `get_retry_request`) and set sensible lower bounds for `itemadapter` and
  `twisted`
- Dropped the unused direct `jmespath` and `w3lib` dependencies (both still
  come in transitively via Scrapy)
- Removed the obsolete `v0/` source tree (pre-1.0 `setup.py` package)

### Added

- Test suite covering all modules (100% coverage)

### Fixed

- `BlurHashPipeline.from_crawler` now actually checks that the optional
  `blurhash` extra is installed before enabling the pipeline (the previous
  `find_spec` call was a no-op and never detected missing libraries)
- `DelayedRetryMiddleware` and `NicerAutoThrottle` now correctly raise
  `NotConfigured` / fall back when `*_HTTP_CODES` contain non-numeric values
  (the `ValueError` guard was previously dead code due to a lazy generator)

## [1.1.0] - 2025-10-16

### Changed

- Added support for Py3.14; dropped Py3.9
- Rewrite `DelayedRetryMiddleware` to use async instead of Twisted Deferred

### Added

- Added `AuthHeaderMiddleware` from [board-game-scraper](https://gitlab.com/recommend.games/board-game-scraper)

## [1.0.2] - 2024-11-18

### Fixed

- Better imports

## [1.0.1] - 2024-11-17

### Fixed

- Fixed a bug in `DelayedRetryMiddleware` which resulted in problems with the Twisted reactor

## [1.0.0] - 2024-11-17

### Added

- Initial release as v1. Ported over the following classes:
  - `BlurHashPipeline`
  - `DelayedRetryMiddleware`
  - `LoopingExtension`
  - `NicerAutoThrottle`
  - `QuietLogFormatter`

[Unreleased]: https://github.com/MarkusShepherd/scrapy-extensions/compare/1.1.0...master
[1.1.0]: https://github.com/MarkusShepherd/scrapy-extensions/compare/1.0.2...1.1.0
[1.0.2]: https://github.com/MarkusShepherd/scrapy-extensions/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/MarkusShepherd/scrapy-extensions/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/MarkusShepherd/scrapy-extensions/tree/1.0.0
