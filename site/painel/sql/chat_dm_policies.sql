-- RLS para mensagens: permitir DMs privados
-- Canal DM segue formato: dm-{id1}-{id2}
-- Cada usuário só pode ler/escrever em canais que contenham seu ID

-- Habilitar RLS
ALTER TABLE mensagens ENABLE ROW LEVEL SECURITY;

-- Limpar policies antigas
DROP POLICY IF EXISTS "Users can read messages" ON mensagens;
DROP POLICY IF EXISTS "Users can insert messages" ON mensagens;
DROP POLICY IF EXISTS "Users can delete own messages" ON mensagens;
DROP POLICY IF EXISTS "chat_select" ON mensagens;
DROP POLICY IF EXISTS "chat_insert" ON mensagens;
DROP POLICY IF EXISTS "chat_delete" ON mensagens;

-- SELECT: usuário pode ver mensagens de canais públicos (geral, urgente)
-- OU de DMs onde ele é participante (canal contém seu ID)
CREATE POLICY "chat_select" ON mensagens FOR SELECT TO authenticated
USING (
  channel IN ('geral', 'urgente')
  OR channel LIKE '%' || auth.uid()::text || '%'
  OR get_user_role() IN ('admin', 'dono')
);

-- INSERT: usuário pode enviar em canais públicos
-- OU em DMs onde ele é participante
CREATE POLICY "chat_insert" ON mensagens FOR INSERT TO authenticated
WITH CHECK (
  sender_id = auth.uid()
  AND (
    channel IN ('geral', 'urgente')
    OR channel LIKE '%' || auth.uid()::text || '%'
    OR get_user_role() IN ('admin', 'dono')
  )
);

-- DELETE: só pode apagar as próprias mensagens
CREATE POLICY "chat_delete" ON mensagens FOR DELETE TO authenticated
USING (
  sender_id = auth.uid()
  OR get_user_role() IN ('admin', 'dono')
);
