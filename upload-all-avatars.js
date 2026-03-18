/**
 * Upload All Avatars — Script local
 *
 * USO:
 * 1. Salve as fotos na pasta "avatars/" com os nomes abaixo
 * 2. Rode: node upload-all-avatars.js
 *
 * A API precisa estar no ar: https://site-da-assessoria.vercel.app/api/upload-avatars
 */

const fs = require('fs');
const path = require('path');

const API_URL = 'https://site-da-assessoria.vercel.app/api/upload-avatars';

const MAPPING = [
  { file: 'einstein',   email: 'einstein@assessoriaextensoes.com' },
  { file: 'dl',         email: 'dl@assessoriaextensoes.com' },
  { file: 'exellence',  email: 'exellence@assessoriaextensoes.com' },
  { file: 'prime',      email: 'prime@assessoriaextensoes.com' },
  { file: 'azul',       email: 'azul@assessoriaextensoes.com' },
  { file: 'barbara',    email: 'barbara@assessoriaextensoes.com' },
  { file: 'ary',        email: 'ary@assessoriaextensoes.com' },
  { file: 'brayan',     email: 'brayan@assessoriaextensoes.com' },
  { file: 'renderizzi', email: 'renderizzi@assessoriaextensoes.com' },
  // { file: 'jed',      email: 'jed@assessoriaextensoes.com' },  // sem foto
];

const AVATARS_DIR = path.join(__dirname, 'avatars');

async function uploadAll() {
  for (const item of MAPPING) {
    // Try multiple extensions
    let filePath = null;
    let contentType = 'image/jpeg';
    for (const ext of ['jpg', 'jpeg', 'png', 'webp']) {
      const p = path.join(AVATARS_DIR, `${item.file}.${ext}`);
      if (fs.existsSync(p)) {
        filePath = p;
        contentType = ext === 'png' ? 'image/png' : ext === 'webp' ? 'image/webp' : 'image/jpeg';
        break;
      }
    }

    if (!filePath) {
      console.log(`⏭️  ${item.file} — arquivo não encontrado, pulando`);
      continue;
    }

    console.log(`📤 Uploading ${item.file} → ${item.email}...`);

    try {
      const imageBuffer = fs.readFileSync(filePath);
      const base64 = imageBuffer.toString('base64');

      const resp = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: item.email,
          image_base64: base64,
          content_type: contentType
        })
      });

      const result = await resp.json();
      if (result.ok) {
        console.log(`✅ ${item.file} — ${result.avatar_url}`);
      } else {
        console.log(`❌ ${item.file} — ${result.error}`);
      }
    } catch (e) {
      console.log(`❌ ${item.file} — ${e.message}`);
    }
  }

  console.log('\n🏁 Done!');
}

uploadAll();
