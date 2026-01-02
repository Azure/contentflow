// ContentFlow - Deployment Template
// Supports both basic (public endpoints) and AI Landing Zone integrated (private endpoints) modes
// Configure via DEPLOYMENT_MODE environment variable: 'basic' (default) or 'ailz-integrated'
targetScope = 'resourceGroup'

// ========== DEPLOYMENT MODE PARAMETERS ==========
@description('Deployment mode: basic (creates all networking) or ailz-integrated (uses existing AI Landing Zone)')
@allowed(['basic', 'ailz-integrated'])
param deploymentMode string

// ========== REQUIRED PARAMETERS ==========
@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@minLength(1)
@description('Primary location for all resources, defaults to resource group location')
param location string = resourceGroup().location

@description('Location for AI Foundry resources')
param foundryLocation string

@description('ID of the user running the deployment')
param principalId string = ''

// ========== AI LANDING ZONE INTEGRATION PARAMETERS ==========
// Required when deploymentMode = 'ailz-integrated'

@description('Resource ID of existing AI Landing Zone Virtual Network (required for ailz-integrated mode)')
param existingVnetResourceId string = ''

@description('Name of the subnet for private endpoints in AI Landing Zone VNet (default: pe-subnet)')
param privateEndpointSubnetName string = 'pe-subnet'

@description('Name of the subnet for container apps in AI Landing Zone VNet (default: aca-env-subnet)')
param containerAppsSubnetName string = 'aca-env-subnet'

@description('Resource ID of existing Cognitive Services Private DNS Zone (required for ailz-integrated mode)')
param existingCognitiveServicesPrivateDnsZoneId string = ''

@description('Resource ID of existing Blob Storage Private DNS Zone (required for ailz-integrated mode)')
param existingBlobPrivateDnsZoneId string = ''

@description('Resource ID of existing Cosmos DB Private DNS Zone (required for ailz-integrated mode)')
param existingCosmosPrivateDnsZoneId string = ''

@description('Resource ID of existing App Config Private DNS Zone (required for ailz-integrated mode)')
param existingAppConfigPrivateDnsZoneId string = ''

@description('Resource ID of existing Container Registry Private DNS Zone (required for ailz-integrated mode)')
param existingAcrPrivateDnsZoneId string = ''

@description('Resource ID of existing Container Apps Environment Private DNS Zone (required for ailz-integrated mode)')
param existingContainerAppsEnvPrivateDnsZoneId string = ''

@description('Resource ID of existing Key Vault Private DNS Zone (optional)')
param existingKeyVaultPrivateDnsZoneId string = ''

@description('Resource ID of existing Log Analytics Workspace from AI Landing Zone (optional, will create new if not provided)')
param existingLogAnalyticsWorkspaceId string = ''

@description('Resource ID of existing App Insights from AI Landing Zone (optional, will create new if not provided)')
param existingAppInsightsId string = ''

// ========== APPLICATION SPECIFIC PARAMETERS ==========
@description('Cosmos DB database name')
param cosmosDbName string = 'contentflow'

@description('Cosmos DB container names to create')
param cosmosDBContainerNames array = [
  {name: 'executor_catalog', partitionKey: '/id'}
  {name: 'pipelines', partitionKey: '/id'}
  {name: 'vaults', partitionKey: '/id'}
  {name: 'pipeline_executions', partitionKey: '/id'}
  {name: 'vault_exec_locks', partitionKey: '/id'}
  {name: 'vault_crawl_checkpoints', partitionKey: '/id'}
  {name: 'vault_executions', partitionKey: '/id'}
]

@description('Name of the blob storage container for documents')
param docsContainerName string = 'content'

@description('API Container App target port')
param apiContainerAppTargetPort int = 8090

@description('Worker Container App target port')
param workerContainerAppTargetPort int = 8099

@description('Enable API service in worker container app - used for health checks')
param workerAPIEnabled bool = true

