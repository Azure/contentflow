@description('Location for all resources')
param location string = resourceGroup().location

@description('App Configuration Store name')
param appConfigStoreName string

@description('Managed Identity that will be given access to the App Configuration Store')
param roleAssignedManagedIdentityPrincipalIds string[]

@description('Enable private endpoint for AILZ mode')
param enablePrivateEndpoint bool = false

@description('Subnet ID for private endpoint (required when enablePrivateEndpoint is true)')
param privateEndpointSubnetId string = ''

@description('App Configuration Private DNS Zone ID for private endpoint (required when enablePrivateEndpoint is true)')
param appConfigPrivateDnsZoneId string = ''

@description('Public network access setting')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Disabled'

@description('Tags for resources')
param tags object = {}

// Create list of role assignments for the managed identities
var roleAssignments = [
    for principalId in roleAssignedManagedIdentityPrincipalIds: {
      principalId: principalId
      principalType: 'ServicePrincipal'
      roleDefinitionIdOrName: 'App Configuration Data Reader'        
    }
  ]

var deployerRoleAssignments = [
    {
      principalId: deployer().objectId
      principalType: 'User'
      roleDefinitionIdOrName: 'App Configuration Data Owner'        
    }
  ]

// Use Azure Verified Module for Config Store
module appConfigStore 'br/public:avm/res/app-configuration/configuration-store:0.9.2' = {
  name: '${deployment().name}-appConfigStore'
  params: {
    name: appConfigStoreName
    location: location
    tags: tags
    sku: 'Standard'
    createMode: 'Default'
    disableLocalAuth: false
    dataPlaneProxy: {
      authenticationMode: 'Pass-through'
      privateLinkDelegation: 'Disabled'
    }
    enablePurgeProtection: false
    softDeleteRetentionInDays: 1
    roleAssignments: concat(roleAssignments, deployerRoleAssignments)
    publicNetworkAccess: publicNetworkAccess
    privateEndpoints: enablePrivateEndpoint ? [
      {
        name: '${appConfigStoreName}-pe'
        resourceGroupResourceId: resourceGroup().id
        subnetResourceId: privateEndpointSubnetId
        privateLinkServiceConnectionName: '${appConfigStoreName}-app-config-plsc'
        privateDnsZoneGroups: [
          {
            name: 'app-config-dns-zone-group'
            privateDnsZoneGroupConfigs: !empty(appConfigPrivateDnsZoneId) ? [
              {
                name: 'app-config'
                privateDnsZoneResourceId: appConfigPrivateDnsZoneId
              }
            ] : []
          }
        ]
      }
    ] : []
  }
}

output endpoint string = appConfigStore.outputs.endpoint
output resourceId string = appConfigStore.outputs.resourceId
output name string = appConfigStore.outputs.name
output privateEndpointIds array = appConfigStore.outputs.privateEndpoints
