export function getProductDisplayTitle(product) {
  const title = product?.title

  // Se tem título real (não é placeholder ou UUID ou null)
  if (title && title.length > 0) {
    // Verificar se o título é apenas um UUID
    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    if (uuidPattern.test(title)) {
      return product?.brand
        ? `${product.brand} - ${product.gtin || "sem GTIN"}`
        : `Produto ${product.gtin || product.id?.substring(0, 8)}`
    }
    return title
  }

  // Fallbacks inteligentes
  if (product?.brand) {
    return `${product.brand} - ${product.gtin || "sem GTIN"}`
  }

  if (product?.gtin) {
    return `GTIN ${product.gtin} (aguardando identificação)`
  }

  return product?.id?.substring(0, 8) || "Produto Sem Título"
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