@description('Queue name for worker tasks')
param workerQueueName string = 'contentflow-execution-requests'

// ========== DEPLOYMENT MODE VALIDATION ==========
var isBasic = deploymentMode == 'basic'
var isAILZIntegrated = deploymentMode == 'ailz-integrated'

// Validate required parameters for ailz-integrated mode
#disable-next-line no-unused-vars
var ailzValidation = isAILZIntegrated ? {
  vnetRequired: !empty(existingVnetResourceId) ?? fail('existingVnetResourceId is required for ailz-integrated mode')
  peSubnetRequired: !empty(privateEndpointSubnetName) ?? fail('privateEndpointSubnetName is required for ailz-integrated mode')
  caSubnetRequired: !empty(containerAppsSubnetName) ?? fail('containerAppsSubnetName is required for ailz-integrated mode')
  cognitiveServicesPrivateDnsZoneRequired: !empty(existingCognitiveServicesPrivateDnsZoneId) ?? fail('existingCognitiveServicesPrivateDnsZoneId is required for ailz-integrated mode')
  blobPrivateDnsZoneRequired: !empty(existingBlobPrivateDnsZoneId) ?? fail('existingBlobPrivateDnsZoneId is required for ailz-integrated mode')
  cosmosPrivateDnsZoneRequired: !empty(existingCosmosPrivateDnsZoneId) ?? fail('existingCosmosPrivateDnsZoneId is required for ailz-integrated mode')
  appConfigPrivateDnsZoneRequired: !empty(existingAppConfigPrivateDnsZoneId) ?? fail('existingAppConfigPrivateDnsZoneId is required for ailz-integrated mode')
  acrPrivateDnsZoneRequired: !empty(existingAcrPrivateDnsZoneId) ?? fail('existingAcrPrivateDnsZoneId is required for ailz-integrated mode')
  containerAppsEnvPrivateDnsZoneRequired: !empty(existingContainerAppsEnvPrivateDnsZoneId) ?? fail('existingContainerAppsEnvPrivateDnsZoneId is required for ailz-integrated mode')
} : {}

// ========== VARIABLES ==========
var tags = {
  'azd-env-name': environmentName
  application: 'contentflow'
  deploymentMode: deploymentMode
}

var resourceToken = uniqueString(resourceGroup().id, environmentName, location)

// Network configuration based on deployment mode
var networkConfig = isAILZIntegrated ? {
  enablePrivateEndpoints: true
  publicNetworkAccess: 'Disabled'
  vnetResourceId: existingVnetResourceId
  privateEndpointSubnetId: '${existingVnetResourceId}/subnets/${privateEndpointSubnetName}'
  containerAppsSubnetId: '${existingVnetResourceId}/subnets/${containerAppsSubnetName}'
  privateDnsZoneIds: {
    cognitiveServices: existingCognitiveServicesPrivateDnsZoneId
    blob: existingBlobPrivateDnsZoneId
    cosmos: existingCosmosPrivateDnsZoneId
    appConfig: existingAppConfigPrivateDnsZoneId
    acr: existingAcrPrivateDnsZoneId
    keyVault: existingKeyVaultPrivateDnsZoneId
    containerAppsEnv: existingContainerAppsEnvPrivateDnsZoneId
  }
} : {
  enablePrivateEndpoints: false
  publicNetworkAccess: 'Enabled'
}

// Resource names
var userAssignedIdentityName = 'id-${resourceToken}'
var logAnalyticsWorkspaceName = 'log-${resourceToken}'
var appInsightsName = 'appi-${resourceToken}'
var storageAccountName = take('st${resourceToken}', 24)
var cosmosAccountName = 'cosmos-${resourceToken}'
var appConfigStoreName = 'appcs-${resourceToken}'
var containerRegistryName = 'cr${resourceToken}'
var containerAppsEnvironmentName = 'cae-${resourceToken}'
var apiContainerAppName = 'api-${resourceToken}'
var workerContainerAppName = 'worker-${resourceToken}'
var webContainerAppName = 'web-${resourceToken}'

