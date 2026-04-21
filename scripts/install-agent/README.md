# Install Agent (MCP Starter)

This is a starter script for an agentic package installer flow:

1. Accept customer org URL and selected modules.
2. Use Salesforce MCP tools to inspect installed metadata.
3. Deploy `EC-Core` first, then selected modules.
4. Run post-install setup and assign permission sets.

## Environment variables

- `ANTHROPIC_API_KEY`

## Next steps

- Add OAuth onboarding for customer orgs.
- Persist install jobs with status tracking.
- Add retries and policy checks around each MCP tool call.
