"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutDashboard, FileUp, ListChecks, FileSearch } from "lucide-react"
import { cn } from "@/lib/utils"

const navigation = [
    { name: "Produtos", href: "/dashboard", icon: LayoutDashboard },
    { name: "Importar GTINs", href: "/dashboard/import", icon: FileUp },
    { name: "Worker Jobs", href: "/dashboard/jobs", icon: ListChecks },
    { name: "Discovery", href: "/dashboard/discovery", icon: FileSearch },
]

export function Sidebar() {
    const pathname = usePathname()

    return (
        <div className="hidden border-r bg-muted/40 md:block w-64 h-full shrink-0">
            <div className="flex h-full max-h-screen flex-col gap-2">
                <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
                    <Link href="/" className="flex items-center gap-2 font-semibold">
                        <span>Daludi AI</span>
                    </Link>
                </div>
                <div className="flex-1">
                    <nav className="grid items-start px-2 text-sm font-medium lg:px-4 mt-4 gap-2">
                        {navigation.map((item) => {
                            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href))
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className={cn(
                                        "flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary",
                                        isActive && "bg-muted text-primary"
                                    )}
                                >
                                    <item.icon className="h-4 w-4" />
                                    {item.name}
                                </Link>
                            )
                        })}
                    </nav>
                </div>
            </div>
        </div>
    )
}
