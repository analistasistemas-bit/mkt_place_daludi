import { Sidebar } from "@/components/layout/sidebar"
import { Navbar } from "@/components/layout/navbar"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <div className="grid min-h-screen w-full md:grid-cols-[256px_1fr]">
            <Sidebar />
            <div className="flex flex-col h-screen overflow-hidden">
                <Navbar />
                <main className="flex-1 overflow-auto p-4 lg:p-6 bg-background">
                    {children}
                </main>
            </div>
        </div>
    )
}
