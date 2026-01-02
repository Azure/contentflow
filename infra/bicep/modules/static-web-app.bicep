// Static Web App Module
// Creates an Azure Static Web App for hosting the React frontend

@description('Name of the static web app')
param name string

@description('Location for the static web app')
param location string

@description('SKU for the static web app')
@allowed([
  'Free'
  'Standard'
])
param sku string = 'Standard'

@description('Tags to apply to the resource')
param tags object = {}

// // Static Web App
// resource staticWebAppold 'Microsoft.Web/staticSites@2023-01-01' = {
//   name: name
//   location: location
//   tags: tags
//   sku: {
//     name: sku
//     tier: sku
//   }
//   properties: {
//     repositoryUrl: ''
//     branch: ''
//     buildProperties: {
//       skipGithubActionWorkflowGeneration: true
//       appLocation: '/'
//       apiLocation: ''
//       outputLocation: 'dist'
//     }
//     stagingEnvironmentPolicy: 'Enabled'
//     allowConfigFileUpdates: true
//     provider: 'None'
//   }
// }

// Deploy Azure Static Web App using AVM module
module staticWebApp 'br/public:avm/res/web/static-site:0.9.3' = {
  name: 'staticWebAppDeployment'
  scope: resourceGroup()
  params: {
    name: name
    location: location
    sku: sku
    tags: tags
    
    // Repository settings
    repositoryUrl: ''
    branch: ''
    repositoryToken: ''
    
    // Build properties
    buildProperties: {
      skipGithubActionWorkflowGeneration: true
      appLocation: '/'
      apiLocation: ''
      outputLocation: 'dist'
    }
    
    // Staging environment settings
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    
    // Enable managed identity for enhanced security
    managedIdentities: {
      systemAssigned: true
    }
    
  }
}

// // App settings for the static web app
// resource staticWebAppSettings 'Microsoft.Web/staticSites/config@2023-01-01' = {
//   parent: staticWebApp.outputs.identity
//   name: 'appsettings'
//   properties: {
//     // Environment variables will be set during deployment
//   }
// }

output id string = staticWebApp.outputs.resourceId
output name string = staticWebApp.outputs.name
output defaultHostname string = staticWebApp.outputs.defaultHostname
// Note: API key for deployment is retrieved via Azure CLI or portal
// output apiKey string = staticWebApp.listSecrets().properties.apiKey // Removed: Outputs should not contain secrets
