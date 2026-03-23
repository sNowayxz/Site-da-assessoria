-- ═══════════════════════════════════════════
-- Schema v7 — Google Calendar Integration
-- ═══════════════════════════════════════════

-- 1. Tokens OAuth por usuário
CREATE TABLE IF NOT EXISTS google_calendar_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  refresh_token TEXT NOT NULL,
  access_token TEXT,
  token_expires_at TIMESTAMPTZ,
  calendar_id TEXT DEFAULT 'primary',
  google_email TEXT,
  connected_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE google_calendar_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuário acessa próprios tokens"
  ON google_calendar_tokens FOR ALL
  USING (auth.uid() = user_id);

-- 2. Mapeamento evento painel <-> Google Calendar
CREATE TABLE IF NOT EXISTS google_calendar_sync (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  evento_id UUID REFERENCES eventos_agenda(id) ON DELETE CASCADE,
  google_event_id TEXT NOT NULL,
  last_synced_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, evento_id)
);

CREATE INDEX IF NOT EXISTS idx_gcal_sync_user ON google_calendar_sync(user_id);
CREATE INDEX IF NOT EXISTS idx_gcal_sync_evento ON google_calendar_sync(evento_id);

ALTER TABLE google_calendar_sync ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuário acessa próprio sync"
  ON google_calendar_sync FOR ALL
  USING (auth.uid() = user_id);

-- 3. Eventos importados do Google (read-only no painel)
CREATE TABLE IF NOT EXISTS google_calendar_imported (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  google_event_id TEXT NOT NULL,
  titulo TEXT NOT NULL,
  data DATE NOT NULL,
  hora TIME,
  data_fim DATE,
  hora_fim TIME,
  descricao TEXT DEFAULT '',
  cor TEXT DEFAULT '#ea4335',
  last_synced_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, google_event_id)
);

CREATE INDEX IF NOT EXISTS idx_gcal_imported_user_data ON google_calendar_imported(user_id, data);

ALTER TABLE google_calendar_imported ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuário acessa próprios importados"
  ON google_calendar_imported FOR ALL
  USING (auth.uid() = user_id);
