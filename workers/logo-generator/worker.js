/**
 * BizComp AI — Logo Generator Worker
 *
 * Model: @cf/black-forest-labs/flux-1-schnell
 * Endpoint: POST /
 * Auth: Bearer token via CLOUDFLARE_AI_KEY env
 * Request: { "prompt": "deskripsi logo dalam Bahasa Indonesia" }
 * Response: { "image": "base64encodedstring..." }
 */

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    const auth = request.headers.get('Authorization')
    if (!auth || !auth.startsWith('Bearer ') || auth.slice(7) !== env.CLOUDFLARE_AI_KEY) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    let prompt
    try {
      const body = await request.json()
      prompt = body.prompt
    } catch {
      return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    if (!prompt || typeof prompt !== 'string') {
      return new Response(JSON.stringify({ error: 'Missing or invalid prompt' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    try {
      const result = await env.AI.run('@cf/black-forest-labs/flux-1-schnell', { prompt })

      if (!result || !result.image) {
        return new Response(JSON.stringify({ error: 'Model returned no image' }), {
          status: 502,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      return new Response(JSON.stringify({ image: result.image }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message || 'AI run failed' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      })
    }
  },
}
