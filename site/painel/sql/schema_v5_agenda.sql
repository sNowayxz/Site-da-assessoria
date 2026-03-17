-- ═══════════════════════════════════════════
-- Schema v5: Tabela Eventos Manuais da Agenda
-- ═══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS eventos_agenda (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo TEXT NOT NULL,
  data DATE NOT NULL,
  hora TIME DEFAULT NULL,
  tipo TEXT NOT NULL DEFAULT 'evento',
  descricao TEXT DEFAULT '',
  cor TEXT DEFAULT '#8b5cf6',
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE eventos_agenda ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own events"
  ON eventos_agenda FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own events"
  ON eventos_agenda FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own events"
  ON eventos_agenda FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own events"
  ON eventos_agenda FOR DELETE
  USING (auth.uid() = user_id);
