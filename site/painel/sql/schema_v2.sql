-- ═══════════════════════════════════════════
-- Assessoria Acadêmica — Schema V2
-- Novas tabelas: modulos, disciplinas
-- Colunas extras em atividades
-- Execute APÓS o schema.sql original
-- ═══════════════════════════════════════════

-- Tabela de módulos (períodos acadêmicos)
CREATE TABLE IF NOT EXISTS modulos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo TEXT UNIQUE NOT NULL,
  nome TEXT NOT NULL,
  situacao TEXT NOT NULL DEFAULT 'aberto' CHECK (situacao IN ('aberto', 'fechado')),
  dt_inicio DATE,
  dt_fim DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de disciplinas (vinculadas a alunos)
CREATE TABLE IF NOT EXISTS disciplinas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aluno_id UUID NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
  modulo_id UUID REFERENCES modulos(id) ON DELETE SET NULL,
  nome TEXT NOT NULL,
  shortname TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'matriculada' CHECK (status IN ('matriculada', 'concluida', 'trancada')),
  dt_inicio DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Novas colunas em atividades (rodar ALTER TABLE)
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS disciplina_id UUID REFERENCES disciplinas(id) ON DELETE SET NULL;
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS modulo_id UUID REFERENCES modulos(id) ON DELETE SET NULL;
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS estilo TEXT DEFAULT 'questionario' CHECK (estilo IN ('questionario', 'dissertativa'));
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS enunciado TEXT DEFAULT '';
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS alternativas JSONB DEFAULT '{}';
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS gabarito TEXT DEFAULT '';
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS nota DECIMAL(5,2) DEFAULT NULL;
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS dt_entrega DATE DEFAULT NULL;
ALTER TABLE atividades ADD COLUMN IF NOT EXISTS prioridade TEXT DEFAULT 'normal' CHECK (prioridade IN ('baixa', 'normal', 'alta', 'urgente'));

-- Novas colunas em alunos
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS email TEXT DEFAULT '';
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS cpf TEXT DEFAULT '';
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS situacao TEXT DEFAULT 'cursando' CHECK (situacao IN ('cursando', 'formado', 'trancado', 'cancelado'));
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS mensalista_valor DECIMAL(10,2) DEFAULT NULL;
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS mensalista_vencimento INTEGER DEFAULT NULL;

-- Tabela de pagamentos (controle financeiro)
CREATE TABLE IF NOT EXISTS pagamentos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aluno_id UUID NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
  valor DECIMAL(10,2) NOT NULL,
  tipo TEXT NOT NULL DEFAULT 'avulso' CHECK (tipo IN ('avulso', 'mensalidade', 'pacote')),
  status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'pago', 'atrasado', 'cancelado')),
  referencia TEXT DEFAULT '',
  dt_vencimento DATE,
  dt_pagamento DATE,
  observacoes TEXT DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_disciplinas_aluno ON disciplinas(aluno_id);
CREATE INDEX IF NOT EXISTS idx_disciplinas_modulo ON disciplinas(modulo_id);
CREATE INDEX IF NOT EXISTS idx_atividades_disciplina ON atividades(disciplina_id);
CREATE INDEX IF NOT EXISTS idx_atividades_modulo ON atividades(modulo_id);
CREATE INDEX IF NOT EXISTS idx_atividades_prioridade ON atividades(prioridade);
CREATE INDEX IF NOT EXISTS idx_pagamentos_aluno ON pagamentos(aluno_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_status ON pagamentos(status);

-- RLS para novas tabelas
ALTER TABLE modulos ENABLE ROW LEVEL SECURITY;
ALTER TABLE disciplinas ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagamentos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Auth pode ver modulos" ON modulos FOR SELECT TO authenticated USING (true);
CREATE POLICY "Auth pode inserir modulos" ON modulos FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Auth pode editar modulos" ON modulos FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Auth pode deletar modulos" ON modulos FOR DELETE TO authenticated USING (true);

CREATE POLICY "Auth pode ver disciplinas" ON disciplinas FOR SELECT TO authenticated USING (true);
CREATE POLICY "Auth pode inserir disciplinas" ON disciplinas FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Auth pode editar disciplinas" ON disciplinas FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Auth pode deletar disciplinas" ON disciplinas FOR DELETE TO authenticated USING (true);

CREATE POLICY "Auth pode ver pagamentos" ON pagamentos FOR SELECT TO authenticated USING (true);
CREATE POLICY "Auth pode inserir pagamentos" ON pagamentos FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Auth pode editar pagamentos" ON pagamentos FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Auth pode deletar pagamentos" ON pagamentos FOR DELETE TO authenticated USING (true);

-- Trigger updated_at para pagamentos
CREATE TRIGGER pagamentos_updated_at
  BEFORE UPDATE ON pagamentos
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