// ========== MODULES DEPLOYMENT =========
// ***************************************

// ========== USER ASSIGNED IDENTITY ==========
module userAssignedIdentity 'modules/user-assigned-identity.bicep' = {
  name: 'userAssignedIdentity-${resourceToken}'
  params: {
    userAssignedIdentityName: userAssignedIdentityName
    location: location
    tags: tags
  }
}

// ========== OBSERVABILITY ==========
// Use existing Log Analytics if provided, otherwise create new (only in basic mode)
var shouldCreateLogAnalytics = isBasic && empty(existingLogAnalyticsWorkspaceId)

module logAnalytics 'modules/log-analytics-ws.bicep' = if (shouldCreateLogAnalytics) {
  name: 'logAnalytics-${resourceToken}'
  params: {
    logAnalyticsWorkspaceName: logAnalyticsWorkspaceName
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    location: location
    tags: tags
  }
}

var logAnalyticsWorkspaceId = !empty(existingLogAnalyticsWorkspaceId) 
  ? existingLogAnalyticsWorkspaceId 
  : (shouldCreateLogAnalytics ? logAnalytics!.outputs.resourceId : '')

// Use existing Application Insights if provided, otherwise create new (only in basic mode)
var shouldCreateAppInsights = isBasic && empty(existingAppInsightsId)

module appInsights 'modules/app-insights.bicep' = if (shouldCreateAppInsights) {
  name: 'appInsights-${resourceToken}'
  params: {
    appInsightsName: appInsightsName
    location: location
    logAnalyticsResourceId: logAnalyticsWorkspaceId
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    tags: tags
  }
}

var appInsightsConnectionString = !empty(existingAppInsightsId) 
  ? reference(existingAppInsightsId, '2020-02-02').ConnectionString 
  : (shouldCreateAppInsights ? appInsights!.outputs.connectionString : '')


// ========== STORAGE ACCOUNT  ==========
// Create new Storage Account, with private endpoint support (if using AILZ integrated mode), 
// or use public endpoints (basic mode)

module storage 'modules/storage.bicep' = {
  name: 'storage-${resourceToken}'
  params: {
    storageAccountName: storageAccountName
    location: location
    docsContainerName: docsContainerName
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    enablePrivateEndpoint: isAILZIntegrated
    privateEndpointSubnetId: isAILZIntegrated ? networkConfig.privateEndpointSubnetId : ''
    blobPrivateDnsZoneId: isAILZIntegrated ? networkConfig.privateDnsZoneIds.blob : ''
    publicNetworkAccess: isAILZIntegrated ? 'Disabled' : 'Enabled'
    logAnalyticsWorkspaceId: logAnalyticsWorkspaceId
    tags: tags
  }
}


// ========== COSMOS DB ==========
// Create new Cosmos DB account with private endpoint support (if using AILZ integrated mode),
// or use public endpoints (basic mode)

module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos-${resourceToken}'
  params: {
    location: location
    cosmosAccountName: cosmosAccountName
    cosmosDbName: cosmosDbName
    cosmosDBContainerNames: cosmosDBContainerNames
    cosmosDBDataContributorPrincipalIds: !empty(principalId) ? [userAssignedIdentity.outputs.principalId, principalId] : [userAssignedIdentity.outputs.principalId]
    zoneRedundant: false
    enablePrivateEndpoint: isAILZIntegrated
    privateEndpointSubnetId: isAILZIntegrated ? networkConfig.privateEndpointSubnetId : ''
    cosmosPrivateDnsZoneId: isAILZIntegrated ? networkConfig.privateDnsZoneIds.cosmos : ''
    publicNetworkAccess: isAILZIntegrated ? 'Disabled' : 'Enabled'
    tags: tags
  }
}

