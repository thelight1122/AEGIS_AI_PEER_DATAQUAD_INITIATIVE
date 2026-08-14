# AI Peer VM deployment bundle

Installs four isolated localhost-only instances: \`lumin\`, \`claude\`, \`gemini\`,
and \`grok\`. The shipped runtime is deliberately **UNSEATED**: it exposes only
\`/health\` and \`/status\`, and has no tensor write path.

See \`docs/runbooks/AI-PEER-VM-DEPLOYMENT.md\`.
