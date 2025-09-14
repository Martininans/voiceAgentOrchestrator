const config = require('../config');

let storage;

if (config.storageBackend === 'azure_blob') {
    storage = require('./azureBlob');
    console.log('🗂️  Using Azure Blob storage backend');
} else {
    // Placeholder: implement Supabase storage adapter if needed
    storage = {
        async ensureContainer() { return; },
        async putObject() { throw new Error('Supabase storage not implemented in this adapter'); },
        async getObject() { throw new Error('Supabase storage not implemented in this adapter'); }
    };
    console.log('🗂️  Using Supabase storage backend (not implemented here)');
}

module.exports = storage;















