-- Voice Agent Orchestrator - Supabase Database Schema
-- Run this in your Supabase SQL editor to create the required tables

-- Enable Row Level Security (RLS)
ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret-here';

-- Create voice_interactions table
CREATE TABLE IF NOT EXISTS voice_interactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    call_sid VARCHAR(255),
    interaction_type VARCHAR(50) NOT NULL, -- 'audio', 'text', 'call', 'sms'
    input_text TEXT,
    output_text TEXT,
    intent VARCHAR(100),
    confidence DECIMAL(3,2),
    duration INTEGER, -- in milliseconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    voice_provider VARCHAR(50) DEFAULT 'twilio',
    language VARCHAR(10) DEFAULT 'en-US',
    voice_type VARCHAR(50) DEFAULT 'alice',
    notification_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create call_sessions table
CREATE TABLE IF NOT EXISTS call_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    call_sid VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20),
    call_status VARCHAR(50) DEFAULT 'initiated',
    call_duration INTEGER, -- in seconds
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analytics_events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_voice_interactions_user_id ON voice_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_interactions_session_id ON voice_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_voice_interactions_created_at ON voice_interactions(created_at);
CREATE INDEX IF NOT EXISTS idx_call_sessions_user_id ON call_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_call_sessions_session_id ON call_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_voice_interactions_updated_at 
    BEFORE UPDATE ON voice_interactions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_call_sessions_updated_at 
    BEFORE UPDATE ON call_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE voice_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (basic policies - adjust based on your auth requirements)
CREATE POLICY "Allow all operations on voice_interactions" ON voice_interactions
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on user_preferences" ON user_preferences
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on call_sessions" ON call_sessions
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on analytics_events" ON analytics_events
    FOR ALL USING (true);

-- Create some helpful views
CREATE OR REPLACE VIEW interaction_summary AS
SELECT 
    user_id,
    COUNT(*) as total_interactions,
    COUNT(DISTINCT session_id) as total_sessions,
    AVG(confidence) as avg_confidence,
    MAX(created_at) as last_interaction
FROM voice_interactions
GROUP BY user_id;

CREATE OR REPLACE VIEW daily_interactions AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_interactions,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as unique_sessions
FROM voice_interactions
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Insert sample data for testing (optional)
INSERT INTO user_preferences (user_id, voice_provider, language, voice_type) 
VALUES 
    ('test_user_1', 'twilio', 'en-US', 'alice'),
    ('test_user_2', 'twilio', 'en-US', 'alice')
ON CONFLICT (user_id) DO NOTHING;

-- Grant necessary permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO authenticated; 