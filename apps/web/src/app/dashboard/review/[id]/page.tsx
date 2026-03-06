"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { fetchApi } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"
import { ArrowLeft, CheckCircle } from "lucide-react"

export default function ReviewPage() {
    const { id } = useParams()
    const router = useRouter()
    const [loading, setLoading] = useState(true)
    const [publishing, setPublishing] = useState(false)
    const [product, setProduct] = useState<any>(null)

    // States editáveis para o draft a ser publicado
    const [draft, setDraft] = useState({
        title: "",
        price: "",
        description: "",
        category: "",
        images: [] as string[]
    })

    useEffect(() => {
        async function load() {
            try {
                // Na prática buscaríamos o ListingDraft pronto em /listings?product_id={id}
                // ou o product enriquecido. Por simplicidade do MVP, chamaremos do products get
                const res = await fetchApi(`/products/${id}`)

                // Mock se listing real ainda não existir:
                const attrs = res.attributes || {}
                setProduct(res)
                setDraft({
                    title: attrs.name || "Produto Sem Título Gerado",
                    price: attrs.price || "199.90",
                    description: attrs.description || "Descrição em desenvolvimento pelo AI...",
                    category: attrs.category || "MLB_BASE",
                    images: attrs.images || ["https://via.placeholder.com/400?text=Sem+Foto"]
                })
            } catch (e: any) {
                toast.error("Erro ao carregar produto: " + e.message)
            } finally {
                setLoading(false)
            }
        }
        if (id) load()
    }, [id])

    async function handlePublish() {
        setPublishing(true)
        try {
            // Stub endpoint. Na API, `/listings/{listing_id}/publish`. Assumimos aqui que mockamos
            const res = await fetchApi(`/listings/publish_mocked_for_mvp`, {
                method: "POST",
                body: JSON.stringify({ product_id: id, ...draft })
            })
            toast.success("Publicado no Mercado Livre com sucesso!")
            router.push("/dashboard")
        } catch (e: any) {
            toast.error("Falha ao publicar: " + e.message)
        } finally {
            setPublishing(false)
        }
    }

    if (loading) return <div className="p-8">Carregando dados para revisão...</div>
    if (!product) return <div className="p-8">Produto não encontrado.</div>

    return (
        <div className="flex flex-col gap-4 h-full">
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard")}>
                    <ArrowLeft className="h-5 w-5" />
                </Button>
                <h1 className="text-2xl font-bold tracking-tight">Revisão de Anúncio</h1>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-8">
                {/* LADO ESQUERDO: Dados e Edição (Form) */}
                <div className="flex flex-col gap-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Painel do Produto</CardTitle>
                            <CardDescription>Edite os atributos finais gerados pela IA antes de publicar.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Tabs defaultValue="geral">
                                <TabsList className="grid w-full grid-cols-3">
                                    <TabsTrigger value="geral">Geral</TabsTrigger>
                                    <TabsTrigger value="desc">Descrição</TabsTrigger>
                                    <TabsTrigger value="attrs">Atributos ML</TabsTrigger>
                                </TabsList>
                                <TabsContent value="geral" className="space-y-4 pt-4">
                                    <div className="space-y-2">
                                        <Label>Título do Anúncio</Label>
                                        <Input
                                            value={draft.title}
                                            onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Preço (R$)</Label>
                                        <Input
                                            type="number"
                                            step="0.01"
                                            value={draft.price}
                                            onChange={(e) => setDraft({ ...draft, price: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Score de Confiança Base</Label>
                                        <div className="text-sm text-muted-foreground">
                                            {(product.confidence * 100).toFixed(0)}% (GS1/Normalizer)
                                        </div>
                                    </div>
                                </TabsContent>
                                <TabsContent value="desc" className="space-y-4 pt-4">
                                    <div className="space-y-2">
                                        <Label>Descrição Formatada</Label>
                                        <Textarea
                                            className="min-h-[250px]"
                                            value={draft.description}
                                            onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                                        />
                                    </div>
                                </TabsContent>
                                <TabsContent value="attrs" className="space-y-4 pt-4">
                                    <div className="text-sm text-muted-foreground">
                                        Ficha técnica preenchida via template...
                                    </div>
                                </TabsContent>
                            </Tabs>
                        </CardContent>
                    </Card>
                </div>

                {/* LADO DIREITO: Visão do ML (Preview Hero) */}
                <div className="flex flex-col gap-4">
                    <Card className="bg-[#f5f5f5] border-yellow-400 border-2 overflow-hidden relative">
                        <div className="bg-[#ffe600] text-black h-12 flex items-center px-4 font-bold border-b border-yellow-400">
                            mercadolivre simulador
                        </div>
                        <CardContent className="p-6 bg-white m-4 rounded-md shadow-sm">
                            <div className="text-xs text-blue-600 mb-2">Voltar à lista</div>
                            <div className="flex flex-col md:flex-row gap-6">
                                {/* Fake Photos Galley */}
                                <div className="flex flex-col gap-2 w-full md:w-1/2">
                                    <div className="aspect-square bg-slate-100 rounded-md border flex items-center justify-center p-2">
                                        <img src={draft.images[0]} alt="Produto" className="max-h-full object-contain mix-blend-multiply" />
                                    </div>
                                </div>
                                {/* Fake Purchase Box */}
                                <div className="flex flex-col gap-3 w-full md:w-1/2">
                                    <div className="text-sm text-muted-foreground">Novo | 5 vendidos</div>
                                    <h1 className="text-xl font-semibold text-neutral-900 leading-tight">
                                        {draft.title || "---"}
                                    </h1>
                                    <div className="text-3xl font-light text-neutral-900 mt-2">
                                        R$ {draft.price || "0,00"}
                                    </div>
                                    <div className="text-green-600 text-sm font-medium">
                                        Chegará grátis amanhã
                                    </div>

                                    <div className="mt-4 flex flex-col gap-2">
                                        <Button className="w-full bg-[#3483fa] hover:bg-[#2968c8] text-white">Comprar agora</Button>
                                        <Button variant="outline" className="w-full text-[#3483fa] border-none bg-blue-50 hover:bg-blue-100 shadow-none">Adicionar ao carrinho</Button>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Call to action de aprovação humana */}
                    <Card className="mt-4 border-green-200 bg-green-50/30">
                        <CardContent className="p-4 flex items-center justify-between">
                            <div>
                                <h3 className="font-semibold text-green-900">Tudo certo?</h3>
                                <p className="text-sm text-green-700">Ao aprovar, o worker listing.publish fará a injeção oficial da API.</p>
                            </div>
                            <Button
                                onClick={handlePublish}
                                disabled={publishing}
                                className="bg-green-600 hover:bg-green-700 gap-2 px-8"
                                size="lg"
                            >
                                <CheckCircle className="w-5 h-5" />
                                {publishing ? "Publicando..." : "Aprovar & Publicar"}
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
