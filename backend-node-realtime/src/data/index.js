const config = require('../config');

let backend;

if (config.dataBackend === 'azure_postgres') {
    backend = require('./pgAdapter');
    console.log('🗄️  Using Azure Postgres data backend');
} else {
    backend = require('./supabaseAdapter');
    console.log('🗄️  Using Supabase data backend');
}

module.exports = backend;















