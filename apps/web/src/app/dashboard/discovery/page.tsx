"use client"

import { fetchApi } from "@/lib/api-client"
import { useEffect, useState } from "react"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export default function DiscoveryPage() {
    const [opps, setOpps] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        async function load() {
            try {
                const res = await fetchApi("/discovery/opportunities")
                setOpps(res?.data || [])
            } catch (error) {
                console.error(error)
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [])

    return (
        <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold tracking-tight">Oportunidades de Venda (Discovery)</h1>
                <Button variant="outline" size="sm" disabled>Ativar Scanner (Breve)</Button>
            </div>
            <p className="text-muted-foreground mb-4">
                Buscas passíveis de geração automatizada que você ainda não possui inventário listado.
            </p>

            <div className="border rounded-md">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>GTIN Desejado</TableHead>
                            <TableHead>Demanda ML</TableHead>
                            <TableHead>Score</TableHead>
                            <TableHead className="text-right">Ação</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {loading ? (
                            <TableRow><TableCell colSpan={4} className="text-center py-6">Carregando oportunidades...</TableCell></TableRow>
                        ) : opps.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-6 text-muted-foreground">
                                    O scanner de oportunidades ainda não injetou dados para seu tenant.
                                </TableCell>
                            </TableRow>
                        ) : (
                            opps.map((o: any) => (
                                <TableRow key={o.id}>
                                    <TableCell className="font-medium font-mono">{o.gtin}</TableCell>
                                    <TableCell>
                                        <Badge variant={o.status === "new" ? "default" : "secondary"}>
                                            {o.status === "new" ? "Alta" : "Normal"}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        {o.score}%
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button variant="secondary" size="sm">
                                            Criar Anúncio
                                        </Button>
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
