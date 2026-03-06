import test from "node:test"
import assert from "node:assert/strict"

import { getProductDisplayTitle, getProductReviewDraft } from "../src/lib/product-display.js"

test("getProductDisplayTitle prioriza product.title resolvido", () => {
  const product = {
    id: "prod-1",
    title: "Café Torrado e Moído Tradicional 500g",
    attributes: { name: "Produto Sem Título Gerado" },
  }

  assert.equal(getProductDisplayTitle(product), "Café Torrado e Moído Tradicional 500g")
})

test("getProductReviewDraft usa campos do produto antes dos mocks legados", () => {
  const product = {
    id: "prod-1",
    title: "Café Torrado e Moído Tradicional 500g",
    description: "Café tradicional embalado a vácuo.",
    category: "cafe",
    images: ["https://example.com/cafe.jpg"],
    attributes: { name: "Produto Sem Título Gerado" },
  }

  assert.deepEqual(getProductReviewDraft(product), {
    title: "Café Torrado e Moído Tradicional 500g",
    price: "199.90",
    description: "Café tradicional embalado a vácuo.",
    category: "cafe",
    images: ["https://example.com/cafe.jpg"],
  })
})
