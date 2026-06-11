@description('The default domain of the Container Apps Environment (e.g. ambitiousdesert-f1f7e820.eastus.azurecontainerapps.io)')
param caeDefaultDomain string

@description('The static IP of the Container Apps Environment')
param caeStaticIp string

@description('Resource ID of the VNet to link the DNS zone to')
param vnetResourceId string

@description('Tags for resources')
param tags object = {}

// Create a Private DNS Zone matching the CAE default domain
// Internal CAE requires DNS resolution of *.defaultDomain → staticIp
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: caeDefaultDomain
  location: 'global'
  tags: tags
}

// Wildcard A record so all container app FQDNs resolve to the CAE static IP
resource wildcardRecord 'Microsoft.Network/privateDnsZones/A@2024-06-01' = {
  parent: privateDnsZone
  name: '*'
  properties: {
    ttl: 300
    aRecords: [
      {
        ipv4Address: caeStaticIp
      }
    ]
  }
}

// Also add an @ record for the apex domain
resource apexRecord 'Microsoft.Network/privateDnsZones/A@2024-06-01' = {
  parent: privateDnsZone
  name: '@'
  properties: {
    ttl: 300
    aRecords: [
      {
        ipv4Address: caeStaticIp
      }
    ]
  }
}

// Link the DNS zone to the VNet so jumpbox and other VNet resources can resolve
resource vnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: privateDnsZone
  name: '${last(split(vnetResourceId, '/'))}-cae-link'
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
output dnsZoneName string = privateDnsZone.name
