const supabaseService = require('../supabase');

module.exports = {
    async testConnection() {
        return supabaseService.testConnection();
    },

    async storeInteraction(interaction) {
        return supabaseService.storeInteraction(interaction);
    },

    async getUserInteractions(userId, limit = 10) {
        return supabaseService.getUserInteractions(userId, limit);
    },

    async getSessionInteractions(sessionId) {
        return supabaseService.getSessionInteractions(sessionId);
    },

    async storeUserPreferences(userId, preferences) {
        return supabaseService.storeUserPreferences(userId, preferences);
    },

    async getUserPreferences(userId) {
        return supabaseService.getUserPreferences(userId);
    }
};















