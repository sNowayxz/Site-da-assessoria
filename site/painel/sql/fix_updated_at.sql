-- Adicionar updated_at à solicitacoes (para notificações de status)
ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Trigger para auto-atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS solicitacoes_set_updated_at ON solicitacoes;
CREATE TRIGGER solicitacoes_set_updated_at
  BEFORE UPDATE ON solicitacoes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Preencher updated_at nos registros existentes
UPDATE solicitacoes SET updated_at = created_at WHERE updated_at IS NULL;
