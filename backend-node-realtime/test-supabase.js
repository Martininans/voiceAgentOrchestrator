require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

console.log('SUPABASE_URL:', process.env.SUPABASE_URL);
console.log('SUPABASE_ANON_KEY:', process.env.SUPABASE_ANON_KEY ? 'present' : 'missing');

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

(async () => {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000); // 10 seconds

    const { data, error } = await supabase
      .from('voice_interactions')
      .select('*')
      .limit(1)
      .abortSignal(controller.signal);

    clearTimeout(timeout);
    console.log('DATA:', data);
    console.log('ERROR:', error);
  } catch (err) {
    console.error('Caught error:', err);
  }
})();