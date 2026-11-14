# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases up to v0.5 were made upstream by Rémi Duraffort
(https://github.com/ivoire/Artifactorial). From v0.6.0 on, releases are made from
this fork, https://github.com/igaw/Artifactorial.

## [Unreleased]

### Changed

- Dependencies are now pinned, including transitive ones: `requirements.in`
  and `requirements-dev.in` list the direct dependencies, and `make lock`
  compiles them into `requirements.txt` and `requirements-dev.txt`.
  Dependabot keeps both up to date.
- The Docker image installs from `requirements.txt` into a venv, so it uses
  the same pinned versions as CI. gunicorn now comes from PyPI (27.x)
  instead of Debian (23.x).
- The Docker base image is pinned by digest, so Dependabot proposes Debian
  security rebuilds.
- Pull requests now build and smoke-test the Docker image.

## [0.6.0] - 2026-11-14

First release from the maintained fork, and the first since v0.5 (2017).

### Upgrade notes

- **Python 3.11+ and Django 5.2 LTS are now required.** Django 2.2 and
  Python < 3.11 are no longer supported.
- **The Docker deployment now really uses PostgreSQL.** Before this release,
  `share/settings.py` defined no `DATABASES`, so the container silently used
  an SQLite file in its writable layer, which was lost every time the
  container was recreated. Nothing persisted there, so there is nothing to
  migrate, but expect to create the admin account and tokens again.
- **The PostgreSQL image is now 18 (was 12), and the `db` volume is mounted at
  `/var/lib/postgresql`** (was `/var/lib/postgresql/data`), which the 18+
  image requires. Any old `artifactorial-db` volume never held real data (see
  above). Remove it with `docker volume rm artifactorial-db` before
  upgrading. The `artifactorial-data` volume (the uploaded artifacts) is
  unchanged.
- **The container image moved to `ghcr.io/igaw/artifactorial`.** The old
  `hub.lavasoftware.org/ivoire/artifactorial` registry is offline. Images are
  published for `linux/amd64` and `linux/arm64`, with build provenance
  attestations.
- **`DEBUG=False` in the environment now really turns debug off.** It used to
  be read as the truthy string `"False"`.

### Added

- PostgreSQL support in the Docker settings, configured through
  `POSTGRES_{DB,USER,PASSWORD,HOST,PORT}`.
- GitHub Actions: lint (black, ruff) and tests on Python 3.11–3.13 for every
  push and pull request. Tagged releases publish multi-arch images to GHCR
  and a GitHub Release.
- `Artifactorial.__version__`, shown in the navbar and linked to the release.
- `make lint`, `make format` and `make test`, plus `requirements-dev.txt`.

### Changed

- Migrated to Django 5.2 LTS and Python 3.11–3.13.
- Docker base image updated from Debian buster to trixie.
- Code reformatted with black and checked with ruff.
- Re-licensed to MIT (done upstream in 2020, unreleased until now).

### Fixed

- Deleting an artifact now removes its file from storage. The `post_delete`
  signal handler was never connected, so deleted artifacts' files stayed on
  disk.
- Directory listings no longer cut off the first character of every file name
  in non-root directories.
- Upload responses no longer return URLs containing a double slash.

### Removed

- The GitLab CI configuration, which depended on infrastructure that no
  longer exists.

[Unreleased]: https://github.com/igaw/Artifactorial/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/igaw/Artifactorial/compare/v0.5...v0.6.0
