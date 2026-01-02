@description('Required: Name of the Container Registry')
param containerRegistryName string

@description('Optional: Location for all resources. Default is the resource group location')
param location string = resourceGroup().location

@description('Optional: Container Registry SKU. Default is Standard, Premium required for private endpoints')
@allowed([
  'Basic'
  'Premium'
  'Standard'
])
param sku string = 'Standard'

@description('Optional: Admin user enabled. Default is false')
param adminUserEnabled bool = false

@description('Enable private endpoint for AILZ integrated mode')
param enablePrivateEndpoint bool = false

@description('Subnet ID for private endpoint (required when enablePrivateEndpoint is true)')
param privateEndpointSubnetId string = ''

@description('Azure Container Registry Private DNS Zone ID for private endpoint (required when enablePrivateEndpoint is true)')
param acrPrivateDnsZoneId string = ''

@description('Public network access setting for the Azure Container Registry')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

@description('Zone redundancy setting for the Azure Container Registry')
@allowed(['Enabled', 'Disabled'])
param zoneRedundancy string = 'Disabled'

@description('Managed Identity that will be given access to the Container Registry')
param roleAssignedManagedIdentityPrincipalIds string[]

@description('Optional: Tags for resources')
param tags object = {}

var roleAssignmentsAcrPull = [
    for principalId in roleAssignedManagedIdentityPrincipalIds: {
      principalId: principalId
      principalType: 'ServicePrincipal'
      roleDefinitionIdOrName: 'AcrPull'        
    }
  ]

var roleAssignmentsAcrPush = [
    for principalId in roleAssignedManagedIdentityPrincipalIds: {
      principalId: principalId
      principalType: 'ServicePrincipal'
      roleDefinitionIdOrName: 'AcrPush'        
    }
  ]

var roleAssignmentsAcrDelete = [
    for principalId in roleAssignedManagedIdentityPrincipalIds: {
      principalId: principalId
      principalType: 'ServicePrincipal'
      roleDefinitionIdOrName: 'AcrDelete'        
    }
  ]

// Use Azure Verified Module for Container Registry
module containerRegistry 'br:mcr.microsoft.com/bicep/avm/res/container-registry/registry:0.9.3' = {
  params: {
    name: containerRegistryName
    location: location
    tags: tags
    acrSku: enablePrivateEndpoint ? 'Premium' : sku
    acrAdminUserEnabled: adminUserEnabled
    publicNetworkAccess: publicNetworkAccess
    zoneRedundancy: zoneRedundancy
    roleAssignments: concat(roleAssignmentsAcrPull, roleAssignmentsAcrPush, roleAssignmentsAcrDelete)
    privateEndpoints: enablePrivateEndpoint ? [
      {
        name: '${containerRegistryName}-pe'
        resourceGroupResourceId: resourceGroup().id
        subnetResourceId: privateEndpointSubnetId
        service: 'registry'
        privateLinkServiceConnectionName: '${containerRegistryName}-acr-plsc'
        privateDnsZoneGroups: [
          {
            name: 'acr-dns-zone-group'
            privateDnsZoneGroupConfigs: !empty(acrPrivateDnsZoneId) ? [
              {
                name: 'acr-config'
                privateDnsZoneResourceId: acrPrivateDnsZoneId
              }
            ] : []
          }
        ]
      }
    ] : []
  }
}

// Output
output name string = containerRegistry.outputs.name
output loginServer string = containerRegistry.outputs.loginServer
output resourceGroupName string = containerRegistry.outputs.resourceGroupName
output resourceId string = containerRegistry.outputs.resourceId
output systemAssignedMIPrincipalId string? = containerRegistry.outputs.?systemAssignedMIPrincipalId
output credentialSetsSystemAssignedMIPrincipalIds array = containerRegistry.outputs.credentialSetsSystemAssignedMIPrincipalIds
output credentialSetsResourceIds array = containerRegistry.outputs.credentialSetsResourceIds
output privateEndpoints array = containerRegistry.outputs.privateEndpoints
