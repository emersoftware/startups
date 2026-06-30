// Slug de una startup para su URL/deep-link: minúsculas, sin acentos, no-alfanum -> guion.
// "Watermelon Tools" -> "watermelon-tools", "Blar" -> "blar", "Con Yappa" -> "con-yappa".
export const slugify = (x: string): string =>
  (x || "")
    .toLowerCase()
    .normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
