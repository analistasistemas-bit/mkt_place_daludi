"use client"

import { Button } from "@/components/ui/button"
import { logout } from "@/app/login/actions"
import { Menu } from "lucide-react"

export function Navbar() {
    return (
        <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6 justify-between w-full">
            <div className="flex items-center md:hidden">
                <Button variant="outline" size="icon" className="shrink-0">
                    <Menu className="h-5 w-5" />
                    <span className="sr-only">Toggle navigation menu</span>
                </Button>
            </div>
            <div className="flex-1">
                {/* Adicionar breadcrumbs se necessário, ou titulo */}
            </div>
            <div>
                <form action={logout}>
                    <Button variant="ghost" type="submit">Sair</Button>
                </form>
            </div>
        </header>
    )
}
