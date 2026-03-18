/* Upload Avatars em Lote — Vercel API */
const fs = require('fs');
const path = require('path');

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  const SB_URL = process.env.SUPABASE_URL || 'https://lztfoprapoyicldunhzw.supabase.co';
  const SB_KEY = process.env.SUPABASE_SERVICE_KEY;
  if (!SB_KEY) return res.status(500).json({ error: 'SUPABASE_SERVICE_KEY não configurada' });

  const { email, image_base64, content_type } = req.body || {};
  if (!email || !image_base64) {
    return res.status(400).json({ error: 'email + image_base64 required' });
  }

  try {
    // 1. Find assessor by email (via auth admin API)
    const authResp = await fetch(`${SB_URL}/auth/v1/admin/users`, {
      headers: { 'apikey': SB_KEY, 'Authorization': `Bearer ${SB_KEY}` }
    });
    const authData = await authResp.json();
    const user = (authData.users || []).find(u => u.email === email);
    if (!user) return res.status(404).json({ error: 'User not found: ' + email });

    // 2. Upload to storage
    const ext = (content_type || 'image/jpeg').includes('png') ? 'png' : 'jpg';
    const storagePath = `avatars/${user.id}.${ext}`;
    const imageBuffer = Buffer.from(image_base64, 'base64');

    // Delete existing if any
    await fetch(`${SB_URL}/storage/v1/object/chat-files/${storagePath}`, {
      method: 'DELETE',
      headers: { 'apikey': SB_KEY, 'Authorization': `Bearer ${SB_KEY}` }
    });

    const uploadResp = await fetch(`${SB_URL}/storage/v1/object/chat-files/${storagePath}`, {
      method: 'POST',
      headers: {
        'apikey': SB_KEY,
        'Authorization': `Bearer ${SB_KEY}`,
        'Content-Type': content_type || 'image/jpeg',
        'x-upsert': 'true'
      },
      body: imageBuffer
    });

    if (!uploadResp.ok) {
      const err = await uploadResp.text();
      return res.status(500).json({ error: 'Upload failed: ' + err });
    }

    // 3. Get public URL
    const publicUrl = `${SB_URL}/storage/v1/object/public/chat-files/${storagePath}`;

    // 4. Update assessores table
    const updateResp = await fetch(`${SB_URL}/rest/v1/assessores?id=eq.${user.id}`, {
      method: 'PATCH',
      headers: {
        'apikey': SB_KEY,
        'Authorization': `Bearer ${SB_KEY}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
      },
      body: JSON.stringify({ avatar_url: publicUrl })
    });

    const updateData = await updateResp.json();

    return res.status(200).json({
      ok: true,
      email,
      user_id: user.id,
      avatar_url: publicUrl,
      db_update: updateResp.ok
    });
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
};
