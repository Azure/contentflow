// App Configuration Store Module with AI Landing Zone Private Endpoint Support
param appConfigStoreName string
param configurationKeyValues array

// App Configuration Store
resource appConfigStore 'Microsoft.AppConfiguration/configurationStores@2024-06-01' existing = {
  name: appConfigStoreName
}

// Configuration Key-Values
resource keyValues 'Microsoft.AppConfiguration/configurationStores/keyValues@2024-06-01' = [
  for item in configurationKeyValues: {
    name: item.name
    parent: appConfigStore
    properties: {
      value: item.value
      contentType: item.contentType
    }
  }
]
