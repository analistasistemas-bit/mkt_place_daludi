import test from "node:test"
import assert from "node:assert/strict"

import { getPaginatedItems } from "../src/lib/paginated-response.js"

test("getPaginatedItems retorna items de uma resposta paginada", () => {
  const response = {
    items: [
      { id: "p1", gtin: "7891000100103" },
    ],
    total: 1,
    page: 1,
    per_page: 20,
    pages: 1,
  }

  assert.deepEqual(getPaginatedItems(response), response.items)
})

test("getPaginatedItems retorna array vazio quando items nao existe", () => {
  assert.deepEqual(getPaginatedItems({ data: [] }), [])
  assert.deepEqual(getPaginatedItems(null), [])
})
