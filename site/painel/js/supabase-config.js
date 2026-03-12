/* ═══════════════════════════════════════════
   Supabase Config
   ═══════════════════════════════════════════ */

var SUPABASE_URL = 'https://lztfoprapoyicldunhzw.supabase.co';
var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6dGZvcHJhcG95aWNsZHVuaHp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzMzY0MzIsImV4cCI6MjA4ODkxMjQzMn0.8Qyq2bVA0oK8gji9hG2AWG-gQ3oH4nWm3QOqQ59S9IA';

// window.supabase é o SDK carregado pelo CDN
// sb é o client que usamos em todo o painel
var sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
