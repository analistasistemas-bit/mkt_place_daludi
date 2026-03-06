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
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { getPaginatedItems } from "@/lib/paginated-response"

export default async function ProductsPage() {
    let products = []

    try {
        const res = await fetchApi("/products")
        products = getPaginatedItems(res)
    } catch (error) {
        console.error(error)
    }

    return (
        <div className="flex flex-col gap-4">
            <h1 className="text-2xl font-bold tracking-tight">Produtos</h1>
            <div className="border rounded-md">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>GTIN</TableHead>
                            <TableHead>Nome base</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Confiança</TableHead>
                            <TableHead className="text-right">Ação</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {products.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="text-center py-6 text-muted-foreground">
                                    Nenhum produto cadastrado. Tente importar na aba de Importação.
                                </TableCell>
                            </TableRow>
                        ) : (
                            products.map((p: any) => (
                                <TableRow key={p.id}>
                                    <TableCell className="font-medium">{p.gtin}</TableCell>
                                    <TableCell>{p.attributes?.name || p.id}</TableCell>
                                    <TableCell>
                                        <Badge variant={p.status === "resolved" ? "default" : "secondary"}>
                                            {p.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        {p.confidence ? `${(p.confidence * 100).toFixed(0)}%` : "N/A"}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Link href={`/dashboard/review/${p.id}`}>
                                            <Button variant="outline" size="sm">
                                                Revisar
                                            </Button>
                                        </Link>
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
