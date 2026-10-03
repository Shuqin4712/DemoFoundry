---
name: demofoundry
description: Placeholder for the DemoFoundry engine, init command and environment check. Not usable yet.
---

# DemoFoundry

Placeholder (workflow lands in P4). The shared engine is in [`engine/`](engine/README.md); this skill will also hold the technique cards and the `init` command that creates `demofoundry/` in a product repo.

The `demofoundry-mold` and `demofoundry-episode` skills reference this folder as `../demofoundry/`, so install all three together:

    npx skills add Shuqin4712/DemoFoundry --skill '*'
