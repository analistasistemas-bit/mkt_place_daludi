import { createClient } from "@/utils/supabase/client"

// API Backend Base URL fallback
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://mkt-place-daludi.onrender.com"

/**
 * Cliente seguro de API do FastAPI para CLIENT COMPONENTS
 * Usa o cliente Supabase Browser que funciona sem next/headers
 */
export async function fetchApi(endpoint: string, options: RequestInit = {}) {
    const supabase = createClient()
    let { data: { session } } = await supabase.auth.getSession()

    // Fallback: se não houver sessão no getSession, tenta getUser (mais lento mas garante refresh)
    if (!session) {
        const { data: { user } } = await supabase.auth.getUser()
        if (user) {
            // Se o user existir mas a sessão do getSession falhou, tentamos pegar a sessão de novo
            const { data: { session: refreshedSession } } = await supabase.auth.getSession()
            session = refreshedSession
        }
    }

    const headers = new Headers(options.headers || {})

    if (session?.access_token) {
        console.log("FetchAPI (Client): Token JWT encontrado e incluído no header.")
        headers.set("Authorization", `Bearer ${session.access_token}`)
    } else {
        console.warn("FetchAPI (Client): Nenhuma sessão ativa encontrada. Request será enviado sem token.")
    }

    if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json")
    }

    console.log(`FetchAPI (Client) calling: ${API_BASE_URL}${endpoint}`)

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
        })

        if (!response.ok) {
            const errorBody = await response.text()
            console.error(`FetchAPI (Client) error [${response.status}]: ${errorBody}`)
            throw new Error(`API Error: ${response.status} ${response.statusText}`)
        }

        return response.json()
    } catch (err: any) {
        console.error(`FetchAPI (Client) fatal error: ${err.message}`)
        throw err
    }
}
