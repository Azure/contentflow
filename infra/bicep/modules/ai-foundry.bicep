@description('Optional: Location for all resources. Default is the resource group location')
param location string = resourceGroup().location

@description('Required: The AI Foundry base name (max 12 characters)')
param aiFoundryBaseName string

@description('Managed Identity that will be given access to the AI Foundry Resource')
param roleAssignedManagedIdentityPrincipalIds string[] = []

@description('Tags for resources')
param tags object = {}

// NOTE: User/human deployer role assignments (Azure AI Developer) are intentionally NOT done here.
// ARM role assignments have deterministic GUIDs computed from scope+principal+role. If the same role
// was previously assigned via CLI (random GUID), Bicep will conflict with a RoleAssignmentExists error
// and fail the entire deployment. post-provision.sh owns all user role assignments exclusively,
// using `az role assignment create` which is idempotent and handles duplicates gracefully.
var managedIdentityRoleAssignments = [for principalId in roleAssignedManagedIdentityPrincipalIds: {
  principalId: principalId
  principalType: 'ServicePrincipal'
  roleDefinitionIdOrName: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // 'Azure AI User'
}]

module aiFoundry 'br/public:avm/ptn/ai-ml/ai-foundry:0.5.0' = {
  params: {
    // Required parameters
    baseName: aiFoundryBaseName
    location: location
    tags: tags
    // Non-required parameters
    aiFoundryConfiguration: {
      // accountName: '<accountName>'
      allowProjectManagement: true
      createCapabilityHosts: false
      disableLocalAuth: true
      location: location
      project: {
        desc: 'AI Foundry project for ContentFlow Solution Accelerator'
        displayName: 'ContentFlow'
        name: 'contentflow-project'
      }
      roleAssignments: managedIdentityRoleAssignments
      sku: 'S0'
    }
    aiModelDeployments: [
      {
        model: {
          format: 'OpenAI'
          name: 'gpt-4.1-mini'
          version: '2025-04-14'
        }
        name: 'gpt-4.1-mini'
        sku: {
          capacity: 100
          name: 'GlobalStandard'
        }
      }
      {
        model: {
          format: 'OpenAI'
          name: 'gpt-4.1'
          version: '2025-04-14'
        }
        name: 'gpt-4.1'
        sku: {
          capacity: 100
          name: 'GlobalStandard'
        }
      }
      {
        model: {
          format: 'OpenAI'
          name: 'text-embedding-3-large'
          version: '1'
        }
        name: 'text-embedding-3-large'
        sku: {
          capacity: 100
          name: 'Standard'
        }
      }
    ]
    // aiSearchConfiguration: {
    //   name: '<name>'
    //   privateDnsZoneResourceId: '<privateDnsZoneResourceId>'
    //   roleAssignments: [
    //     {
    //       principalId: '<principalId>'
    //       principalType: 'ServicePrincipal'
    //       roleDefinitionIdOrName: 'Search Index Data Contributor'
    //     }
    //   ]
    // }
    // // baseUniqueName: '<baseUniqueName>'
    // cosmosDbConfiguration: {
    //   name: '<name>'
    //   privateDnsZoneResourceId: '<privateDnsZoneResourceId>'
    //   roleAssignments: [
    //     {
    //       principalId: '<principalId>'
    //       principalType: 'ServicePrincipal'
    //       roleDefinitionIdOrName: 'Cosmos DB Account Reader Role'
    //     }
    //   ]
    // }
    includeAssociatedResources: false
    // keyVaultConfiguration: {
    //   name: '<name>'
    //   privateDnsZoneResourceId: '<privateDnsZoneResourceId>'
    //   roleAssignments: [
    //     {
    //       principalId: '<principalId>'
    //       principalType: 'ServicePrincipal'
    //       roleDefinitionIdOrName: 'Key Vault Secrets User'
    //     }
    //   ]
    // }
  }
}


output aiProjectName string = aiFoundry.outputs.aiProjectName
output aiServicesName string = aiFoundry.outputs.aiServicesName
output location string = location
