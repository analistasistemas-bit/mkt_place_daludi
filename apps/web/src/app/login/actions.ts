"use server"

import { revalidatePath } from "next/cache"
import { redirect } from "next/navigation"
import { createClient } from "@/utils/supabase/server"

export async function login(formData: FormData) {
    const email = formData.get("email") as string
    console.log(`[AUTH] Tentativa de login para: ${email}`)
    const password = formData.get("password") as string

    const supabase = await createClient()

    const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
    })
    console.log(`[AUTH] Resposta do Supabase para ${email}: ${error ? "Erro: " + error.message : "Sucesso"}`)

    if (error) {
        // Para MVP, poderíamos retornar { error: error.message } e lidar na action com useFormState ou apenas redirect pra /login?error...
        redirect("/login?error=true")
    }

    revalidatePath("/", "layout")
    redirect("/dashboard")
}

export async function logout() {
    const supabase = await createClient()
    await supabase.auth.signOut()
    redirect("/login")
}
