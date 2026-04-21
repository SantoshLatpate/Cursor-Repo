import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export async function installPackages(customerOrgUrl, selectedModules) {
  if (!customerOrgUrl || !Array.isArray(selectedModules) || selectedModules.length === 0) {
    throw new Error('customerOrgUrl and selectedModules are required');
  }

  const message = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 1200,
    tools: [
      { type: 'salesforce_mcp', name: 'deploy_metadata' },
      { type: 'salesforce_mcp', name: 'run_apex' },
      { type: 'salesforce_mcp', name: 'assign_permission_set' }
    ],
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'text',
            text: `Install EC-Core then selected modules (${selectedModules.join(', ')}) for org ${customerOrgUrl}. Check existing metadata first, deploy only required modules, run module post-install Apex, and assign required permission sets.`
          }
        ]
      }
    ]
  });

  return message;
}
