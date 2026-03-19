// ACR Role Assignment Module
// Assigns AcrPull and AcrPush roles to a managed identity on an existing Container Registry.
// Deployed as a cross-resource-group module when the existing ACR is in a different RG.

@description('Name of the existing Container Registry')
param containerRegistryName string

@description('Principal ID of the managed identity to assign roles to')
param principalId string

resource existingAcr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(existingAcr.id, principalId, '7f951dda-4ed3-4680-a7ca-43fe172d538d')
  scope: existingAcr
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
  }
}

resource acrPushRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(existingAcr.id, principalId, '8311e382-0749-4cb8-b61a-304f252e45ec')
  scope: existingAcr
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8311e382-0749-4cb8-b61a-304f252e45ec') // AcrPush
  }
}
