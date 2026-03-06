"use client"

export const dynamic = 'force-dynamic'

import { useState } from "react"
import { fetchApi } from "@/lib/api-client.client"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "sonner"
import { Upload } from "lucide-react"

export default function ImportPage() {
    const [loading, setLoading] = useState(false)

    async function handleImport(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        const formData = new FormData(e.currentTarget)
        const rawGtins = formData.get("gtins") as string
        if (!rawGtins) return

        setLoading(true)
        try {
            const gtins = rawGtins
                .split(/[\n,]+/)
                .map((g) => g.trim())
                .filter((g) => g.length > 0)

            if (gtins.length === 0) throw new Error("Nenhum GTIN válido")

            console.log("Iniciando importação de GTINs:", gtins)
            const res = await fetchApi("/products/import", {
                method: "POST",
                body: JSON.stringify({ gtins: gtins }),
            })

            console.log("Importação concluída com sucesso:", res)
            toast.success(`${gtins.length} GTINs enviados para processamento!`)

            const form = e.currentTarget
            form.reset()

        } catch (err: any) {
            console.error("Erro no handleImport:", err)
            toast.error(`Erro ao importar: ${err.message}`)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex flex-col gap-4">
            <h1 className="text-2xl font-bold tracking-tight">Importação de Produtos</h1>
            <Card className="max-w-xl">
                <CardHeader>
                    <CardTitle>Via GTINs</CardTitle>
                    <CardDescription>
                        Cole uma lista de códigos GTIN (um por linha ou separados por vírgula) para disparar a busca e criação pelo pipeline da Inteligência Artificial.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form id="import-form" onSubmit={handleImport} className="grid gap-4">
                        <Textarea
                            name="gtins"
                            placeholder="Ex: 7891234567890\n7890000000001"
                            className="min-h-[150px]"
                            required
                        />
                        <Button type="submit" disabled={loading} className="w-full sm:w-auto flex gap-2">
                            <Upload className="w-4 h-4" />
                            {loading ? "Importando..." : "Importar Batch"}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    )
}
