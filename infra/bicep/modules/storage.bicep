// Storage Account Module
// Creates storage account with private endpoints (AILZ) or public endpoints (standalone)

@description('Location for all resources')
param location string = resourceGroup().location

@description('Storage account name')
param storageAccountName string

@description('Storage account SKU name')
@allowed([
  'Standard_LRS'
  'Standard_GRS'
  'Standard_RAGRS'
  'Standard_ZRS'
  'Premium_LRS'
  'Premium_ZRS'
])
param skuName string = 'Standard_LRS'

@description('Container name for documents')
param docsContainerName string

@description('Managed identities that will be given access to the storage account')
param roleAssignedManagedIdentityPrincipalIds array

@description('Enable private endpoint for AILZ mode')
param enablePrivateEndpoint bool = false

@description('Subnet ID for private endpoint (required when enablePrivateEndpoint is true)')
param privateEndpointSubnetId string = ''

@description('Blob Private DNS Zone ID for private endpoint (required when enablePrivateEndpoint is true)')
param blobPrivateDnsZoneId string = ''

@description('Queue Private DNS Zone ID for private endpoint (required when enablePrivateEndpoint is true)')
param queuePrivateDnsZoneId string = ''

@description('Public network access setting')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Disabled'

@description('Log Analytics Workspace ID for diagnostic settings')
param logAnalyticsWorkspaceId string = ''

@description('Tags for resources')
param tags object = {}


var accountRoleAssignments array = [for principalId in roleAssignedManagedIdentityPrincipalIds: {
          principalId: principalId
          principalType: 'ServicePrincipal'
          roleDefinitionIdOrName: 'Contributor'        
        }
      ]

var blobRoleAssignments array = [for principalId in roleAssignedManagedIdentityPrincipalIds: {
          principalId: principalId
          principalType: 'ServicePrincipal'
          roleDefinitionIdOrName: 'Storage Blob Data Contributor'        
        }
      ]

var queueRoleAssignments array = [for principalId in roleAssignedManagedIdentityPrincipalIds: {
          principalId: principalId
          principalType: 'ServicePrincipal'
          roleDefinitionIdOrName: 'Storage Queue Data Contributor'        
        }
      ]

var deployerRoleAssignments = [
    {
      principalId: deployer().objectId
      principalType: 'User'
      roleDefinitionIdOrName: 'Storage Blob Data Contributor'        
    }
    {
      principalId: deployer().objectId
      principalType: 'User'
      roleDefinitionIdOrName: 'Storage Queue Data Contributor'        
    }
  ]


// Use Azure Verified Module for Storage Account
module storageAccount 'br/public:avm/res/storage/storage-account:0.27.1' = {
  name: '${deployment().name}.storageAccount'
  params: {
    // Required parameters
    name: storageAccountName
    // Non-required parameters
    location: location
    kind: 'StorageV2'
    skuName: skuName
    accessTier: 'Hot'
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalyticsWorkspaceId
      }
    ]
    allowSharedKeyAccess: false
    enableHierarchicalNamespace: false
    publicNetworkAccess: publicNetworkAccess
    networkAcls: enablePrivateEndpoint ? {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      ipRules: []
      virtualNetworkRules: []
    } : {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
    privateEndpoints: enablePrivateEndpoint ? [
      {
        name: '${storageAccountName}-blob-pe'
        resourceGroupResourceId: resourceGroup().id
        subnetResourceId: privateEndpointSubnetId
        service: 'blob'
        privateLinkServiceConnectionName: '${storageAccountName}-blob-plsc'
        privateDnsZoneGroups: [
          {
            name: 'blob-dns-zone-group'
            privateDnsZoneGroupConfigs: [
              {
                name: 'blob-config'
                privateDnsZoneResourceId: blobPrivateDnsZoneId
              }
            ]
          }
        ]
      }
      {
        name: '${storageAccountName}-queue-pe'
        resourceGroupResourceId: resourceGroup().id
        subnetResourceId: privateEndpointSubnetId
        service: 'queue'
        privateLinkServiceConnectionName: '${storageAccountName}-queue-plsc'
        privateDnsZoneGroups: [
          {
            name: 'queue-dns-zone-group'
            privateDnsZoneGroupConfigs: [
              {
                name: 'queue-config'
                privateDnsZoneResourceId: queuePrivateDnsZoneId
              }
            ]
          }
        ]
      }
    ] : []
    blobServices: {
      automaticSnapshotPolicyEnabled: true
      deleteRetentionPolicyDays: 7
      deleteRetentionPolicyEnabled: true
      containerDeleteRetentionPolicyDays: 7
      containerDeleteRetentionPolicyEnabled: true
      containers: [
        {
          name: docsContainerName
          publicAccess: 'None'
        }
      ]
    }
    queueServices: {
      queues: [
        {
          name: 'contentflow-execution-requests'
          metadata: {}
        }
      ]
    }
    roleAssignments: concat(
      accountRoleAssignments,
      blobRoleAssignments,
      queueRoleAssignments,
      deployerRoleAssignments
    )
    tags: tags
  }
}

// Outputs
output resourceId string = storageAccount.outputs.resourceId
output name string = storageAccount.name
output primaryBlobEndpoint string = storageAccount.outputs.primaryBlobEndpoint
output primaryQueueEndpoint string = 'https://${storageAccount.outputs.name}.queue.${environment().suffixes.storage}/'
output privateEndpoints array = storageAccount.outputs.privateEndpoints
