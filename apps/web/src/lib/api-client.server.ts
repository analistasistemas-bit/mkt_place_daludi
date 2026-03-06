import { createClient } from "@/utils/supabase/server"

// API Backend Base URL fallback
const API_BASE_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "https://mkt-place-daludi.onrender.com"

/**
 * Cliente seguro de API do FastAPI para SERVER COMPONENTS
 * Usa o cliente Supabase Server que necessita de next/headers
 */
export async function fetchApi(endpoint: string, options: RequestInit = {}) {
    const supabase = await createClient()
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
        console.error(`FetchAPI (Server) error [${response.status}]: ${errorBody}`)
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }

    return response.json()
}
