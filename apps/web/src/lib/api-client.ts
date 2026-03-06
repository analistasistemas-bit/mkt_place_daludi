import { createClient } from "@/utils/supabase/server"

// API Backend Base URL fallback
const API_BASE_URL = process.env.API_URL || "http://localhost:8000"

/**
 * Cliente seguro de API do FastAPI. 
 * Executa APENAS sob Server Components / Server Actions porque usa os cookies Next.js
 * Injeta o JWT do Supabase para que a API consiga fazer o RLS via auth_middleware.
 */
export async function fetchApi(endpoint: string, options: RequestInit = {}) {
    // Pega client do Supabase que lê cookies do Next context
    const supabase = await createClient()
    const { data: { session } } = await supabase.auth.getSession()

    const headers = new Headers(options.headers || {})

    if (session?.access_token) {
        headers.set("Authorization", `Bearer ${session.access_token}`)
    }

    // Como as rotas fastapi na config necessitam de um X-Tenant-Id (via auth middleware/ou fallback jwt)
    // Adiciona header genérico app JSON se não fornecido
    if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json")
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    })

    if (!response.ok) {
        // Tratar/lançar erros estruturados se a API rejeitar
        const errorBody = await response.text()
        console.error(`FetchAPI error [${response.status}]: ${errorBody}`)
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }

    return response.json()
}
