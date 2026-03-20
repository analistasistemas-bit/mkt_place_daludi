"use client"

export const dynamic = 'force-dynamic'

import { useEffect, useState } from "react"
import { fetchApi } from "@/lib/api-client.client"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

function getStatusBadge(status: string) {
    switch (status) {
        case "completed":
            return <Badge variant="default" className="bg-green-600 hover:bg-green-700">Concluído</Badge>
        case "failed":
            return <Badge variant="destructive">Falhou</Badge>
        case "processing":
            return <Badge variant="default" className="bg-blue-600 hover:bg-blue-700">Processando</Badge>
        case "queued":
            return <Badge variant="default" className="bg-yellow-600 hover:bg-yellow-700">Na Fila</Badge>
        default:
            return <Badge variant="outline" className="text-muted-foreground">Pendente</Badge>
    }
}

function formatDate(dateStr: string) {
    try {
        return new Date(dateStr).toLocaleString('pt-BR', { timeZone: 'America/Recife' })
    } catch {
        return dateStr
    }
}

export default function JobsPage() {
    const [jobs, setJobs] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    async function loadJobs() {
        setLoading(true)
        setError(null)
        try {
            const res = await fetchApi("/jobs")
            setJobs(res.items || [])
        } catch (err: any) {
            console.error("Erro ao carregar jobs:", err)
            setError(err.message || "Erro ao carregar jobs")
            setJobs([])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadJobs()
        // Auto-refresh a cada 10 segundos
        const interval = setInterval(loadJobs, 10000)
        return () => clearInterval(interval)
    }, [])

    return (
        <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold tracking-tight">Monitor de Jobs (Worker)</h1>
                <Button variant="outline" size="sm" onClick={loadJobs} disabled={loading} className="flex gap-2">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    {loading ? "Carregando..." : "Atualizar"}
                </Button>
            </div>

            {error && (
                <div className="border border-red-300 bg-red-50 text-red-700 rounded-md p-3 text-sm">
                    ⚠️ Não foi possível carregar os jobs: {error}
                </div>
            )}

            <div className="border rounded-md">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Tipo</TableHead>
                            <TableHead>Mensagem</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Data</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {!loading && jobs.length === 0 && !error ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-6 text-muted-foreground">
                                    Nenhum job registrado recentemente.
                                </TableCell>
                            </TableRow>
                        ) : (
                            jobs.map((j: any) => (
                                <TableRow key={j.id}>
                                    <TableCell className="font-mono text-xs max-w-[120px] truncate" title={j.job_type}>
                                        {j.job_type || "—"}
                                    </TableCell>
                                    <TableCell className="max-w-xs truncate text-sm" title={j.error || j.job_type}>
                                        {j.error ? <span className="text-red-600">Erro: {j.error}</span> : (j.result ? "Sucesso" : "—")}
                                    </TableCell>
                                    <TableCell>
                                        {getStatusBadge(j.status)}
                                    </TableCell>
                                    <TableCell className="text-right text-muted-foreground text-sm">
                                        {formatDate(j.created_at)}
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    )
}
