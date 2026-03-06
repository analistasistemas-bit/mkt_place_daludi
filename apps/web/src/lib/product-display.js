export function getProductDisplayTitle(product) {
  return (
    product?.title ||
    product?.attributes?.name ||
    product?.id ||
    "Produto Sem Título Gerado"
  )
}

export function getProductReviewDraft(product) {
  const attrs = product?.attributes || {}

  return {
    title: getProductDisplayTitle(product),
    price: attrs.price || "199.90",
    description: product?.description || attrs.description || "Descrição em desenvolvimento pelo AI...",
    category: product?.category || attrs.category || "MLB_BASE",
    images: product?.images || attrs.images || ["https://via.placeholder.com/400?text=Sem+Foto"],
  }
}
