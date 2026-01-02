// Cosmos DB Module with AI Landing Zone Private Endpoint Support

@description('Location for cosmos DB resources')
param location string

@description('Required: Cosmos DB account name')
param cosmosAccountName string

@description('Required: Cosmos DB database name')
param cosmosDbName string

@description('Required: Cosmos DB container names used in the application')
param cosmosDBContainerNames array

@description('Required: List of principal IDs (managed identity or user) to be assigned Cosmos DB SQL Data Contributor role')
param cosmosDBDataContributorPrincipalIds array

@description('Optional: Enable zone redundancy for Cosmos DB account. Defaults to false.')
param zoneRedundant bool = false

@description('Optional: Enable private endpoint for AILZ integrated mode. Defaults to false.')
param enablePrivateEndpoint bool = false

@description('Optional: Subnet ID for private endpoint (required when enablePrivateEndpoint is true)')
param privateEndpointSubnetId string = ''

@description('Optional: Cosmos DB Private DNS Zone ID for private endpoint (required when enablePrivateEndpoint is true)')
param cosmosPrivateDnsZoneId string = ''

@description('Optional: Public network access setting (used in AILZ integrated mode). Defaults to Enabled.')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

@description('Optional: Tags for resources')
param tags object = {}

// Use Azure Verified Module for Cosmos DB
module cosmosAccount 'br:mcr.microsoft.com/bicep/avm/res/document-db/database-account:0.16.0' = {
  name: '${deployment().name}.cosmosAccount'
  params: {
    name: cosmosAccountName
    location: location
    tags: tags
    capabilitiesToAdd: [
      'EnableServerless'
    ]
    databaseAccountOfferType: 'Standard'
    disableLocalAuthentication: true
    automaticFailover: false
    enableMultipleWriteLocations: false
    enableFreeTier: false
    defaultConsistencyLevel: 'Session'
    backupPolicyContinuousTier: 'Continuous7Days'
    networkRestrictions: {
      publicNetworkAccess: publicNetworkAccess
      networkAclBypass: 'AzureServices'
      ipRules: []
    }
    privateEndpoints: enablePrivateEndpoint ? [
      {
        name: '${cosmosAccountName}-pe'
        resourceGroupResourceId: resourceGroup().id
        subnetResourceId: privateEndpointSubnetId
        service: 'Sql'
        privateLinkServiceConnectionName: '${cosmosAccountName}-cosmos-plsc'
        privateDnsZoneGroups: [
          {
            name: 'cosmos-dns-zone-group'
            privateDnsZoneGroupConfigs: !empty(cosmosPrivateDnsZoneId) ? [
              {
                name: 'cosmos-config'
                privateDnsZoneResourceId: cosmosPrivateDnsZoneId
              }
            ] : []
          }
        ]
      }
    ] : []
    zoneRedundant: zoneRedundant
    sqlDatabases: [
      {
        name: cosmosDbName
        containers: [for container in cosmosDBContainerNames: {
            name: container.name
            paths: [container.partitionKey]
            kind: 'Hash'
          }
        ]
      }
    ]
    dataPlaneRoleDefinitions: [
      {
        // Cosmos DB Built-in Data Contributor: https://docs.azure.cn/en-us/cosmos-db/nosql/security/reference-data-plane-roles#cosmos-db-built-in-data-contributor
        roleName: 'Cosmos DB SQL Data Contributor'
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
        ]
        assignments: [
          for principalId in cosmosDBDataContributorPrincipalIds: {
            principalId: principalId
          }
        ]
      }
    ]
  }
}

// Outputs
output resourceId string = cosmosAccount.outputs.resourceId
output cosmosAccountName string = cosmosAccount.name
output cosmosEndpoint string = cosmosAccount.outputs.endpoint
output cosmosDBName string = cosmosDbName
output privateEndpoints array = cosmosAccount.outputs.privateEndpoints
