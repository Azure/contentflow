// Queue Private DNS Zone Module
// Creates privatelink.queue.core.windows.net DNS zone and links it to the VNet
// Used when no existing queue DNS zone is provided in AILZ mode

@description('Resource ID of the VNet to link the DNS zone to')
param vnetResourceId string

@description('Tags for resources')
param tags object = {}

// Create the private DNS zone for Azure Storage Queue
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: 'privatelink.queue.core.windows.net'
  location: 'global'
  tags: tags
}

// Link the DNS zone to the VNet so containers can resolve queue endpoints via private IP
resource vnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: privateDnsZone
  name: '${last(split(vnetResourceId, '/'))}-queue-link'
  location: 'global'
  tags: tags
  properties: {
    virtualNetwork: {
      id: vnetResourceId
    }
    registrationEnabled: false
  }
}

output dnsZoneId string = privateDnsZone.id
