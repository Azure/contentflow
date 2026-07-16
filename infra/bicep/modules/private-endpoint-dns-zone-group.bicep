@description('Name of the private endpoint')
param privateEndpointName string

@description('Resource ID of the private DNS zone')
param privateDnsZoneId string

@description('Location for the deployment metadata')
param location string = resourceGroup().location

// Reference existing private endpoint
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' existing = {
  name: privateEndpointName
}

// Create DNS zone group for the private endpoint
resource dnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-azurecr-io'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

output dnsZoneGroupName string = dnsZoneGroup.name
output dnsZoneGroupId string = dnsZoneGroup.id
