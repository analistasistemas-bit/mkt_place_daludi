"use client"

import { Button } from "@/components/ui/button"

export default function DashboardError({
    error,
    reset,
}: {
    error: Error & { digest?: string }
    reset: () => void
}) {
    return (
        <div className="flex flex-col items-center justify-center gap-4 py-16">
            <div className="text-center space-y-2">
                <h2 className="text-xl font-semibold text-red-600">Algo deu errado</h2>
                <p className="text-muted-foreground text-sm max-w-md">
                    Ocorreu um erro ao carregar esta página. Isso pode acontecer quando o servidor backend está se inicializando.
                </p>
                {error.message && (
                    <p className="text-xs text-muted-foreground font-mono bg-muted p-2 rounded">
                        {error.message}
                    </p>
                )}
            </div>
            <Button onClick={reset} variant="outline">
                Tentar novamente
            </Button>
        </div>
    )
}
