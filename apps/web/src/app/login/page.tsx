import { login } from "./actions"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"

export default async function LoginPage({ searchParams }: { searchParams: { error?: string } }) {
    const errorMsg = searchParams?.error ? "Email ou senha inválidos." : null

    return (
        <div className="flex h-screen w-full items-center justify-center p-4">
            <Card className="w-full max-w-sm">
                <CardHeader>
                    <CardTitle className="text-2xl">Daludi Marketplace</CardTitle>
                    <CardDescription>
                        Entre com suas credenciais para gerenciar seus anúncios.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form className="grid gap-4" action={login}>
                        {errorMsg && (
                            <div className="text-sm font-medium text-destructive mb-2">
                                {errorMsg}
                            </div>
                        )}
                        <div className="grid gap-2">
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                name="email"
                                type="email"
                                placeholder="m@exemplo.com"
                                required
                            />
                        </div>
                        <div className="grid gap-2">
                            <div className="flex items-center">
                                <Label htmlFor="password">Senha</Label>
                            </div>
                            <Input id="password" name="password" type="password" required />
                        </div>
                        <Button className="w-full" type="submit">
                            Entrar
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    )
}
