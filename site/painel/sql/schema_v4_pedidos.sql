-- ═══════════════════════════════════════════
-- Schema v4 — Pedidos de Extensão + Mercado Pago
-- Rodar no SQL Editor do Supabase
-- ═══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pedidos_extensao (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  nome_cliente TEXT NOT NULL,
  email TEXT NOT NULL,
  telefone TEXT,
  ra TEXT,
  curso TEXT NOT NULL,
  carga_horaria INTEGER NOT NULL,
  tema TEXT NOT NULL,
  prazo DATE,
  observacoes TEXT,
  valor DECIMAL(10,2),
  status TEXT DEFAULT 'aguardando_pagamento'
    CHECK (status IN ('aguardando_pagamento','pago','em_andamento','concluido','cancelado')),
  payment_id TEXT,
  payment_status TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos_extensao(status);
CREATE INDEX IF NOT EXISTS idx_pedidos_email ON pedidos_extensao(email);
CREATE INDEX IF NOT EXISTS idx_pedidos_payment ON pedidos_extensao(payment_id);

-- RLS
ALTER TABLE pedidos_extensao ENABLE ROW LEVEL SECURITY;

-- Anon: pode inserir pedidos (clientes não logados)
CREATE POLICY "Anon can insert pedidos"
  ON pedidos_extensao FOR INSERT
  TO anon
  WITH CHECK (true);

-- Anon: pode consultar pedidos (para página de status)
CREATE POLICY "Anon can read pedidos"
  ON pedidos_extensao FOR SELECT
  TO anon
  USING (true);

-- Authenticated: acesso total (admin)
CREATE POLICY "Auth full access pedidos SELECT"
  ON pedidos_extensao FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Auth full access pedidos INSERT"
  ON pedidos_extensao FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Auth full access pedidos UPDATE"
  ON pedidos_extensao FOR UPDATE
  TO authenticated
  USING (true);

CREATE POLICY "Auth full access pedidos DELETE"
  ON pedidos_extensao FOR DELETE
  TO authenticated
  USING (true);
