/* ═══════════════════════════════════════════
   Supabase Config
   SUBSTITUA pelos dados do seu projeto Supabase
   ═══════════════════════════════════════════ */

const SUPABASE_URL = 'https://lztfoprapoyicldunhzw.supabase.co';
const SUPABASE_ANON_KEY = 'SUA_ANON_KEY_AQUI';

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