// ========== APP CONFIGURATION ==========
// Create new App Configuration store, with private endpoint support (if using AILZ integrated mode),
// or use public endpoints (basic mode)

module appConfigStore 'modules/app-config-store.bicep' = {
  name: 'appConfig-${resourceToken}'
  params: {
    appConfigStoreName: appConfigStoreName
    location: location
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    enablePrivateEndpoint: isAILZIntegrated
    privateEndpointSubnetId: isAILZIntegrated ? networkConfig.privateEndpointSubnetId : ''
    appConfigPrivateDnsZoneId: isAILZIntegrated ? networkConfig.privateDnsZoneIds.appConfig : ''
    publicNetworkAccess: isAILZIntegrated ? 'Disabled' : 'Enabled'
    tags: tags
  }
}

module appConfigStoreKeys 'modules/app-config-store-keys.bicep' = {
  name: 'appConfigKeys-${resourceToken}'
  params: {
    appConfigStoreName: appConfigStoreName
    // Prepopulate App Config with required settings
    configurationKeyValues: [
      {
        contentType: 'text/plain'
        name: 'contentflow.common.COSMOS_DB_ENDPOINT'
        value: cosmos!.outputs.cosmosEndpoint
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.common.COSMOS_DB_NAME'
        value: cosmosDbName
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.common.BLOB_STORAGE_ACCOUNT_NAME'
        value: storageAccountName
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.common.BLOB_STORAGE_CONTAINER_NAME'
        value: docsContainerName
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.common.STORAGE_ACCOUNT_WORKER_QUEUE_URL'
        value: storage!.outputs.primaryQueueEndpoint
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.common.STORAGE_WORKER_QUEUE_NAME'
        value: workerQueueName
      }
      // API settings
      {
        contentType: 'text/plain'
        name: 'contentflow.api.API_ENABLED'
        value: 'True'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.api.DEBUG'
        value: 'False'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.api.LOG_LEVEL'
        value: 'DEBUG'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.api.API_SERVER_HOST'
        value: '0.0.0.0'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.api.API_SERVER_PORT'
        value: '${apiContainerAppTargetPort}'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.api.API_SERVER_WORKERS'
        value: '1'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.api.CORS_ALLOW_CREDENTIALS'
        value: 'true'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.api.CORS_ALLOW_ORIGINS'
        value: '*'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.api.WORKER_ENGINE_API_ENDPOINT'
        value: 'https://${workerContainerApp.outputs.fqdn}'
      }
      // Worker settings
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.NUM_PROCESSING_WORKERS'
        value: '4'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.NUM_SOURCE_WORKERS'
        value: '2'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.LOG_LEVEL'
        value: 'INFO'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.DEBUG'
        value: 'false'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.API_ENABLED'
        value: '${workerAPIEnabled}'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.API_HOST'
        value: '0.0.0.0'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.API_PORT'
        value: '${workerContainerAppTargetPort}'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.QUEUE_POLL_INTERVAL_SECONDS'
        value: '5'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.QUEUE_VISIBILITY_TIMEOUT_SECONDS'
        value: '300'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.QUEUE_MAX_MESSAGES'
        value: '32'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.MAX_TASK_RETRIES'
        value: '3'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.TASK_TIMEOUT_SECONDS'
        value: '600'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.DEFAULT_POLLING_INTERVAL_SECONDS'
        value: '60'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.SCHEDULER_SLEEP_INTERVAL_SECONDS'
        value: '5'
      }
      {
        contentType: 'text/plain'
        name: 'contentflow.worker.LOCK_TTL_SECONDS'
        value: '300'
      }
      {
        contentType: 'text/plain'
        name: 'sentinel'
        value: '1'
      }
    ]
  }
  dependsOn: [
    // appConfigStore
  ]
}

