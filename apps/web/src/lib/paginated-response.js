export function getPaginatedItems(response) {
  if (!response || !Array.isArray(response.items)) {
    return []
  }

  return response.items
}
