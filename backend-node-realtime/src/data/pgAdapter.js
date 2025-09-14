const { Pool } = require('pg');
const config = require('../config');

const pool = new Pool({ connectionString: config.azure.postgres.connectionString });

async function query(sql, params) {
    const client = await pool.connect();
    try {
        const res = await client.query(sql, params);
        return res;
    } finally {
        client.release();
    }
}

module.exports = {
    async testConnection() {
        try {
            await query('SELECT 1');
            return { connected: true, message: 'Azure Postgres connected successfully' };
        } catch (e) {
            return { connected: false, error: e.message };
        }
    },

    async storeInteraction(interaction) {
        const sql = `
            INSERT INTO voice_interactions (
                user_id, session_id, call_sid, interaction_type, input_text, output_text, intent, confidence, duration, created_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9, NOW())
            RETURNING id
        `;
        const params = [
            interaction.user_id,
            interaction.session_id,
            interaction.call_sid,
            interaction.type,
            interaction.input_text,
            interaction.output_text,
            interaction.intent,
            interaction.confidence,
            interaction.duration
        ];
        const res = await query(sql, params);
        return { success: true, id: res.rows[0].id };
    },

    async getUserInteractions(userId, limit = 10) {
        const sql = `
            SELECT * FROM voice_interactions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        `;
        const res = await query(sql, [userId, limit]);
        return res.rows;
    },

    async getSessionInteractions(sessionId) {
        const sql = `
            SELECT * FROM voice_interactions
            WHERE session_id = $1
            ORDER BY created_at ASC
        `;
        const res = await query(sql, [sessionId]);
        return res.rows;
    },

    async storeUserPreferences(userId, preferences) {
        const sql = `
            INSERT INTO user_preferences (user_id, voice_provider, language, voice_type, notification_preferences, updated_at)
            VALUES ($1,$2,$3,$4,$5,NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET voice_provider = EXCLUDED.voice_provider,
                          language = EXCLUDED.language,
                          voice_type = EXCLUDED.voice_type,
                          notification_preferences = EXCLUDED.notification_preferences,
                          updated_at = NOW()
            RETURNING user_id
        `;
        const params = [
            userId,
            preferences.voice_provider,
            preferences.language,
            preferences.voice_type,
            preferences.notifications
        ];
        const res = await query(sql, params);
        return { success: true, id: res.rows[0].user_id };
    },

    async getUserPreferences(userId) {
        const sql = `SELECT * FROM user_preferences WHERE user_id = $1`;
        const res = await query(sql, [userId]);
        return res.rows[0] || null;
    }
};















