const { createClient } = require('@supabase/supabase-js');
const config = require('./config');

// Initialize Supabase client
const supabase = createClient(
    config.supabase.url,
    config.supabase.anonKey,
    {
        auth: {
            autoRefreshToken: true,
            persistSession: false,
            detectSessionInUrl: false
        },
        db: {
            schema: 'public'
        }
    }
);

// Database operations
class SupabaseService {
    constructor() {
        this.client = supabase;
        this.config = config.supabase;
    }

    // Test connection
    async testConnection() {
        try {
            console.log('🔍 Testing Supabase connection to:', this.config.url);
            
            // Extract domain from URL for DNS test
            const url = new URL(this.config.url);
            const domain = url.hostname;
            console.log('🔍 Testing DNS resolution for:', domain);
            
            // Test DNS resolution (this will help identify if it's a DNS issue)
            try {
                const dns = require('dns').promises;
                const addresses = await dns.resolve4(domain);
                console.log('✅ DNS resolution successful, IPs:', addresses);
            } catch (dnsError) {
                console.warn('⚠️  DNS resolution failed:', dnsError.message);
                return { connected: false, error: `DNS resolution failed: ${dnsError.message}` };
            }
            
            // First, test basic HTTP connectivity to Supabase
            try {
                const response = await fetch(this.config.url);
                console.log('✅ HTTP connectivity to Supabase successful, status:', response.status);
            } catch (httpError) {
                console.warn('⚠️  HTTP connectivity test failed:', httpError.message);
                return { connected: false, error: `HTTP connectivity failed: ${httpError.message}` };
            }
            
            // Use a simpler test that doesn't require specific tables
            const { data, error } = await this.client
                .rpc('version'); // This calls a built-in function
            
            if (error) {
                console.log('⚠️  RPC test failed, trying fallback test...');
                
                // If RPC fails, try a simple query to test connection
                const { error: queryError } = await this.client
                    .from('_dummy_table_that_doesnt_exist')
                    .select('*')
                    .limit(1);
                
                // If we get a specific error about the table not existing, connection is working
                if (queryError && queryError.message.includes('does not exist')) {
                    console.log('✅ Supabase connection successful (fallback test)');
                    return { connected: true, message: 'Supabase connected successfully (table test)' };
                }
                
                console.warn('⚠️  Supabase connection test failed:', error.message);
                console.warn('🔍 Query error details:', queryError);
                return { connected: false, error: error.message };
            }
            
            console.log('✅ Supabase connection successful');
            return { connected: true, message: 'Supabase connected successfully' };
        } catch (error) {
            console.warn('⚠️  Supabase connection error:', error.message);
            console.warn('🔍 Error type:', error.constructor.name);
            console.warn('🔍 Error stack:', error.stack);
            return { connected: false, error: error.message };
        }
    }

    // Store voice interaction
    async storeInteraction(interaction) {
        try {
            const { data, error } = await this.client
                .from('voice_interactions')
                .insert([{
                    user_id: interaction.user_id,
                    session_id: interaction.session_id,
                    call_sid: interaction.call_sid,
                    interaction_type: interaction.type,
                    input_text: interaction.input_text,
                    output_text: interaction.output_text,
                    intent: interaction.intent,
                    confidence: interaction.confidence,
                    duration: interaction.duration,
                    created_at: new Date().toISOString()
                }])
                .select();

            if (error) {
                console.error('❌ Error storing interaction:', error);
                throw error;
            }

            return { success: true, id: data[0].id };
        } catch (error) {
            console.error('❌ Supabase store interaction error:', error);
            throw error;
        }
    }

    // Get user interactions
    async getUserInteractions(userId, limit = 10) {
        try {
            const { data, error } = await this.client
                .from('voice_interactions')
                .select('*')
                .eq('user_id', userId)
                .order('created_at', { ascending: false })
                .limit(limit);

            if (error) {
                console.error('❌ Error fetching user interactions:', error);
                throw error;
            }

            return data;
        } catch (error) {
            console.error('❌ Supabase get user interactions error:', error);
            throw error;
        }
    }

    // Get session interactions
    async getSessionInteractions(sessionId) {
        try {
            const { data, error } = await this.client
                .from('voice_interactions')
                .select('*')
                .eq('session_id', sessionId)
                .order('created_at', { ascending: true });

            if (error) {
                console.error('❌ Error fetching session interactions:', error);
                throw error;
            }

            return data;
        } catch (error) {
            console.error('❌ Supabase get session interactions error:', error);
            throw error;
        }
    }

    // Store user preferences
    async storeUserPreferences(userId, preferences) {
        try {
            const { data, error } = await this.client
                .from('user_preferences')
                .upsert([{
                    user_id: userId,
                    voice_provider: preferences.voice_provider,
                    language: preferences.language,
                    voice_type: preferences.voice_type,
                    notification_preferences: preferences.notifications,
                    updated_at: new Date().toISOString()
                }])
                .select();

            if (error) {
                console.error('❌ Error storing user preferences:', error);
                throw error;
            }

            return { success: true, id: data[0].id };
        } catch (error) {
            console.error('❌ Supabase store user preferences error:', error);
            throw error;
        }
    }

    // Get user preferences
    async getUserPreferences(userId) {
        try {
            const { data, error } = await this.client
                .from('user_preferences')
                .select('*')
                .eq('user_id', userId)
                .single();

            if (error) {
                console.error('❌ Error fetching user preferences:', error);
                throw error;
            }

            return data;
        } catch (error) {
            console.error('❌ Supabase get user preferences error:', error);
            throw error;
        }
    }

    // Analytics queries
    async getInteractionStats(userId = null, days = 7) {
        try {
            let query = this.client
                .from('voice_interactions')
                .select('*')
                .gte('created_at', new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString());

            if (userId) {
                query = query.eq('user_id', userId);
            }

            const { data, error } = await query;

            if (error) {
                console.error('❌ Error fetching interaction stats:', error);
                throw error;
            }

            return {
                total_interactions: data.length,
                unique_users: userId ? 1 : new Set(data.map(d => d.user_id)).size,
                interactions_by_type: data.reduce((acc, item) => {
                    acc[item.interaction_type] = (acc[item.interaction_type] || 0) + 1;
                    return acc;
                }, {}),
                average_confidence: data.reduce((sum, item) => sum + (item.confidence || 0), 0) / data.length
            };
        } catch (error) {
            console.error('❌ Supabase get interaction stats error:', error);
            throw error;
        }
    }
}

// Create and export service instance
const supabaseService = new SupabaseService();

module.exports = supabaseService; 