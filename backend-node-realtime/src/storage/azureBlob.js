const { BlobServiceClient } = require('@azure/storage-blob');
const config = require('../config');

function getClient() {
    if (!config.azure.blob.connectionString) {
        throw new Error('Missing AZURE_STORAGE_CONNECTION_STRING');
    }
    const serviceClient = BlobServiceClient.fromConnectionString(config.azure.blob.connectionString);
    const containerClient = serviceClient.getContainerClient(config.azure.blob.container);
    return { serviceClient, containerClient };
}

module.exports = {
    async ensureContainer() {
        const { containerClient } = getClient();
        await containerClient.createIfNotExists({ access: 'container' });
    },

    async putObject(key, buffer, contentType = 'application/octet-stream') {
        const { containerClient } = getClient();
        const blockBlobClient = containerClient.getBlockBlobClient(key);
        await blockBlobClient.uploadData(buffer, {
            blobHTTPHeaders: { blobContentType: contentType }
        });
        return { key, url: blockBlobClient.url };
    },

    async getObject(key) {
        const { containerClient } = getClient();
        const blockBlobClient = containerClient.getBlockBlobClient(key);
        const download = await blockBlobClient.download();
        const chunks = [];
        for await (const chunk of download.readableStreamBody) {
            chunks.push(chunk);
        }
        return Buffer.concat(chunks);
    }
};