// ========== CONTAINER REGISTRY WITH PRIVATE ENDPOINT SUPPORT ==========
// Create new Container Registry, with private endpoint support (if using AILZ integrated mode),
// or use public endpoints (basic mode)

module containerRegistry 'modules/container-registry.bicep' = {
  name: 'acr-${resourceToken}'
  params: {
    containerRegistryName: containerRegistryName
    location: location
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    enablePrivateEndpoint: isAILZIntegrated
    privateEndpointSubnetId: isAILZIntegrated ? networkConfig.privateEndpointsSubnetId : ''
    acrPrivateDnsZoneId: isAILZIntegrated ? networkConfig.privateDnsZoneIds.acr : ''
    publicNetworkAccess: isAILZIntegrated ? 'Disabled' : 'Enabled'
    tags: tags
  }
}

// ========== CONTAINER APPS ENVIRONMENT ==========
// Create new Container Apps Environment, with private endpoint support (if using AILZ integrated mode),
// or use public endpoints (basic mode)

module containerAppsEnvironment 'modules/container-apps-environment.bicep' = {
  name: 'cae-la-${resourceToken}'
  params: {
    containerAppsEnvironmentName: containerAppsEnvironmentName
    logAnalyticsWorkspaceId: !empty(existingLogAnalyticsWorkspaceId) ? existingLogAnalyticsWorkspaceId : logAnalytics!.outputs.logAnalyticsWorkspaceId
    logAnalyticsPrimarySharedKey: !empty(existingLogAnalyticsWorkspaceId) ? listKeys(existingLogAnalyticsWorkspaceId, '2021-12-01-preview').primarySharedKey : logAnalytics.outputs.primarySharedKey
    userAssignedResourceIds: [userAssignedIdentity.outputs.resourceId]
    location: location
    enablePrivateEndpoint: isAILZIntegrated
    privateEndpointSubnetId: isAILZIntegrated ? networkConfig.containerAppsSubnetId : null
    // caePrivateDnsZoneId: isAILZIntegrated ? networkConfig.privateDnsZoneIds.existingContainerAppsEnvPrivateDnsZoneId : ''
    publicNetworkAccess: isAILZIntegrated ? 'Disabled' : 'Enabled'
    tags: tags
  }
}

// ========== AI FOUNDRY HUB AND PROJECT ==========
module aiFoundry 'modules/ai-foundry.bicep' = {
  name: 'aiFoundry-${resourceToken}'
  params: {
    aiFoundryBaseName: substring('aif${resourceToken}', 0, 12)
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    location: foundryLocation
    tags: tags
  }
}

// ========== API CONTAINER APP ==========
module apiContainerApp 'modules/container-app.bicep' = {
  name: 'ca-api-${resourceToken}'
  params: {
    name: apiContainerAppName
    location: containerAppsEnvironment!.outputs.location
    containerAppsEnvId: containerAppsEnvironment!.outputs.resourceId
    containerRegistryServer: containerRegistry!.outputs.loginServer
    managedIdentityId: userAssignedIdentity.outputs.resourceId
    targetPort: 8090
    externalIngress: !isAILZIntegrated
    corsEnabled: true
    livenessProbePath: '/'
    cpuCores: 2
    memoryInGB: '4Gi'
    minReplicas: 1
    maxReplicas: 2
    environmentVariables: [
      {
        name: 'AZURE_APP_CONFIG_ENDPOINT'
        value: appConfigStore!.outputs.endpoint
      }
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: appInsightsConnectionString
      }
      {
        name: 'AZURE_CLIENT_ID'
        value: userAssignedIdentity.outputs.clientId
      }
    ]
    tags: union(tags, { 'azd-service-name': 'api' })
  }
}

