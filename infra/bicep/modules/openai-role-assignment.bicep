// Assigns 'Cognitive Services OpenAI User' role to a managed identity on an existing Azure OpenAI resource.
// This enables the managed identity to perform inference operations (chat completions, embeddings, etc.)
// without requiring API keys — supporting Zero Trust Architecture (ZTA) compliance.

@description('Resource ID of the existing Azure OpenAI / Cognitive Services resource')
param openAIResourceId string

@description('Principal IDs of the managed identities to assign the role to')
param principalIds string[]

// Cognitive Services OpenAI User - allows inference (completions, embeddings) but not management
var roleDefinitionId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

// Reference the existing resource to scope the role assignment
resource openAIResource 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: last(split(openAIResourceId, '/'))
  scope: resourceGroup()
}

// Create role assignments for each principal
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for principalId in principalIds: {
    name: guid(openAIResourceId, roleDefinitionId, principalId)
    scope: openAIResource
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
      principalId: principalId
      principalType: 'ServicePrincipal'
    }
  }
]
