@description('Location for all resources')
param location string = resourceGroup().location

@description('Application Insights name')
param appInsightsName string

@description('Log Analytics resource id output from log-analytics-ws.bicep module')
param logAnalyticsResourceId string

@description('Managed Identity that will be given access to the Application Insights')
param roleAssignedManagedIdentityPrincipalIds string[] = []

@description('Tags for resources')
param tags object = {}

// Use Azure Verified Module for App Insights
module applicationInsights 'br/public:avm/res/insights/component:0.6.0' = {
  params: {
    name: appInsightsName
    location: location
    workspaceResourceId: logAnalyticsResourceId
    tags: tags
    disableLocalAuth: false
  }
}

output resourceId string = applicationInsights.outputs.resourceId
output applicationId string = applicationInsights.outputs.applicationId
output instrumentationKey string = applicationInsights.outputs.instrumentationKey
output connectionString string = applicationInsights.outputs.connectionString