// ========== WORKER CONTAINER APP ==========
module workerContainerApp 'modules/container-app.bicep' = {
  name: 'ca-worker-${resourceToken}'
  params: {
    name: workerContainerAppName
    location: containerAppsEnvironment!.outputs.location
    containerAppsEnvId: containerAppsEnvironment!.outputs.resourceId
    containerRegistryServer: containerRegistry!.outputs.loginServer
    managedIdentityId: userAssignedIdentity.outputs.resourceId
    targetPort: workerContainerAppTargetPort
    externalIngress: !isAILZIntegrated
    corsEnabled: true
    livenessProbePath: '/'
    cpuCores: 2
    memoryInGB: '4Gi'
    minReplicas: 1
    maxReplicas: 3
    environmentVariables: [
      {
        name: 'AZURE_APP_CONFIG_ENDPOINT'
        value: appConfigStore!.outputs.endpoint
      }
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: appInsightsConnectionString
      }
      {
        name: 'AZURE_CLIENT_ID'
        value: userAssignedIdentity.outputs.clientId
      }
    ]
    tags: union(tags, { 'azd-service-name': 'worker' })
  }
}

// ========== API CONTAINER APP ==========
module webContainerApp 'modules/container-app.bicep' = {
  name: 'ca-web-${resourceToken}'
  params: {
    name: webContainerAppName
    location: containerAppsEnvironment!.outputs.location
    containerAppsEnvId: containerAppsEnvironment!.outputs.resourceId
    containerRegistryServer: containerRegistry!.outputs.loginServer
    managedIdentityId: userAssignedIdentity.outputs.resourceId
    targetPort: 8080
    externalIngress: !isAILZIntegrated
    corsEnabled: true
    livenessProbePath: '/'
    cpuCores: 1
    memoryInGB: '2Gi'
    minReplicas: 1
    maxReplicas: 1
    environmentVariables: [
      {
        name: 'VITE_API_BASE_URL'
        value: 'https://${apiContainerApp.outputs.fqdn}/api/'
      }
    ]
    tags: union(tags, { 'azd-service-name': 'web' })
  }
}

// ========== OUTPUTS ==========
output DEPLOYMENT_MODE string = deploymentMode
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = resourceGroup().name

// Container Registry outputs
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry!.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name

// Service endpoints
output API_ENDPOINT string = 'https://${apiContainerApp.outputs.fqdn}'
output WORKER_ENDPOINT string = 'https://${workerContainerApp.outputs.fqdn}'
output WEB_ENDPOINT string = 'https://${webContainerApp.outputs.fqdn}'

// Resource outputs
output COSMOS_DB_ENDPOINT string = cosmos.outputs.cosmosEndpoint
output COSMOS_DB_NAME string = cosmosDbName
output STORAGE_ACCOUNT_NAME string = storage.outputs.name
output STORAGE_QUEUE_URL string = storage.outputs.primaryQueueEndpoint
output STORAGE_QUEUE_NAME string = workerQueueName
output APP_CONFIG_ENDPOINT string = appConfigStore.outputs.endpoint
output APPLICATIONINSIGHTS_CONNECTION_STRING string = appInsightsConnectionString

// Managed Identity outputs
output MANAGED_IDENTITY_CLIENT_ID string = userAssignedIdentity.outputs.clientId
output MANAGED_IDENTITY_PRINCIPAL_ID string = userAssignedIdentity.outputs.principalId

// AI Foundry outputs
output AZURE_AI_FOUNDRY_LOCATION string = aiFoundry.outputs.location
output AI_PROJECT_NAME string = aiFoundry.outputs.aiProjectName
output AI_SERVICES_NAME string = aiFoundry.outputs.aiServicesName

// Network outputs
output VNET_RESOURCE_ID string = isAILZIntegrated ? existingVnetResourceId : ''
output PRIVATE_ENDPOINT_SUBNET_ID string = isAILZIntegrated ? networkConfig.privateEndpointSubnetId : ''
output CONTAINER_APPS_SUBNET_ID string = isAILZIntegrated ? networkConfig.containerAppsSubnetId : ''
