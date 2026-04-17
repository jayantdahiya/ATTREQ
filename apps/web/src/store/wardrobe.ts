import { create } from 'zustand'
import { WardrobeItem } from '@/lib/api/wardrobe'

interface WardrobeState {
  items: WardrobeItem[]
  selectedCategory: string | null
  selectedSeason: string | null
  selectedOccasion: string | null
  setItems: (items: WardrobeItem[]) => void
  addItem: (item: WardrobeItem) => void
  updateItem: (id: string, item: Partial<WardrobeItem>) => void
  removeItem: (id: string) => void
  setFilter: (filter: { category?: string; season?: string; occasion?: string }) => void
  clearFilters: () => void
}

export const useWardrobeStore = create<WardrobeState>((set) => ({
  items: [],
  selectedCategory: null,
  selectedSeason: null,
  selectedOccasion: null,
  setItems: (items) => set({ items }),
  addItem: (item) => set((state) => ({ items: [...state.items, item] })),
  updateItem: (id, updatedItem) =>
    set((state) => ({
      items: state.items.map((item) => (item.id === id ? { ...item, ...updatedItem } : item)),
    })),
  removeItem: (id) => set((state) => ({ items: state.items.filter((item) => item.id !== id) })),
  setFilter: (filter) => set((state) => ({ ...state, ...filter })),
  clearFilters: () => set({ selectedCategory: null, selectedSeason: null, selectedOccasion: null }),
}))
