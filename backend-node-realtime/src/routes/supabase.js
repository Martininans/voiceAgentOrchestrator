const supabaseService = require('../supabase');
console.log('✅ Loading Supabase Routes');

module.exports = async function (fastify, opts) {
    console.log('🔧 Registering Supabase routes with prefix:', opts.prefix || '/supabase');
    
    // Test Supabase connection
    fastify.get('/test', async (request, reply) => {
        console.log('🔗 Testing Supabase connection');
        try {
            const result = await supabaseService.testConnection();
            return result;
        } catch (error) {
            console.error('❌ Error testing Supabase connection:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Store voice interaction
    fastify.post('/interactions', async (request, reply) => {
        console.log('💾 Storing voice interaction');
        try {
            const result = await supabaseService.storeInteraction(request.body);
            return result;
        } catch (error) {
            console.error('❌ Error storing interaction:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Get user interactions
    fastify.get('/interactions/user/:userId', async (request, reply) => {
        console.log('📊 Getting user interactions');
        try {
            const { userId } = request.params;
            const limit = parseInt(request.query.limit) || 10;
            const result = await supabaseService.getUserInteractions(userId, limit);
            return { success: true, interactions: result };
        } catch (error) {
            console.error('❌ Error getting user interactions:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Get session interactions
    fastify.get('/interactions/session/:sessionId', async (request, reply) => {
        console.log('📊 Getting session interactions');
        try {
            const { sessionId } = request.params;
            const result = await supabaseService.getSessionInteractions(sessionId);
            return { success: true, interactions: result };
        } catch (error) {
            console.error('❌ Error getting session interactions:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Store user preferences
    fastify.post('/preferences/:userId', async (request, reply) => {
        console.log('⚙️  Storing user preferences');
        try {
            const { userId } = request.params;
            const result = await supabaseService.storeUserPreferences(userId, request.body);
            return result;
        } catch (error) {
            console.error('❌ Error storing user preferences:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Get user preferences
    fastify.get('/preferences/:userId', async (request, reply) => {
        console.log('⚙️  Getting user preferences');
        try {
            const { userId } = request.params;
            const result = await supabaseService.getUserPreferences(userId);
            return { success: true, preferences: result };
        } catch (error) {
            console.error('❌ Error getting user preferences:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Get interaction statistics
    fastify.get('/stats', async (request, reply) => {
        console.log('📈 Getting interaction statistics');
        try {
            const userId = request.query.user_id || null;
            const days = parseInt(request.query.days) || 7;
            const result = await supabaseService.getInteractionStats(userId, days);
            return { success: true, stats: result };
        } catch (error) {
            console.error('❌ Error getting interaction stats:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Health check for Supabase
    fastify.get('/health', async (request, reply) => {
        return {
            status: 'healthy',
            service: 'supabase',
            timestamp: new Date().toISOString()
        };
    });
    
    console.log('✅ Supabase routes registered successfully');
}; 