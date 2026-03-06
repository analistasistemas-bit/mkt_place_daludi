import { createClient } from "@/utils/supabase/client"

// API Backend Base URL fallback
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

/**
 * Cliente seguro de API do FastAPI para CLIENT COMPONENTS
 * Usa o cliente Supabase Browser que funciona sem next/headers
 */
export async function fetchApi(endpoint: string, options: RequestInit = {}) {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()

    const headers = new Headers(options.headers || {})

    if (session?.access_token) {
        headers.set("Authorization", `Bearer ${session.access_token}`)
    }

    if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json")
    }

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
}
