# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Added support for Py3.14; dropped Py3.9

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

[Unreleased]: https://github.com/MarkusShepherd/scrapy-extensions/compare/1.0.2...master
[1.0.2]: https://github.com/MarkusShepherd/scrapy-extensions/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/MarkusShepherd/scrapy-extensions/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/MarkusShepherd/scrapy-extensions/tree/1.0.0
