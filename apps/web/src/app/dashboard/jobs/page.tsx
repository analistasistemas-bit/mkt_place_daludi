import { fetchApi } from "@/lib/api-client.server"

export const dynamic = 'force-dynamic'

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

function getStatusBadge(status: string) {
    switch (status) {
        case "completed":
            return <Badge variant="default" className="bg-green-600 hover:bg-green-700">Concluído</Badge>
        case "failed":
            return <Badge variant="destructive">Falhou</Badge>
        case "processing":
            return <Badge variant="default" className="bg-blue-600 hover:bg-blue-700">Processando</Badge>
        default:
            return <Badge variant="outline" className="text-muted-foreground">Pendente</Badge>
    }
}

export default async function JobsPage() {
    let jobs = []

    try {
        // API Route to fetch jobs / job events
        const res = await fetchApi("/jobs")
        jobs = res.items || []
    } catch (error) {
        console.error(error)
    }

    return (
        <div className="flex flex-col gap-4">
            <h1 className="text-2xl font-bold tracking-tight">Monitor de Jobs (Worker)</h1>
            <div className="border rounded-md">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Tarefa</TableHead>
                            <TableHead>Mensagem</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Data</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {jobs.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-6 text-muted-foreground">
                                    Nenhum job registrado recentemente.
                                </TableCell>
                            </TableRow>
                        ) : (
                            jobs.map((j: any) => (
                                <TableRow key={j.id}>
                                    <TableCell className="font-mono text-sm max-w-xs truncate" title={j.job_id}>
                                        {j.job_id}
                                    </TableCell>
                                    <TableCell>{j.message}</TableCell>
                                    <TableCell>
                                        {getStatusBadge(j.status)}
                                    </TableCell>
                                    <TableCell className="text-right text-muted-foreground">
                                        {new Date(j.created_at).toLocaleString('pt-BR')}
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
