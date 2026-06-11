@description('Name of the Container Apps Environment')
param containerAppsEnvironmentName string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Log Analytics workspace resource ID used to derive customer ID and shared key')
param logAnalyticsWorkspaceResourceId string

@description('User Assigned Identity resource IDs that will be assigned to the Container Apps Environment')
param userAssignedResourceIds string[]

@description('Enable private endpoint for AILZ integrated mode')
param enablePrivateEndpoint bool = false

@description('Subnet ID for private endpoint (required when enablePrivateEndpoint is true)')
param privateEndpointSubnetId string = ''

// @description('Azure Container Apps Environment Private DNS Zone ID for private endpoint (required when enablePrivateEndpoint is true)')
// param caePrivateDnsZoneId string = ''

@description('Public network access setting for the Azure Container Registry')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'


@description('Tags for resources')
param tags object = {}

// Derive Log Analytics credentials from workspace resource ID
var logAnalyticsCustomerId = reference(logAnalyticsWorkspaceResourceId, '2021-12-01-preview').customerId
var logAnalyticsSharedKey = listKeys(logAnalyticsWorkspaceResourceId, '2021-12-01-preview').primarySharedKey

// Use Azure Verified Module for Container Apps Environment
module containerAppsEnvironment 'br:mcr.microsoft.com/bicep/avm/res/app/managed-environment:0.11.3' = {
  name: '${deployment().name}.containerAppsEnvironment'
  params: {
    name: containerAppsEnvironmentName
    location: location
    tags: tags
    zoneRedundant: false
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
    platformReservedCidr: '172.17.17.0/24'
    platformReservedDnsIP: '172.17.17.17'
    publicNetworkAccess: publicNetworkAccess
    internal: enablePrivateEndpoint
    infrastructureSubnetResourceId: enablePrivateEndpoint ? privateEndpointSubnetId : null
    managedIdentities: {
      systemAssigned: true
      userAssignedResourceIds: userAssignedResourceIds
    }
    
  }
}

output name string = containerAppsEnvironment.outputs.name
output resourceId string = containerAppsEnvironment.outputs.resourceId
output location string = containerAppsEnvironment.outputs.location
output systemAssignedMIPrincipalId string? = containerAppsEnvironment.outputs.?systemAssignedMIPrincipalId
output defaultDomain string = containerAppsEnvironment.outputs.defaultDomain
output staticIp string = containerAppsEnvironment.outputs.staticIp
output domainVerificationId string = containerAppsEnvironment.outputs.domainVerificationId
