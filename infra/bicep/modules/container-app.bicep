// Container App Module
// Creates a Container App with azd-compatible configuration

@description('Name of the container app')
param name string

@description('Location for the container app')
param location string

@description('Container Apps Environment ID')
param containerAppsEnvId string

@description('Container Registry server')
param containerRegistryServer string

@description('Managed Identity Resource ID')
param managedIdentityId string

@description('Target port for the container')
param targetPort int

@description('Enable external ingress. Defaults to true.')
param externalIngress bool = true

@description('Enable CORS. Defaults to true.')
param corsEnabled bool = true

@description('CPU cores for the container. Defaults to 1.')
param cpuCores int = 1

@description('Memory in GB for the container. Defaults to 2Gi.')
param memoryInGB string = '2Gi'

@description('Liveness probe path. Leave empty to disable liveness probe. Defaults to /health.')
param livenessProbePath string = ''

@description('Minimum number of replicas for scaling. Defaults to 1.')
param minReplicas int = 1

@description('Maximum number of replicas for scaling. Defaults to 2.')
param maxReplicas int = 2

@description('Environment variables')
param environmentVariables array = []

@description('Tags to apply to resources')
param tags object = {}


// Use Azure Verified Module for Container App
module containerApp 'br:mcr.microsoft.com/bicep/avm/res/app/container-app:0.19.0' = {
  name: '${deployment().name}.containerApp'
  params: {
    name: name
    location: location
    tags: tags
    environmentResourceId: containerAppsEnvId
    corsPolicy: corsEnabled ? {
      allowedOrigins: ['*']
      allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
      allowedHeaders: ['*']
      exposeHeaders: ['*']
      maxAge: 3600
      allowCredentials: true
    } : null
    containers: [
      {
        name: name
        // Use base image as required by azd - will be replaced during deployment
        image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
        resources: {
          cpu: cpuCores
          memory: memoryInGB
        }
        env: environmentVariables
        probes: !empty(livenessProbePath) ? [
          {
            type: 'Liveness'
            httpGet: {
              path: livenessProbePath
              port: targetPort
            }
            initialDelaySeconds: 5
            periodSeconds: 60
          }
        ] : []
      }
    ]
    ingressAllowInsecure: false
    ingressExternal: externalIngress
    ingressTargetPort: targetPort
    ingressTransport: 'auto'
    activeRevisionsMode: 'Single'
    managedIdentities: {
      userAssignedResourceIds: [ managedIdentityId ]
    }
    registries: [
      {
        server: containerRegistryServer
        identity: managedIdentityId
      }
    ]
    scaleSettings: maxReplicas > 1 ? {
      minReplicas: minReplicas
      maxReplicas: maxReplicas
      rules: [ 
        {
          name: 'http-scaler'
          http: {
            metadata: {
              concurrentRequests: '10'
            }
          }
        }
      ]
    } : null
  }
}

output resourceId string = containerApp.outputs.resourceId
output name string = containerApp.name
output fqdn string = containerApp.outputs.fqdn
