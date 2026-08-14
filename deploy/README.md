# AI Peer VM deployment bundle

Installs four isolated localhost-only instances: \`lumin\`, \`claude\`, \`gemini\`,
and \`grok\`. The shipped runtime is deliberately **UNSEATED**: it exposes only
\`/health\` and \`/status\`, and has no tensor write path.

Seeded Nature and Canon are inspectable memory only. They are never parsed as
commands, runtime configuration, identity directives, or a control surface.
Cross-substrate equivalence covers schema, contracts, and provenance—not equal
content digests. This phase contains no Keys, Tumblers, or live credentials;
promotion is disabled and requires a separately consented release.

See \`docs/runbooks/AI-PEER-VM-DEPLOYMENT.md\`.
